"""
Test Suite for Step 7: Adaptive Security Policy Engine
======================================================
Tests all three tiers (Low, Medium, High), threshold boundaries,
anti-social-engineering warning banners, and fail-secure robustness.
"""

import pytest
from threshold_config import RiskTier, AuthAction, PolicyConfig
from policy_engine import AdaptivePolicyEngine, PolicyDecision
from scorer import RiskScorer


@pytest.fixture
def policy_engine():
    config = PolicyConfig(tau_low_medium=0.30, tau_medium_high=0.70)
    return AdaptivePolicyEngine(config=config)


# ─── 1. Direct Score Tests ────────────────────────────────────────────────────

def test_low_risk_tier(policy_engine):
    decision = policy_engine.evaluate_risk_score(0.15)
    assert decision.risk_tier == RiskTier.LOW
    assert decision.auth_action == AuthAction.NORMAL
    assert decision.required_factors == ["PASSWORD", "OTP"]
    assert decision.requires_pin is False
    assert decision.requires_cryptographic_seal is False
    assert decision.warning_banner is None


def test_medium_risk_tier(policy_engine):
    decision = policy_engine.evaluate_risk_score(
        0.45,
        transaction_details={"amount": 12000.0},
        risk_reasons=["Transfer amount moderately exceeds typical baseline"]
    )
    assert decision.risk_tier == RiskTier.MEDIUM
    assert decision.auth_action == AuthAction.WARNING
    assert decision.required_factors == ["PASSWORD", "OTP"]
    assert decision.requires_pin is False
    assert decision.requires_cryptographic_seal is False
    assert decision.warning_banner is not None
    assert "CAUTION" in decision.warning_banner
    assert "₹12,000.00" in decision.warning_banner


def test_high_risk_tier(policy_engine):
    decision = policy_engine.evaluate_risk_score(
        0.85,
        transaction_details={"amount": 90000.0, "beneficiary_name": "Unknown Entity"},
        risk_reasons=["Transfer amount is 18.0x higher than typical volume", "New beneficiary added recently"]
    )
    assert decision.risk_tier == RiskTier.HIGH
    assert decision.auth_action == AuthAction.STRONG_VERIFICATION
    assert decision.required_factors == ["PASSWORD", "OTP", "ADDITIONAL_CONFIRMATION"]
    assert decision.requires_pin is True
    assert decision.requires_cryptographic_seal is True
    assert decision.warning_banner is not None
    assert "HIGH-RISK" in decision.warning_banner
    assert "Unknown Entity" in decision.warning_banner


# ─── 2. Threshold Boundary Tests ──────────────────────────────────────────────

def test_threshold_boundaries(policy_engine):
    # Exactly at tau_1 (0.30) -> should be MEDIUM
    d_boundary_1 = policy_engine.evaluate_risk_score(0.30)
    assert d_boundary_1.risk_tier == RiskTier.MEDIUM

    # Just below tau_1 (0.299) -> should be LOW
    d_below_1 = policy_engine.evaluate_risk_score(0.299)
    assert d_below_1.risk_tier == RiskTier.LOW

    # Exactly at tau_2 (0.70) -> should be HIGH
    d_boundary_2 = policy_engine.evaluate_risk_score(0.70)
    assert d_boundary_2.risk_tier == RiskTier.HIGH

    # Just below tau_2 (0.699) -> should be MEDIUM
    d_below_2 = policy_engine.evaluate_risk_score(0.699)
    assert d_below_2.risk_tier == RiskTier.MEDIUM


# ─── 3. End-to-End Contextual Transaction Tests ───────────────────────────────

def test_routine_grocery_transaction(policy_engine):
    tx = {
        "amount": 750.0,
        "user_avg_amount": 5000.0,
        "is_new_beneficiary": False,
        "hour_of_day": 14,
        "velocity_last_hour": 0,
    }
    decision = policy_engine.evaluate_transaction(tx)
    assert decision.risk_tier == RiskTier.LOW
    assert decision.auth_action == AuthAction.NORMAL


def test_unusual_amount_transaction(policy_engine):
    tx = {
        "amount": 28000.0,
        "user_avg_amount": 4000.0,
        "is_new_beneficiary": False,
        "hour_of_day": 16,
        "velocity_last_hour": 1,
    }
    decision = policy_engine.evaluate_transaction(tx)
    # Amount > 3x avg should trigger moderate boost
    assert decision.risk_tier in [RiskTier.MEDIUM, RiskTier.HIGH]
    assert len(decision.risk_reasons) > 0


def test_social_engineering_urgent_scam_transaction(policy_engine):
    # Classic vishing profile: very large amount + new beneficiary + night hours (3 AM)
    tx = {
        "amount": 85000.0,
        "beneficiary_name": "Suspicious Account",
        "user_avg_amount": 3000.0,
        "is_new_beneficiary": True,
        "hour_of_day": 3,
        "velocity_last_hour": 2,
    }
    decision = policy_engine.evaluate_transaction(tx)
    assert decision.risk_tier == RiskTier.HIGH
    assert decision.auth_action == AuthAction.STRONG_VERIFICATION
    assert decision.requires_pin is True
    assert decision.requires_cryptographic_seal is True
    assert "Suspicious Account" in decision.warning_banner


# ─── 4. Fail-Secure Robustness Test ───────────────────────────────────────────

def test_fail_secure_default():
    class BrokenScorer:
        def score_transaction(self, tx):
            raise RuntimeError("Database connection timed out during risk assessment")

    engine = AdaptivePolicyEngine(scorer=BrokenScorer())
    decision = engine.evaluate_transaction({"amount": 100.0})

    # Must fail securely into HIGH risk
    assert decision.risk_tier == RiskTier.HIGH
    assert decision.auth_action == AuthAction.STRONG_VERIFICATION
    assert decision.fail_secure_fallback is True
    assert decision.requires_pin is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
