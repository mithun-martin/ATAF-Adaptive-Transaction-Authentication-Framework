from pydantic import BaseModel


class AccountOut(BaseModel):
    account_number: str
    ifsc_code: str
    balance: float
    user_name: str
    user_phone: str
    masked_phone: str

    class Config:
        from_attributes = True
