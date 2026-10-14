"""
Step 9: Adaptive Security Policy Engine
========================================
Implements the core decision logic mapping AI risk scores to authentication actions.

Tri-Tier Policy Matrix:
  - LOW RISK    (R < tau_1):         Normal Authentication (Password + OTP)
  - MEDIUM RISK (tau_1 <= R < tau_2): Contextual Warning Banner + OTP
  - HIGH RISK   (R >= tau_2):        Strong Verification (Transaction-Bound 3FA + PIN)

Includes fail-secure default handling in compliance with cybersecurity standards.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from services.threshold_config import (
    RiskTier,
    AuthAction,
    PolicyConfig,
    DEFAULT_POLICY_CONFIG,
)
from services.risk_scorer import RiskScorer


class PolicyDecision(BaseModel):
    """Structured decision output produced by the Adaptive Security Policy Engine."""
    risk_score: float = Field(..., description="Calculated risk probability R in [0.0, 1.0]")
    risk_tier: RiskTier = Field(..., description="Categorized tier: LOW, MEDIUM, or HIGH")
    auth_action: AuthAction = Field(..., description="Required enforcement: NORMAL, WARNING, or STRONG_VERIFICATION")
    required_factors: List[str] = Field(..., description="List of factors required to authorize transaction")
    warning_banner: Optional[str] = Field(None, description="Contextual warning text if MEDIUM or HIGH risk")
    risk_reasons: List[str] = Field(default_factory=list, description="Specific triggers that elevated the risk score")
    requires_pin: bool = Field(default=False, description="Whether 4-digit Transaction Security PIN is mandated")
    requires_cryptographic_seal: bool = Field(default=False, description="Whether HMAC-SHA256 seal is required")
    fail_secure_fallback: bool = Field(default=False, description="Whether policy was triggered via fail-safe handler")


class AdaptivePolicyEngine:
    """
    Evaluates transaction context and AI risk score to produce an adaptive authentication decision.
    """

    def __init__(
        self,
        config: Optional[PolicyConfig] = None,
        scorer: Optional[RiskScorer] = None,
    ):
        self.config = config or DEFAULT_POLICY_CONFIG
        self.scorer = scorer or RiskScorer()

    def evaluate_risk_score(
        self,
        risk_score: float,
        transaction_details: Optional[Dict[str, Any]] = None,
        risk_reasons: Optional[List[str]] = None,
    ) -> PolicyDecision:
        """
        Evaluates an AI risk score against calibrated policy thresholds (tau_1, tau_2).
        """
        reasons = list(risk_reasons or [])
        tx = transaction_details or {}
        score = float(max(0.0, min(1.0, risk_score)))

        # ── TIER 1: LOW RISK ──────────────────────────────────────────────────
        if score < self.config.tau_low_medium:
            return PolicyDecision(
                risk_score=score,
                risk_tier=RiskTier.LOW,
                auth_action=AuthAction.NORMAL,
                required_factors=["PASSWORD", "OTP"],
                warning_banner=None,
                risk_reasons=reasons,
                requires_pin=False,
                requires_cryptographic_seal=False,
            )

        # ── TIER 2: MEDIUM RISK ───────────────────────────────────────────────
        elif score < self.config.tau_medium_high:
            amount_str = f"₹{tx.get('amount', 0):,.2f}" if "amount" in tx else "this amount"
            reasons_str = "; ".join(reasons) if reasons else "unusual activity pattern"
            warning_msg = (
                f"⚠️ CAUTION: Unusual transaction activity detected ({reasons_str}). "
                f"If you were instructed to transfer {amount_str} over an unsolicited phone call, remote desktop app, "
                f"or urgent message, this may be an impersonation scam. Please verify recipient details before entering your OTP."
            )
            return PolicyDecision(
                risk_score=score,
                risk_tier=RiskTier.MEDIUM,
                auth_action=AuthAction.WARNING,
                required_factors=["PASSWORD", "OTP"],
                warning_banner=warning_msg,
                risk_reasons=reasons,
                requires_pin=False,
                requires_cryptographic_seal=False,
            )

        # ── TIER 3: HIGH RISK ─────────────────────────────────────────────────
        else:
            recipient_name = tx.get("beneficiary_name", "the recipient")
            amount_str = f"₹{tx.get('amount', 0):,.2f}" if "amount" in tx else "this amount"
            reasons_str = "; ".join(reasons) if reasons else "high anomaly detection"
            warning_msg = (
                f"🚨 HIGH RISK FRAUD ALERT: Critical risk indicators detected ({reasons_str}). "
                f"In accordance with Adaptive Security Policy, strong transaction-bound authentication "
                f"is strictly enforced. You must review the locked transaction parameters, sign an anti-coercion "
                f"affirmation, and enter your 4-digit Transaction Security PIN to authorize this transfer."
            )
            return PolicyDecision(
                risk_score=score,
                risk_tier=RiskTier.HIGH,
                auth_action=AuthAction.STRONG_VERIFICATION,
                required_factors=["PASSWORD", "OTP", "TRANSACTION_BINDING_3FA"],
                warning_banner=warning_msg,
                risk_reasons=reasons,
                requires_pin=True,
                requires_cryptographic_seal=True,
            )

    def evaluate_transaction(self, transaction_details: Dict[str, Any]) -> PolicyDecision:
        """End-to-end evaluation: scores transaction with AI, then maps to policy action."""
        try:
            risk_score, risk_reasons = self.scorer.score_transaction(transaction_details)
            return self.evaluate_risk_score(
                risk_score=risk_score,
                transaction_details=transaction_details,
                risk_reasons=risk_reasons,
            )
        except Exception as e:
            # Fail-Secure Fallback
            decision = self.evaluate_risk_score(
                risk_score=1.0,
                transaction_details=transaction_details,
                risk_reasons=[f"Fail-secure fallback triggered: Risk engine evaluation error ({str(e)})"],
            )
            decision.fail_secure_fallback = True
            return decision
