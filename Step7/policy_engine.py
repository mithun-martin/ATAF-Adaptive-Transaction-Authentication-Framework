"""
Step 7: Adaptive Security Policy Engine
========================================
Implements the core decision logic mapping AI risk scores to authentication actions.

Tri-Tier Policy Matrix:
  - LOW RISK    (R < tau_1):         Normal Authentication (Password + OTP)
  - MEDIUM RISK (tau_1 <= R < tau_2): Additional Warning Banner + OTP
  - HIGH RISK   (R >= tau_2):        Strong Verification (Transaction-Bound 3FA + PIN)

Includes fail-secure default handling in compliance with cybersecurity best practices.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from threshold_config import (
    RiskTier,
    AuthAction,
    PolicyConfig,
    DEFAULT_POLICY_CONFIG,
)
from scorer import RiskScorer


class PolicyDecision(BaseModel):
    """Structured decision output produced by the Adaptive Security Policy Engine."""
    risk_score: float = Field(..., description="Calculated risk probability R in [0.0, 1.0]")
    risk_tier: RiskTier = Field(..., description="Categorized tier: LOW, MEDIUM, or HIGH")
    auth_action: AuthAction = Field(..., description="Required enforcement: NORMAL, WARNING, or STRONG_VERIFICATION")
    required_factors: List[str] = Field(..., description="List of factors required to authorize transaction")
    warning_banner: Optional[str] = Field(None, description="Contextual warning text if MEDIUM or HIGH risk")
    risk_reasons: List[str] = Field(default_factory=list, description="Specific triggers that elevated the risk score")
    requires_pin: bool = Field(default=False, description="Whether 4-digit Transaction Security PIN is mandated")
    requires_cryptographic_seal: bool = Field(default=False, description="Whether HMAC-SHA256 transaction binding seal is required")
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
        Directly evaluates an already-computed AI risk score against policy thresholds.
        Used when the AI model runs in an external service or prior pipeline step.
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
            warning_msg = (
                f"⚠️ CAUTION: Unusual transaction activity detected ({', '.join(reasons) if reasons else 'irregular pattern'}). "
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
            amount_str = f"₹{tx.get('amount', 0):,.2f}" if "amount" in tx else "this transaction"
            high_risk_msg = (
                f"🚨 HIGH-RISK TRANSACTION ALERT: ATAF AI detected severe anomaly patterns ({', '.join(reasons) if reasons else 'high-fraud probability indicators'}). "
                f"To protect against unauthorized transfers and coercive fraud, strong transaction-bound cryptographic "
                f"affirmation and your Transaction Security PIN are strictly required to authorize {amount_str} to {recipient_name}."
            )
            return PolicyDecision(
                risk_score=score,
                risk_tier=RiskTier.HIGH,
                auth_action=AuthAction.STRONG_VERIFICATION,
                required_factors=["PASSWORD", "OTP", "ADDITIONAL_CONFIRMATION"],
                warning_banner=high_risk_msg,
                risk_reasons=reasons,
                requires_pin=True,
                requires_cryptographic_seal=True,
            )

    def evaluate_transaction(self, transaction: Dict[str, Any]) -> PolicyDecision:
        """
        End-to-end evaluation: Takes transaction dictionary, computes AI risk score,
        and applies the adaptive authentication policy.
        """
        try:
            score, reasons = self.scorer.score_transaction(transaction)
            return self.evaluate_risk_score(
                risk_score=score,
                transaction_details=transaction,
                risk_reasons=reasons,
            )
        except Exception as e:
            # Cybersecurity Fail-Secure Principle:
            # If any failure occurs during risk scoring, NEVER default to low friction.
            # Escalate safely to Strong Verification.
            return PolicyDecision(
                risk_score=1.0,
                risk_tier=self.config.fail_secure_default_tier,
                auth_action=AuthAction.STRONG_VERIFICATION,
                required_factors=["PASSWORD", "OTP", "ADDITIONAL_CONFIRMATION"],
                warning_banner=f"Security engine encountered an evaluation anomaly ({str(e)}). Defaulting to Strong Verification for account security.",
                risk_reasons=["AI_SCORER_FAIL_SECURE_TRIGGER"],
                requires_pin=True,
                requires_cryptographic_seal=True,
                fail_secure_fallback=True,
            )
