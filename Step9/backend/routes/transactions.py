from datetime import datetime, timezone, timedelta
import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import (
    get_verified_user,
    verify_password,
    verify_pin,
    generate_otp,
)
from config import settings
from database import get_db
from models.account import Account
from models.beneficiary import Beneficiary
from models.challenge import TransactionChallenge
from models.otp import OTP
from models.transaction import Transaction
from models.user import User
from schemas.transaction import (
    TransactionCancelRequest,
    TransactionChallengeResponse,
    TransactionHighRiskConfirmRequest,
    TransactionInitiateRequest,
    TransactionOut,
    TransactionResendOTPRequest,
    TransactionVerificationResponse,
    TransactionVerifyOTPRequest,
)
from services import (
    AdaptivePolicyEngine,
    PolicyConfig,
    RiskScorer,
    RiskTier,
    TransactionCryptoEngine,
    list_user_transactions,
    transfer_money,
)
from utils import mask_account, mask_phone

router = APIRouter(prefix="/transactions", tags=["Transactions - Step 9 Adaptive Proposed System"])

# Initialize singletons for Step 9
policy_config = PolicyConfig(
    tau_low_medium=settings.TAU_LOW_MEDIUM,
    tau_medium_high=settings.TAU_MEDIUM_HIGH,
)
risk_scorer = RiskScorer()
policy_engine = AdaptivePolicyEngine(config=policy_config, scorer=risk_scorer)
crypto_engine = TransactionCryptoEngine(secret_key=settings.SECRET_KEY)


