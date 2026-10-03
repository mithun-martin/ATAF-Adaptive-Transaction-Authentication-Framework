from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_verified_user
from database import get_db
from models.beneficiary import Beneficiary
from models.user import User
from schemas.beneficiary import BeneficiaryCreate, BeneficiaryOut

router = APIRouter(prefix="/beneficiaries", tags=["Beneficiaries"])


def mask_account(account_number: str) -> str:
    if len(account_number) <= 4:
        return account_number
    return "XXXX" + account_number[-4:]


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
                bank_name=b.bank_name,
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
    beneficiary = Beneficiary(
        user_id=user.id,
        name=payload.name.strip(),
        account_number=payload.account_number.strip(),
        bank_name=payload.bank_name.strip(),
    )
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)

    return BeneficiaryOut(
        id=beneficiary.id,
        name=beneficiary.name,
        account_number=beneficiary.account_number,
        bank_name=beneficiary.bank_name,
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

    db.delete(beneficiary)
    db.commit()
    return None
