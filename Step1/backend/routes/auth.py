from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import (
    create_access_token,
    generate_account_number,
    generate_otp,
    hash_password,
    verify_password,
    get_current_user,
)
from config import settings
from database import get_db
from models.account import Account
from models.user import User
from models.otp import OTP
from schemas.user import TokenResponse, UserLogin, UserOut, UserRegister
from schemas.otp import OTPRequest, OTPVerify, OTPResponse
from utils import mask_phone

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    existing_phone = db.query(User).filter(User.phone == payload.phone).first()
    if existing_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        phone=payload.phone.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    account_number = generate_account_number()
    while db.query(Account).filter(Account.account_number == account_number).first():
        account_number = generate_account_number()

    account = Account(
        user_id=user.id,
        account_number=account_number,
        ifsc_code="SIMB0001234",
        balance=settings.STARTING_BALANCE,
    )
    db.add(account)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Generate OTP for login verification
    otp_code = generate_otp()
    otp = OTP(
        user_id=user.id,
        code=otp_code,
        purpose="LOGIN",
    )
    db.add(otp)
    db.commit()

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        message=f"OTP sent to {mask_phone(user.phone)}. Please verify to continue.",
        requires_otp=True,
        otp_display=otp_code,  # Simulated: shown in UI for testing
    )


@router.post("/otp/generate", response_model=OTPResponse)
def request_otp(
    payload: OTPRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new OTP for the authenticated user."""
    otp_code = generate_otp()
    otp = OTP(
        user_id=user.id,
        code=otp_code,
        purpose=payload.purpose,
    )
    db.add(otp)
    db.commit()

    return OTPResponse(
        message=f"OTP sent to {mask_phone(user.phone)}",
        otp_display=otp_code,
        expires_in=settings.OTP_EXPIRE_SECONDS,
    )


@router.post("/otp/verify")
def verify_otp(
    payload: OTPVerify,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify an OTP."""
    from datetime import datetime, timezone, timedelta

    otp = (
        db.query(OTP)
        .filter(
            OTP.user_id == user.id,
            OTP.purpose == payload.purpose,
            OTP.is_used == False,
        )
        .order_by(OTP.created_at.desc())
        .first()
    )

    if not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending OTP found. Please request a new one.")

    # Check expiry
    now = datetime.now(timezone.utc)
    otp_created = otp.created_at.replace(tzinfo=timezone.utc) if otp.created_at.tzinfo is None else otp.created_at
    if now > otp_created + timedelta(seconds=settings.OTP_EXPIRE_SECONDS):
        otp.is_used = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired. Please request a new one.")

    # Check attempts
    if otp.attempts >= otp.max_attempts:
        otp.is_used = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum OTP attempts exceeded. Please request a new one.")

    otp.attempts += 1

    if otp.code != payload.code:
        db.commit()
        remaining = otp.max_attempts - otp.attempts
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
        )

    # OTP is valid
    otp.is_used = True
    db.commit()

    return {"message": "OTP verified successfully.", "verified": True}