@router.post(
    "/initiate",
    response_model=TransactionChallengeResponse,
    status_code=status.HTTP_200_OK,
    summary="Factor 1: Password Auth + AI Risk Assessment + Adaptive Policy Evaluation",
)
def initiate_transaction(
    payload: TransactionInitiateRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    """
    Step 9 Proposed Adaptive Pipeline — Factor 1:
    1. Authenticate user's account password.
    2. Validate recipient beneficiary and balance.
    3. Assemble transaction behavioural context.
    4. Run AI Risk Scorer (Step 5 XGBoost Model + context heuristics).
    5. Run Adaptive Security Policy Engine:
       - LOW RISK (<0.30) -> Standard 2FA
       - MEDIUM RISK (0.30-0.70) -> Anti-Social-Engineering Warning Banner + OTP
       - HIGH RISK (>=0.70) -> Escalates to Step 8 Transaction-Bound Verification
    6. Generate 6-digit OTP & pre-calculate cryptographic seals if HIGH risk.
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

    transfer_amount = float(payload.amount)
    if transfer_amount > float(account.balance):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: ₹{account.balance:,.2f}",
        )

    # Calculate Contextual Features for AI Risk Engine
    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)
    one_hour_ago_naive = now_naive - timedelta(hours=1)
    twenty_four_hours_ago_naive = now_naive - timedelta(hours=24)

    past_txs = (
        db.query(Transaction)
        .filter(
            Transaction.sender_account_id == account.id,
            Transaction.status == "COMPLETED",
        )
        .all()
    )
    if past_txs:
        user_avg_amount = sum(float(t.amount) for t in past_txs) / len(past_txs)
    else:
        user_avg_amount = 5000.0

    is_new_ben = beneficiary.created_at > twenty_four_hours_ago_naive
    velocity_last_hour = (
        db.query(Transaction)
        .filter(
            Transaction.sender_account_id == account.id,
            Transaction.created_at >= one_hour_ago_naive,
        )
        .count()
    )

    tx_context = {
        "amount": transfer_amount,
        "user_avg_amount": user_avg_amount,
        "is_new_beneficiary": is_new_ben,
        "hour_of_day": now_utc.hour,
        "velocity_last_hour": velocity_last_hour,
        "beneficiary_name": beneficiary.name,
    }
    if payload.raw_features:
        tx_context["raw_features"] = payload.raw_features

    # Run AI Risk Scorer & Policy Engine
    decision = policy_engine.evaluate_transaction(tx_context)

    # Generate Factor 2 OTP
    otp_code = generate_otp(6)
    challenge_id = str(uuid.uuid4())
    expires_at = now_utc + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    # Prepare Cryptographic Parameters if HIGH Risk
    nonce = None
    seal_timestamp = None
    cryptographic_seal = None

    if decision.risk_tier == RiskTier.HIGH:
        nonce = crypto_engine.generate_nonce()
        seal_timestamp = int(time.time())
        cryptographic_seal = crypto_engine.compute_transaction_seal(
            challenge_id=challenge_id,
            sender_account=account.account_number,
            beneficiary_account=beneficiary.account_number,
            amount=transfer_amount,
            timestamp=seal_timestamp,
            nonce=nonce,
        )

    # Persist Challenge State
    challenge = TransactionChallenge(
        id=challenge_id,
        user_id=user.id,
        beneficiary_id=beneficiary.id,
        amount=transfer_amount,
        remark=payload.remark,
        risk_score=decision.risk_score,
        risk_tier=decision.risk_tier.value,
        auth_action=decision.auth_action.value,
        warning_banner=decision.warning_banner,
        risk_reasons=json.dumps(decision.risk_reasons),
        requires_pin=decision.requires_pin,
        requires_cryptographic_seal=decision.requires_cryptographic_seal,
        otp_code=otp_code,
        otp_verified=False,
        stage="AWAITING_OTP",
        attempts=0,
        max_attempts=3,
        nonce=nonce,
        seal_timestamp=seal_timestamp,
        cryptographic_seal=cryptographic_seal,
        expires_at=expires_at,
    )
    db.add(challenge)

    # Record OTP audit
    otp_audit = OTP(
        user_id=user.id,
        code=otp_code,
        purpose="TRANSACTION",
    )
    db.add(otp_audit)
    db.commit()

    return TransactionChallengeResponse(
        challenge_id=challenge_id,
        stage="AWAITING_OTP",
        risk_score=decision.risk_score,
        risk_tier=decision.risk_tier.value,
        auth_action=decision.auth_action.value,
        warning_banner=decision.warning_banner,
        risk_reasons=decision.risk_reasons,
        requires_pin=decision.requires_pin,
        requires_cryptographic_seal=decision.requires_cryptographic_seal,
        cryptographic_seal=cryptographic_seal,
        nonce=nonce,
        seal_timestamp=seal_timestamp,
        message=f"Password verified. Risk assessed as {decision.risk_tier.value} ({decision.risk_score:.2f}). Transaction OTP sent to {mask_phone(user.phone)}.",
        otp_display=otp_code,
        expires_in=settings.OTP_EXPIRE_SECONDS,
        amount=transfer_amount,
        beneficiary_name=beneficiary.name,
        beneficiary_account=mask_account(beneficiary.account_number),
        masked_phone=mask_phone(user.phone),
    )


@router.post(
    "/verify-otp",
    response_model=TransactionVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Factor 2: OTP Verification & Dynamic Adaptive Routing",
)
def verify_transaction_otp(
    payload: TransactionVerifyOTPRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    """
    Step 9 Factor 2: OTP Verification & Dynamic Adaptive Routing
    - Validates 6-digit OTP code against active challenge.
    - If LOW or MEDIUM risk: Automatically authorizes & completes the transaction!
    - If HIGH risk: Holds transfer & steps up to Factor 3 (Transaction-Bound Verification).
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
            detail="Transaction challenge session not found.",
        )

    if challenge.stage not in ["AWAITING_OTP"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Challenge is not awaiting OTP (current state: {challenge.stage}).",
        )

    now_utc = datetime.now(timezone.utc)
    challenge_exp = challenge.expires_at.replace(tzinfo=timezone.utc) if challenge.expires_at.tzinfo is None else challenge.expires_at
    if now_utc > challenge_exp:
        challenge.stage = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction challenge session has expired. Please initiate a new transfer.",
        )

    if challenge.attempts >= challenge.max_attempts:
        challenge.stage = "LOCKED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maximum verification attempts exceeded. Challenge locked for security.",
        )

    # Check OTP
    if challenge.otp_code != payload.otp_code.strip():
        challenge.attempts += 1
        db.commit()
        remaining = challenge.max_attempts - challenge.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining.",
        )

    # OTP Verified!
    challenge.otp_verified = True

    # ── BRANCH 1: LOW OR MEDIUM RISK (Streamlined Authorization) ──────────────
    if challenge.risk_tier in [RiskTier.LOW.value, RiskTier.MEDIUM.value]:
        # Frictionless completion for low/medium risk
        completed_tx = transfer_money(
            db=db,
            user=user,
            beneficiary_id=challenge.beneficiary_id,
            amount=challenge.amount,
            remark=challenge.remark,
            auth_mode="ADAPTIVE_SYSTEM_3",
            auth_factors="PASSWORD,OTP",
            risk_score=float(challenge.risk_score),
            risk_tier=challenge.risk_tier,
        )
        challenge.stage = "COMPLETED"
        db.commit()

        tx_out = TransactionOut(
            id=completed_tx.id,
            reference_id=completed_tx.reference_id,
            beneficiary_name=completed_tx.beneficiary.name,
            beneficiary_account=mask_account(completed_tx.beneficiary.account_number),
            amount=float(completed_tx.amount),
            remark=completed_tx.remark,
            status=completed_tx.status,
            auth_mode=completed_tx.auth_mode,
            auth_factors=completed_tx.auth_factors,
            risk_score=float(completed_tx.risk_score),
            risk_tier=completed_tx.risk_tier,
            cryptographic_seal=None,
            created_at=completed_tx.created_at,
        )

        return TransactionVerificationResponse(
            challenge_id=challenge.id,
            stage="COMPLETED",
            message=f"Transaction authorized successfully under {challenge.risk_tier} risk adaptive policy.",
            risk_score=float(challenge.risk_score),
            risk_tier=challenge.risk_tier,
            auth_action=challenge.auth_action,
            requires_step_up=False,
            transaction=tx_out,
        )

    # ── BRANCH 2: HIGH RISK (Mandates Step 8 Transaction-Bound Verification) ──
    else:
        challenge.stage = "AWAITING_HIGH_RISK_VERIFICATION"
        db.commit()

        beneficiary = db.query(Beneficiary).filter(Beneficiary.id == challenge.beneficiary_id).first()

        return TransactionVerificationResponse(
            challenge_id=challenge.id,
            stage="AWAITING_HIGH_RISK_VERIFICATION",
            message="OTP verified. High risk detected: Step-up transaction-bound verification is required.",
            risk_score=float(challenge.risk_score),
            risk_tier=challenge.risk_tier,
            auth_action=challenge.auth_action,
            requires_step_up=True,
            transaction=None,
            cryptographic_seal=challenge.cryptographic_seal,
            nonce=challenge.nonce,
            seal_timestamp=challenge.seal_timestamp,
            amount=float(challenge.amount),
            beneficiary_name=beneficiary.name if beneficiary else "",
            beneficiary_account=beneficiary.account_number if beneficiary else "",
            bank_name=beneficiary.bank_name if beneficiary else "",
            ifsc_code=beneficiary.ifsc_code if beneficiary else "",
            remark=challenge.remark,
        )


