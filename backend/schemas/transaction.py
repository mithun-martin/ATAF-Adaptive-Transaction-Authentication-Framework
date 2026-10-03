from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    beneficiary_id: int
    amount: Decimal = Field(gt=0)


class TransactionOut(BaseModel):
    id: int
    beneficiary_name: str
    beneficiary_account: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
