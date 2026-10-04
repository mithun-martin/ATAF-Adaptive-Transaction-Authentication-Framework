from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_verified_user
from database import get_db
from models.beneficiary import Beneficiary
from models.transaction import Transaction
from models.user import User
from schemas.beneficiary import BeneficiaryCreate, BeneficiaryOut
from utils import mask_account

router = APIRouter(prefix="/beneficiaries", tags=["Beneficiaries"])


@router.get("", response_model=list[BeneficiaryOut])
def list_beneficiaries(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Beneficiary)
        .filter(Beneficiary.user_id == user.id)
        .order_by(Beneficiary.created_at.desc())
        .all()
    )
    result = []
    for b in rows:
        result.append(
            BeneficiaryOut(
                id=b.id,
                name=b.name,
                account_number=b.account_number,
                ifsc_code=b.ifsc_code,
                bank_name=b.bank_name,
                nickname=b.nickname,
                created_at=b.created_at,
                masked_account=mask_account(b.account_number),
            )
        )
    return result


@router.post("", response_model=BeneficiaryOut, status_code=status.HTTP_201_CREATED)
def add_beneficiary(
    payload: BeneficiaryCreate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    # Check for duplicate beneficiary (same account number for this user)
    existing = (
        db.query(Beneficiary)
        .filter(
            Beneficiary.user_id == user.id,
            Beneficiary.account_number == payload.account_number.strip(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A beneficiary with this account number already exists.",
        )

    beneficiary = Beneficiary(
        user_id=user.id,
        name=payload.name.strip(),
        account_number=payload.account_number.strip(),
        ifsc_code=payload.ifsc_code.strip().upper(),
        bank_name=payload.bank_name.strip(),
        nickname=payload.nickname.strip() if payload.nickname else None,
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)

    return BeneficiaryOut(
        id=beneficiary.id,
        name=beneficiary.name,
        account_number=beneficiary.account_number,
        ifsc_code=beneficiary.ifsc_code,
        bank_name=beneficiary.bank_name,
        nickname=beneficiary.nickname,
        created_at=beneficiary.created_at,
        masked_account=mask_account(beneficiary.account_number),
    )


@router.delete("/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_beneficiary(
    beneficiary_id: int,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    beneficiary = (
        db.query(Beneficiary)
        .filter(Beneficiary.id == beneficiary_id, Beneficiary.user_id == user.id)
        .first()
    )
    if not beneficiary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")

    # Check if beneficiary has transactions — soft-prevent deletion
    tx_count = (
        db.query(Transaction)
        .filter(Transaction.beneficiary_id == beneficiary_id)
        .count()
    )
    if tx_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete: {tx_count} transaction(s) linked to this beneficiary.",
        )

    db.delete(beneficiary)
    db.commit()
    return None
