import random
import string
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.account import Account
from models.beneficiary import Beneficiary
from models.transaction import Transaction
from models.user import User


def generate_reference_id() -> str:
    """Generate a unique transaction reference ID like TXN-XXXXXX."""
    chars = string.ascii_uppercase + string.digits
    return "TXN" + "".join(random.choices(chars, k=10))


def transfer_money(
    db: Session,
    user: User,
    beneficiary_id: int,
    amount: Decimal,
    remark: str | None = None,
) -> Transaction:
    """
    Execute a money transfer.

    Auth is handled by the route layer. This service only moves money
    and records the transaction so later steps can insert extra
    authentication between the request and this call.
    """
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    beneficiary = (
        db.query(Beneficiary)
        .filter(Beneficiary.id == beneficiary_id, Beneficiary.user_id == user.id)
        .first()
    )
    if not beneficiary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")

    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    current_balance = Decimal(str(account.balance))

    # Generate unique reference ID
    ref_id = generate_reference_id()
    while db.query(Transaction).filter(Transaction.reference_id == ref_id).first():
        ref_id = generate_reference_id()

    if amount > current_balance:
        failed = Transaction(
            reference_id=ref_id,
            sender_account_id=account.id,
            beneficiary_id=beneficiary.id,
            amount=float(amount),
            remark=remark,
            status="FAILED",
            failure_reason="Insufficient balance",
        )
        db.add(failed)
        db.commit()
        db.refresh(failed)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )

    account.balance = float(current_balance - amount)

    completed = Transaction(
        reference_id=ref_id,
        sender_account_id=account.id,
        beneficiary_id=beneficiary.id,
        amount=float(amount),
        remark=remark,
        status="COMPLETED",
    )
    db.add(completed)
    db.commit()
    db.refresh(completed)
    return completed


def list_user_transactions(db: Session, user: User) -> list[Transaction]:
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        return []

    return (
        db.query(Transaction)
        .filter(Transaction.sender_account_id == account.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
