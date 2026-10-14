from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_verified_user
from database import get_db
from models.beneficiary import Beneficiary
from models.transaction import Transaction
from models.user import User
from schemas.beneficiary import BeneficiaryCreate, BeneficiaryOut

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
    return rows


@router.post("", response_model=BeneficiaryOut, status_code=status.HTTP_201_CREATED)
def add_beneficiary(
    payload: BeneficiaryCreate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
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
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)

    return beneficiary


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
