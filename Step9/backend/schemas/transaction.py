from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    beneficiary_id: int
    amount: Decimal = Field(gt=0)
    remark: Optional[str] = Field(None, max_length=200)


class TransactionInitiateRequest(BaseModel):
    """
    Step 9 Factor 1: Transfer details + Account Password verification.
    Triggers AI risk assessment & adaptive policy evaluation.
    """
    beneficiary_id: int
    amount: Decimal = Field(gt=0)
    remark: Optional[str] = Field(None, max_length=200)
    password: str = Field(min_length=1, description="Account password required for Factor 1")
    raw_features: Optional[List[float]] = Field(default=None, description="Optional raw tabular features for ML model")


class TransactionChallengeResponse(BaseModel):
    """
    Returned upon Factor 1 (Password) success & AI risk scoring.
    """
    challenge_id: str
    stage: str = "AWAITING_OTP"
    risk_score: float
    risk_tier: str
    auth_action: str
    warning_banner: Optional[str] = None
    risk_reasons: List[str] = []
    requires_pin: bool = False
    requires_cryptographic_seal: bool = False
    cryptographic_seal: Optional[str] = None
    nonce: Optional[str] = None
    seal_timestamp: Optional[int] = None
    message: str
    otp_display: str  # Simulated: shown in UI for research/demo testing
    expires_in: int
    amount: float
    beneficiary_name: str
    beneficiary_account: str
    masked_phone: str


class TransactionVerifyOTPRequest(BaseModel):
    """
    Step 9 Factor 2: Enter 6-digit OTP.
    - If LOW or MEDIUM risk: Completes transaction immediately!
    - If HIGH risk: Advances challenge to AWAITING_HIGH_RISK_VERIFICATION.
    """
    challenge_id: str
    otp_code: str = Field(min_length=6, max_length=6)


class TransactionOut(BaseModel):
    id: int
    reference_id: str
    beneficiary_name: str
    beneficiary_account: str
    amount: float
    remark: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    auth_mode: str = "ADAPTIVE_SYSTEM_3"
    auth_factors: str
    risk_score: float
    risk_tier: str
    cryptographic_seal: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionVerificationResponse(BaseModel):
    """
    Response from OTP verification.
    If LOW/MEDIUM: stage is COMPLETED, transaction object populated.
    If HIGH: stage is AWAITING_HIGH_RISK_VERIFICATION with step-up cryptographic parameters.
    """
    challenge_id: str
    stage: str
    message: str
    risk_score: float
    risk_tier: str
    auth_action: str
    requires_step_up: bool
    transaction: Optional[TransactionOut] = None
    # Step-up parameter fields if HIGH risk
    cryptographic_seal: Optional[str] = None
    nonce: Optional[str] = None
    seal_timestamp: Optional[int] = None
    amount: Optional[float] = None
    beneficiary_name: Optional[str] = None
    beneficiary_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc_code: Optional[str] = None
    remark: Optional[str] = None


class TransactionHighRiskConfirmRequest(BaseModel):
    """
    Step 9 Factor 3 (Only required for HIGH risk):
    Transaction-Bound verification with cryptographic seal integrity,
    explicit affirmations, and 4-digit Security PIN.
    """
    challenge_id: str
    transaction_pin: str = Field(min_length=4, max_length=6, description="4-digit Transaction Security PIN")
    explicit_affirmation: bool = Field(
        description="Explicit user confirmation that they personally initiated this transfer"
    )
    anti_coercion_ack: bool = Field(
        description="Explicit acknowledgement that user is not under coercion by phone caller or third party"
    )
    purpose_verified: bool = Field(
        default=True,
        description="Confirmation that transaction amount and destination account were personally inspected"
    )


class TransactionResendOTPRequest(BaseModel):
    challenge_id: str


class TransactionCancelRequest(BaseModel):
    challenge_id: str


class SetPINRequest(BaseModel):
    current_password: str
    new_pin: str = Field(min_length=4, max_length=6)
