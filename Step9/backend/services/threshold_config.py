"""
Threshold Configuration & Risk Tier Policies for Step 9
========================================================
Calibrated decision thresholds (tau_1 = 0.30, tau_2 = 0.70)
and adaptive authentication controls.
"""

from enum import Enum
from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AuthAction(str, Enum):
    NORMAL = "NORMAL"                         # Low Risk: Standard Password + OTP
    WARNING = "WARNING"                       # Medium Risk: Contextual Warning Banner + OTP
    STRONG_VERIFICATION = "STRONG_VERIFICATION" # High Risk: Step 8 Transaction-Bound 3FA (Seal + PIN)


class PolicyConfig(BaseModel):
    """Configuration parameters for the Adaptive Security Policy."""
    tau_low_medium: float = Field(
        default=0.30,
        description="Cutoff between LOW and MEDIUM risk (tau_1)."
    )
    tau_medium_high: float = Field(
        default=0.70,
        description="Cutoff between MEDIUM and HIGH risk (tau_2)."
    )

    new_beneficiary_boost: float = Field(default=0.15, description="Risk boost for new beneficiary")
    unusual_amount_boost: float = Field(default=0.20, description="Risk boost for transfers > 3x user median")
    off_hours_boost: float = Field(default=0.10, description="Risk boost for transactions between 01:00 and 05:00")
    rapid_velocity_boost: float = Field(default=0.25, description="Risk boost for rapid multiple transfers")

    fail_secure_default_tier: RiskTier = Field(default=RiskTier.HIGH)


DEFAULT_POLICY_CONFIG = PolicyConfig()
