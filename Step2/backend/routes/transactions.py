from datetime import datetime, timezone, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_verified_user, verify_password, generate_otp
from config import settings
from database import get_db
from models.account import Account
from models.beneficiary import Beneficiary
from models.challenge import TransactionChallenge
from models.otp import OTP
from models.user import User
from schemas.transaction import (
    TransactionCancelRequest,
    TransactionChallengeResponse,
    TransactionInitiateRequest,
    TransactionOut,
    TransactionResendOTPRequest,
    TransactionVerifyOTPRequest,
)
from services import transaction_service
from utils import mask_account, mask_phone

router = APIRouter(prefix="/transactions", tags=["Transactions - Step 2 Baseline 2FA"])


@router.post(
    "/initiate",
    response_model=TransactionChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Step 2 - Factor 1: Password Verification & Transaction OTP Generation",
)
def initiate_transaction(
    payload: TransactionInitiateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    """
    Step 2 Baseline Authentication — Factor 1 (Password):
    1. Authenticate user's account password.
    2. Check beneficiary and sufficient balance.
    3. Generate a secure, transaction-specific OTP.
    4. Issue a pending Transaction Challenge.
    """
    # Factor 1: Password Verification
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Incorrect account password.",
        )

    # Validate Beneficiary
    beneficiary = (
        db.query(Beneficiary)
        .filter(Beneficiary.id == payload.beneficiary_id, Beneficiary.user_id == user.id)
        .first()
    )
    if not beneficiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Beneficiary not found.",
        )

    # Validate Balance
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender account not found.",
        )

    if float(payload.amount) > float(account.balance):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Current balance: ₹{account.balance:,.2f}",
        )

    # Generate OTP (Factor 2)
    otp_code = generate_otp(6)
    challenge_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    challenge = TransactionChallenge(
        id=challenge_id,
        user_id=user.id,
        beneficiary_id=beneficiary.id,
        amount=float(payload.amount),
        remark=payload.remark,
        otp_code=otp_code,
        status="PENDING_OTP",
        attempts=0,
        max_attempts=3,
        expires_at=expires_at,
    )
    db.add(challenge)

    # Also log to OTP audit table
    otp_audit = OTP(
        user_id=user.id,
        code=otp_code,
        purpose="TRANSACTION",
    )
    db.add(otp_audit)

    db.commit()

    return TransactionChallengeResponse(
        challenge_id=challenge_id,
        message=f"Password verified. Transaction OTP sent to {mask_phone(user.phone)}.",
        otp_display=otp_code,
        expires_in=settings.OTP_EXPIRE_SECONDS,
        amount=float(payload.amount),
        beneficiary_name=beneficiary.name,
        beneficiary_account=mask_account(beneficiary.account_number),
        masked_phone=mask_phone(user.phone),
    )


@router.post(
    "/verify-otp",
    response_model=TransactionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Step 2 - Factor 2: OTP Verification & Final Transaction Execution",
)
def verify_otp_and_execute(
    payload: TransactionVerifyOTPRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    """
    Step 2 Baseline Authentication — Factor 2 (OTP):
    1. Verify 6-digit transaction OTP against the active challenge.
    2. Enforce expiry and maximum attempt limits (max 3).
    3. On success, execute money transfer and record transaction with Baseline 2FA factors.
    """
    challenge = (
        db.query(TransactionChallenge)
        .filter(
            TransactionChallenge.id == payload.challenge_id,
            TransactionChallenge.user_id == user.id,
        )
        .first()
    )

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction challenge not found or invalid session.",
        )

    if challenge.status != "PENDING_OTP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot verify OTP. Challenge is already {challenge.status}.",
        )

    # Check Expiry
    now = datetime.now(timezone.utc)
    expires_at = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge.expires_at.tzinfo is None else challenge.expires_at
    if now > expires_at:
        challenge.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction OTP has expired. Please initiate a new transfer.",
        )

    # Check Attempts
    if challenge.attempts >= challenge.max_attempts:
        challenge.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP verification attempts exceeded. Transaction cancelled for security.",
        )

    challenge.attempts += 1

    if challenge.otp_code != payload.otp_code.strip():
        db.commit()
        remaining = challenge.max_attempts - challenge.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
        )

    # OTP Verified Successfully!
    challenge.status = "VERIFIED"

    # Execute transfer
    tx = transaction_service.transfer_money(
        db=db,
        user=user,
        beneficiary_id=challenge.beneficiary_id,
        amount=challenge.amount,
        remark=challenge.remark,
        auth_mode="BASELINE",
        auth_factors="PASSWORD,OTP",
    )

    db.commit()

    return TransactionOut(
        id=tx.id,
        reference_id=tx.reference_id,
        beneficiary_name=tx.beneficiary.name,
        beneficiary_account=mask_account(tx.beneficiary.account_number),
        amount=float(tx.amount),
        remark=tx.remark,
        status=tx.status,
        failure_reason=tx.failure_reason,
        auth_mode=tx.auth_mode,
        auth_factors=tx.auth_factors,
        created_at=tx.created_at,
    )


