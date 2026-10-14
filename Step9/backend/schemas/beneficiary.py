from datetime import datetime
from pydantic import BaseModel, Field


class BeneficiaryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_number: str = Field(min_length=8, max_length=20)
    bank_name: str = Field(min_length=1, max_length=100)
    ifsc_code: str = Field(min_length=11, max_length=11)


class BeneficiaryOut(BaseModel):
    id: int
    name: str
    account_number: str
    bank_name: str
    ifsc_code: str
    created_at: datetime

    class Config:
        from_attributes = True
