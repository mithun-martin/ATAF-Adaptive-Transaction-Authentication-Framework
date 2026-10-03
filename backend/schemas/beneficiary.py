from datetime import datetime

from pydantic import BaseModel, Field


class BeneficiaryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_number: str = Field(min_length=4, max_length=20)
    bank_name: str = Field(min_length=1, max_length=100)


class BeneficiaryOut(BaseModel):
    id: int
    name: str
    account_number: str
    bank_name: str
    created_at: datetime
    masked_account: str | None = None

    class Config:
        from_attributes = True