@router.post(
    "/resend-otp",
    response_model=TransactionChallengeResponse,
    summary="Step 2: Resend Transaction OTP",
)
def resend_transaction_otp(
    payload: TransactionResendOTPRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    challenge = (
        db.query(TransactionChallenge)
        .filter(
            TransactionChallenge.id == payload.challenge_id,
            TransactionChallenge.user_id == user.id,
        )
        .first()
    )

    if not challenge or challenge.status != "PENDING_OTP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active transaction challenge not found.",
        )

    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == challenge.beneficiary_id).first()

    # Generate fresh OTP
    otp_code = generate_otp(6)
    challenge.otp_code = otp_code
    challenge.attempts = 0
    now = datetime.now(timezone.utc)
    challenge.expires_at = now + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    # Log new OTP to audit table
    otp_audit = OTP(
        user_id=user.id,
        code=otp_code,
        purpose="TRANSACTION",
    )
    db.add(otp_audit)
    db.commit()

    return TransactionChallengeResponse(
        challenge_id=challenge.id,
        message=f"New Transaction OTP sent to {mask_phone(user.phone)}.",
        otp_display=otp_code,
        expires_in=settings.OTP_EXPIRE_SECONDS,
        amount=float(challenge.amount),
        beneficiary_name=beneficiary.name if beneficiary else "Beneficiary",
        beneficiary_account=mask_account(beneficiary.account_number) if beneficiary else "",
        masked_phone=mask_phone(user.phone),
    )


@router.post(
    "/cancel",
    summary="Step 2: Cancel pending transaction challenge",
)
def cancel_transaction_challenge(
    payload: TransactionCancelRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    challenge = (
        db.query(TransactionChallenge)
        .filter(
            TransactionChallenge.id == payload.challenge_id,
            TransactionChallenge.user_id == user.id,
        )
        .first()
    )

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction challenge not found.",
        )

    challenge.status = "CANCELLED"
    db.commit()
    return {"message": "Transaction challenge cancelled successfully."}


@router.post(
    "",
    status_code=status.HTTP_400_BAD_REQUEST,
    summary="Legacy direct transfer disabled in Baseline 2FA",
)
def direct_transfer_disabled():
    """
    Direct transfers are disabled in Step 2.
    Baseline Authentication requires 2FA: Password verification -> OTP verification.
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Direct transfers are disabled in Baseline Authentication. Use /transactions/initiate (Password) followed by /transactions/verify-otp.",
    )


@router.get("", response_model=list[TransactionOut])
def get_transactions(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    rows = transaction_service.list_user_transactions(db, user)
    result = []
    for tx in rows:
        result.append(
            TransactionOut(
                id=tx.id,
                reference_id=tx.reference_id,
                beneficiary_name=tx.beneficiary.name if tx.beneficiary else "Unknown",
                beneficiary_account=mask_account(tx.beneficiary.account_number) if tx.beneficiary else "",
                amount=float(tx.amount),
                remark=tx.remark,
                status=tx.status,
                failure_reason=tx.failure_reason,
                auth_mode=getattr(tx, "auth_mode", "BASELINE"),
                auth_factors=getattr(tx, "auth_factors", "PASSWORD,OTP"),
                created_at=tx.created_at,
            )
        )
    return result
