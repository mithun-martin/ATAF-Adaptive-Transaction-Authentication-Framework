from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    beneficiary_id: int
    amount: Decimal = Field(gt=0)
    remark: Optional[str] = Field(None, max_length=200)


class TransactionInitiateRequest(BaseModel):
    """
    Step 2 Baseline Factor 1: Transfer details + Account Password verification.
    """
    beneficiary_id: int
    amount: Decimal = Field(gt=0)
    remark: Optional[str] = Field(None, max_length=200)
    password: str = Field(min_length=1, description="Account password required for transaction authorization")


class TransactionChallengeResponse(BaseModel):
    """
    Returned upon successful password verification, issuing a pending transaction challenge with OTP.
    """
    challenge_id: str
    message: str
    otp_display: str  # Simulated: shown in UI for testing/research
    expires_in: int  # in seconds
    amount: float
    beneficiary_name: str
    beneficiary_account: str
    masked_phone: str


class TransactionVerifyOTPRequest(BaseModel):
    """
    Step 2 Baseline Factor 2: Enter 6-digit OTP to finalize transaction.
    """
    challenge_id: str
    otp_code: str = Field(min_length=6, max_length=6)


class TransactionResendOTPRequest(BaseModel):
    challenge_id: str


class TransactionCancelRequest(BaseModel):
    challenge_id: str


class TransactionOut(BaseModel):
    id: int
    reference_id: str
    beneficiary_name: str
    beneficiary_account: str
    amount: float
    remark: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    auth_mode: str = "BASELINE"
    auth_factors: str = "PASSWORD,OTP"
    created_at: datetime

    class Config:
        from_attributes = True
