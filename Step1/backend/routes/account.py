from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_verified_user
from database import get_db
from models.account import Account
from models.user import User
from schemas.user import AccountOut, UserProfile
from utils import mask_phone

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("", response_model=AccountOut)
def get_account(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    return AccountOut(
        account_number=account.account_number,
        ifsc_code=account.ifsc_code,
        balance=float(account.balance),
        user_name=user.name,
        user_phone=user.phone,
        masked_phone=mask_phone(user.phone),
    )


@router.get("/profile", response_model=UserProfile)
def get_profile(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        masked_phone=mask_phone(user.phone),
        account_number=account.account_number,
        ifsc_code=account.ifsc_code,
        balance=float(account.balance),
        created_at=user.created_at,
    )