@router.post(
    "/confirm-high-risk",
    response_model=TransactionOut,
    status_code=status.HTTP_200_OK,
    summary="Factor 3: High-Risk Transaction-Bound Verification (PIN + Affirmation + Seal)",
)
def confirm_high_risk_transaction(
    payload: TransactionHighRiskConfirmRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    """
    Step 9 Factor 3 (Only required for HIGH risk):
    1. Validates challenge is in 'AWAITING_HIGH_RISK_VERIFICATION'.
    2. Validates explicit affirmations against social-engineering coercion.
    3. Authenticates 4-digit Transaction Security PIN.
    4. Cryptographically verifies HMAC-SHA256 parameter binding seal against tampering.
    5. Finalizes transfer and logs immutable audit receipt.
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
            detail="Transaction challenge session not found.",
        )

    if challenge.stage != "AWAITING_HIGH_RISK_VERIFICATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Challenge is not awaiting high-risk verification (current state: {challenge.stage}).",
        )

    # 1. Affirmation Checks
    if not payload.explicit_affirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit personal transaction confirmation is required.",
        )

    if not payload.anti_coercion_ack:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anti-coercion acknowledgement is required to authorize high-risk transfer.",
        )

    # 2. Transaction Security PIN Authentication
    if not verify_pin(payload.transaction_pin, user.transaction_pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Incorrect Transaction Security PIN.",
        )

    # 3. Cryptographic Binding Verification (PSD2 Article 97 / NIST SP 800-63B)
    account = db.query(Account).filter(Account.user_id == user.id).first()
    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == challenge.beneficiary_id).first()

    is_valid_seal, seal_error = crypto_engine.verify_transaction_seal(
        expected_seal=challenge.cryptographic_seal,
        challenge_id=challenge.id,
        sender_account=account.account_number,
        beneficiary_account=beneficiary.account_number,
        amount=float(challenge.amount),
        timestamp=challenge.seal_timestamp,
        nonce=challenge.nonce,
        ttl_seconds=settings.OTP_EXPIRE_SECONDS + 120,
    )

    if not is_valid_seal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cryptographic parameter binding failure: {seal_error}",
        )

    # 4. Finalize Transfer
    completed_tx = transfer_money(
        db=db,
        user=user,
        beneficiary_id=challenge.beneficiary_id,
        amount=challenge.amount,
        remark=challenge.remark,
        auth_mode="ADAPTIVE_SYSTEM_3",
        auth_factors="PASSWORD,OTP,TRANSACTION_BINDING_3FA",
        risk_score=float(challenge.risk_score),
        risk_tier=challenge.risk_tier,
        cryptographic_seal=challenge.cryptographic_seal,
    )

    challenge.stage = "COMPLETED"
    db.commit()

    return TransactionOut(
        id=completed_tx.id,
        reference_id=completed_tx.reference_id,
        beneficiary_name=completed_tx.beneficiary.name,
        beneficiary_account=mask_account(completed_tx.beneficiary.account_number),
        amount=float(completed_tx.amount),
        remark=completed_tx.remark,
        status=completed_tx.status,
        auth_mode=completed_tx.auth_mode,
        auth_factors=completed_tx.auth_factors,
        risk_score=float(completed_tx.risk_score),
        risk_tier=completed_tx.risk_tier,
        cryptographic_seal=completed_tx.cryptographic_seal,
        created_at=completed_tx.created_at,
    )


@router.post("/resend-otp", response_model=TransactionChallengeResponse)
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

    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge session not found.")

    if challenge.stage != "AWAITING_OTP":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot resend OTP for this challenge stage.")

    new_otp = generate_otp(6)
    challenge.otp_code = new_otp
    challenge.attempts = 0
    now_utc = datetime.now(timezone.utc)
    challenge.expires_at = now_utc + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    otp_audit = OTP(user_id=user.id, code=new_otp, purpose="TRANSACTION_RESEND")
    db.add(otp_audit)
    db.commit()

    beneficiary = db.query(Beneficiary).filter(Beneficiary.id == challenge.beneficiary_id).first()

    return TransactionChallengeResponse(
        challenge_id=challenge.id,
        stage="AWAITING_OTP",
        risk_score=float(challenge.risk_score),
        risk_tier=challenge.risk_tier,
        auth_action=challenge.auth_action,
        warning_banner=challenge.warning_banner,
        risk_reasons=json.loads(challenge.risk_reasons) if challenge.risk_reasons else [],
        requires_pin=challenge.requires_pin,
        requires_cryptographic_seal=challenge.requires_cryptographic_seal,
        cryptographic_seal=challenge.cryptographic_seal,
        nonce=challenge.nonce,
        seal_timestamp=challenge.seal_timestamp,
        message=f"Fresh OTP sent to {mask_phone(user.phone)}.",
        otp_display=new_otp,
        expires_in=settings.OTP_EXPIRE_SECONDS,
        amount=float(challenge.amount),
        beneficiary_name=beneficiary.name if beneficiary else "",
        beneficiary_account=mask_account(beneficiary.account_number) if beneficiary else "",
        masked_phone=mask_phone(user.phone),
    )


@router.post("/cancel")
def cancel_transaction(
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

    challenge.stage = "CANCELLED"
    db.commit()
    return {"message": "Transaction challenge cancelled successfully."}


@router.get("", response_model=list[TransactionOut])
def get_transactions(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    txs = list_user_transactions(db, user)
    result = []
    for t in txs:
        result.append(
            TransactionOut(
                id=t.id,
                reference_id=t.reference_id,
                beneficiary_name=t.beneficiary.name if t.beneficiary else "Unknown",
                beneficiary_account=mask_account(t.beneficiary.account_number) if t.beneficiary else "XXXX",
                amount=float(t.amount),
                remark=t.remark,
                status=t.status,
                failure_reason=t.failure_reason,
                auth_mode=t.auth_mode,
                auth_factors=t.auth_factors,
                risk_score=float(t.risk_score),
                risk_tier=t.risk_tier,
                cryptographic_seal=t.cryptographic_seal,
                created_at=t.created_at,
            )
        )
    return result
