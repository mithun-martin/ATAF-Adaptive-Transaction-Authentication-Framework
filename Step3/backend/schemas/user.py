from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    password: str = Field(min_length=6, max_length=100)
    transaction_pin: Optional[str] = Field(default="1234", min_length=4, max_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    message: str = "Login successful."
    requires_otp: bool = False
    otp_display: Optional[str] = None  # Simulated: shown in response for testing


class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    masked_phone: str
    account_number: str
    ifsc_code: str
    balance: float
    has_transaction_pin: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class AccountOut(BaseModel):
    account_number: str
    ifsc_code: str
    balance: float
    user_name: str
    user_phone: str
    masked_phone: str

    class Config:
        from_attributes = True
