from typing import Optional
from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    purpose: str = Field(default="LOGIN", max_length=50)


class OTPVerify(BaseModel):
    code: str = Field(min_length=6, max_length=6)
    purpose: str = Field(default="LOGIN", max_length=50)


class OTPResponse(BaseModel):
    message: str
    otp_display: Optional[str] = None
    expires_in: int = 180
