from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_verified_user
from database import get_db
from models.user import User
from schemas.transaction import TransactionCreate, TransactionOut
from services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def mask_account(account_number: str) -> str:
    if len(account_number) <= 4:
        return account_number
    return "XXXX" + account_number[-4:]


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    """
    Transfer money to a beneficiary.

    Later project steps will insert additional authentication
    checks before calling the transaction service.
    """
    tx = transaction_service.transfer_money(
        db=db,
        user=user,
        beneficiary_id=payload.beneficiary_id,
        amount=payload.amount,
    )

    return TransactionOut(
        id=tx.id,
        beneficiary_name=tx.beneficiary.name,
        beneficiary_account=mask_account(tx.beneficiary.account_number),
        amount=float(tx.amount),
        status=tx.status,
        created_at=tx.created_at,
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
                beneficiary_name=tx.beneficiary.name if tx.beneficiary else "Unknown",
                beneficiary_account=mask_account(tx.beneficiary.account_number) if tx.beneficiary else "",
                amount=float(tx.amount),
                status=tx.status,
                created_at=tx.created_at,
            )
        )
    return result
