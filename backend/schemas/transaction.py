from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    beneficiary_id: int
    amount: Decimal = Field(gt=0)
    remark: Optional[str] = Field(None, max_length=200)


class TransactionOut(BaseModel):
    id: int
    reference_id: str
    beneficiary_name: str
    beneficiary_account: str
    amount: float
    remark: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
