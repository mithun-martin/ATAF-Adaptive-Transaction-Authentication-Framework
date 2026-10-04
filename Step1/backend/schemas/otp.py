from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    """Request to generate an OTP."""
    purpose: str = Field(default="LOGIN", pattern="^(LOGIN|TRANSACTION)$")


class OTPVerify(BaseModel):
    """Submit an OTP for verification."""
    code: str = Field(min_length=6, max_length=6)
    purpose: str = Field(default="LOGIN", pattern="^(LOGIN|TRANSACTION)$")


class OTPResponse(BaseModel):
    """Response after OTP generation.
    
    In simulation mode, the OTP code is included in the response
    so it can be displayed in the UI. In production, this would
    be sent via SMS only.
    """
    message: str
    otp_display: str  # Simulated: actual OTP shown for testing
    expires_in: int  # seconds
