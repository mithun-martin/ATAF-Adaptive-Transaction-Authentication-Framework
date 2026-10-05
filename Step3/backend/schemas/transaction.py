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
    Step 3 Static 3FA Factor 1: Transfer details + Account Password verification.
    """
    beneficiary_id: int
    amount: Decimal = Field(gt=0)
    remark: Optional[str] = Field(None, max_length=200)
    password: str = Field(min_length=1, description="Account password required for Factor 1")


class TransactionChallengeResponse(BaseModel):
    """
    Returned upon Factor 1 (Password) success, issuing challenge in AWAITING_OTP stage.
    """
    challenge_id: str
    stage: str = "AWAITING_OTP"
    message: str
    otp_display: str  # Simulated: shown in UI for testing/research
    expires_in: int
    amount: float
    beneficiary_name: str
    beneficiary_account: str
    masked_phone: str


class TransactionVerifyOTPRequest(BaseModel):
    """
    Step 3 Static 3FA Factor 2: Enter 6-digit OTP.
    """
    challenge_id: str
    otp_code: str = Field(min_length=6, max_length=6)


class TransactionAdditionalVerificationStageResponse(BaseModel):
    """
    Returned upon Factor 2 (OTP) success, advancing challenge to Factor 3 (Additional Verification).
    Provides cryptographic binding seal and explicit transaction details.
    """
    challenge_id: str
    stage: str = "AWAITING_ADDITIONAL_CONFIRMATION"
    message: str
    cryptographic_seal: str
    nonce: str
    amount: float
    beneficiary_name: str
    beneficiary_account: str
    bank_name: str
    ifsc_code: str
    remark: Optional[str] = None
    prompt: str = "Did you personally initiate this transaction?"


class TransactionAdditionalVerificationRequest(BaseModel):
    """
    Step 3 Static 3FA Factor 3: Transaction-Bound Additional Confirmation.
    Requires explicit confirmation, anti-coercion confirmation, and Transaction Security PIN.
    """
    challenge_id: str
    transaction_pin: str = Field(min_length=4, max_length=6, description="4-digit Transaction Security PIN")
    explicit_confirmation: bool = Field(
        description="Explicit user confirmation that they personally initiated this transaction"
    )
    anti_coercion_confirmation: bool = Field(
        description="Explicit verification that no caller or third party instructed this transfer"
    )


class TransactionResendOTPRequest(BaseModel):
    challenge_id: str


class TransactionCancelRequest(BaseModel):
    challenge_id: str


class SetPINRequest(BaseModel):
    current_password: str
    new_pin: str = Field(min_length=4, max_length=6)


class TransactionOut(BaseModel):
    id: int
    reference_id: str
    beneficiary_name: str
    beneficiary_account: str
    amount: float
    remark: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    auth_mode: str = "STATIC_3FA"
    auth_factors: str = "PASSWORD,OTP,ADDITIONAL_CONFIRMATION"
    cryptographic_seal: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
