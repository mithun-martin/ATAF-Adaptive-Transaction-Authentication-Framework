from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_verified_user
from database import get_db
from models.user import User
from schemas.transaction import TransactionCreate, TransactionOut
from services import transaction_service
from utils import mask_account

router = APIRouter(prefix="/transactions", tags=["Transactions"])


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
        remark=payload.remark,
    )

    return TransactionOut(
        id=tx.id,
        reference_id=tx.reference_id,
        beneficiary_name=tx.beneficiary.name,
        beneficiary_account=mask_account(tx.beneficiary.account_number),
        amount=float(tx.amount),
        remark=tx.remark,
        status=tx.status,
        failure_reason=tx.failure_reason,
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
                reference_id=tx.reference_id,
                beneficiary_name=tx.beneficiary.name if tx.beneficiary else "Unknown",
                beneficiary_account=mask_account(tx.beneficiary.account_number) if tx.beneficiary else "",
                amount=float(tx.amount),
                remark=tx.remark,
                status=tx.status,
                failure_reason=tx.failure_reason,
                created_at=tx.created_at,
            )
        )
    return result
