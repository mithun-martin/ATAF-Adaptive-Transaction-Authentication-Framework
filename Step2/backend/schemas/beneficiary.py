from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BeneficiaryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_number: str = Field(min_length=4, max_length=20)
    ifsc_code: str = Field(min_length=4, max_length=11, default="OTHR0001234")
    bank_name: str = Field(min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, max_length=50)


class BeneficiaryOut(BaseModel):
    id: int
    name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    nickname: Optional[str] = None
    masked_account: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
