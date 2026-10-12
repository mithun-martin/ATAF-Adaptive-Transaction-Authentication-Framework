"""
Step 7: Threshold Configuration & Risk Tier Policies
=====================================================
Defines the calibrated decision thresholds (tau_1, tau_2) and the
associated cybersecurity authentication controls for each risk tier.

Calibrated based on Step 6 evaluation curves:
- PR-AUC: 0.6926, ROC-AUC: 0.9468 on IEEE-CIS test set.
- tau_1 = 0.30: Separates routine transactions from borderline unusual activity.
- tau_2 = 0.70: Separates warning-tier from severe anomaly / fraud-risk transfers.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AuthAction(str, Enum):
    NORMAL = "NORMAL"                         # Low Risk: Standard Password + OTP
    WARNING = "WARNING"                       # Medium Risk: Advisory Warning + OTP
    STRONG_VERIFICATION = "STRONG_VERIFICATION" # High Risk: Transaction-Bound 3FA (Seal + PIN)


class PolicyConfig(BaseModel):
    """Configuration parameters for the Adaptive Security Policy."""
    # Machine Learning Probability Thresholds
    tau_low_medium: float = Field(
        default=0.30,
        description="Cutoff between LOW and MEDIUM risk (tau_1). Below this is routine authentication."
    )
    tau_medium_high: float = Field(
        default=0.70,
        description="Cutoff between MEDIUM and HIGH risk (tau_2). Above this mandates strong verification."
    )

    # Heuristic Rule Weights (Boost to raw model score for specific critical banking flags)
    new_beneficiary_boost: float = Field(default=0.15, description="Risk boost for unverified or newly added beneficiary")
    unusual_amount_boost: float = Field(default=0.20, description="Risk boost for transfers > 3x user median")
    off_hours_boost: float = Field(default=0.10, description="Risk boost for transactions between 01:00 and 05:00")
    rapid_velocity_boost: float = Field(default=0.25, description="Risk boost for multiple transfers within 10 minutes")

    # Fail-Secure Setting: If AI engine fails or is unreachable, default to HIGH risk tier
    fail_secure_default_tier: RiskTier = Field(default=RiskTier.HIGH)


DEFAULT_POLICY_CONFIG = PolicyConfig()
