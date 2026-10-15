"""
Step 10: Social-Engineering Attack Simulation Engine
=====================================================
Executes attack and benign control scenarios against:
  1. System 1 (Baseline: Password -> OTP)
  2. System 2 (Static 3FA: Password -> OTP -> Additional Confirmation)
  3. System 3 (Proposed Adaptive: Password -> AI Risk -> Dynamic Policy)

Quantifies security outcomes (fraud stopped vs. compromised) and user
friction (number of steps, factors enforced, and warnings rendered).
"""

import os
import sys
from typing import Dict, Any, List, Tuple

# Enable loading Step 7 policy engine and Step 5 models
STEP7_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Step7"))
if STEP7_DIR not in sys.path:
    sys.path.insert(0, STEP7_DIR)

from threshold_config import RiskTier, AuthAction, PolicyConfig, DEFAULT_POLICY_CONFIG
from policy_engine import AdaptivePolicyEngine
from scorer import RiskScorer
from scenarios.models import (
    AttackScenario,
    SystemEvaluationOutcome,
    ScenarioExecutionReport,
)
from scenarios.catalog import default_catalog


class AttackSimulator:
    """Simulates social-engineering attacks against all three authentication paradigms."""

    def __init__(self, policy_engine: AdaptivePolicyEngine = None):
        self.policy_engine = policy_engine or AdaptivePolicyEngine(
            config=DEFAULT_POLICY_CONFIG,
            scorer=RiskScorer(),
        )

    # ── 1. SYSTEM 1: BASELINE AUTHENTICATION (PASSWORD -> OTP) ────────────────
    def evaluate_system_1(self, scenario: AttackScenario) -> SystemEvaluationOutcome:
        """
        Baseline System 1:
        Relies strictly on Password + OTP.
        If the victim is socially engineered into providing the OTP,
        System 1 has ZERO visibility into transaction parameters and authorizes the fraud.
        """
        tx = scenario.transaction

        if scenario.is_fraud:
            if tx.victim_provides_otp:
                # Attack succeeds: victim was duped into sharing OTP
                return SystemEvaluationOutcome(
                    system_name="System 1 (Baseline 2FA)",
                    authorized=True,
                    fraud_prevented=False,
                    factors_enforced=["PASSWORD", "OTP"],
                    friction_steps=2,
                    security_verdict="COMPROMISED",
                    explanation="Fraud Succeeded: Attacker successfully deceived victim into entering/sharing OTP. System 1 lacked risk visibility to intervene.",
                )
            else:
                return SystemEvaluationOutcome(
                    system_name="System 1 (Baseline 2FA)",
                    authorized=False,
                    fraud_prevented=True,
                    factors_enforced=["PASSWORD", "OTP"],
                    friction_steps=2,
                    security_verdict="PREVENTED",
                    explanation="Victim refused to share OTP, stopping attack at factor 2.",
                )
        else:
            # Benign control
            return SystemEvaluationOutcome(
                system_name="System 1 (Baseline 2FA)",
                authorized=True,
                fraud_prevented=True,
                factors_enforced=["PASSWORD", "OTP"],
                friction_steps=2,
                security_verdict="BENIGN_AUTHORIZED",
                explanation="Legitimate transaction authorized smoothly via Password + OTP.",
            )

    # ── 2. SYSTEM 2: STATIC 3FA (PASSWORD -> OTP -> ADDITIONAL CONFIRMATION) ──
    def evaluate_system_2(self, scenario: AttackScenario) -> SystemEvaluationOutcome:
        """
        Static 3FA System 2:
        Requires Factor 3 (Additional Confirmation + PIN + Affirmation) on 100% of transactions.
        Stops fraud because victims inspect locked parameters or attacker lacks PIN,
        but imposes high friction on benign users.
        """
        tx = scenario.transaction

        if scenario.is_fraud:
            # Under social engineering, explicit parameter inspection and anti-coercion check alert the victim
            if not tx.victim_signs_affirmation or not tx.victim_knows_pin:
                return SystemEvaluationOutcome(
                    system_name="System 2 (Static 3FA)",
                    authorized=False,
                    fraud_prevented=True,
                    factors_enforced=["PASSWORD", "OTP", "ADDITIONAL_CONFIRMATION"],
                    friction_steps=3,
                    security_verdict="PREVENTED",
                    explanation="Fraud Prevented: Static 3FA mandatory parameter display and anti-coercion affirmations broke the attacker's deception.",
                )
            else:
                return SystemEvaluationOutcome(
                    system_name="System 2 (Static 3FA)",
                    authorized=True,
                    fraud_prevented=False,
                    factors_enforced=["PASSWORD", "OTP", "ADDITIONAL_CONFIRMATION"],
                    friction_steps=3,
                    security_verdict="COMPROMISED",
                    explanation="Coerced victim completed all 3 factors including offline PIN.",
                )
        else:
            # Benign control transaction
            return SystemEvaluationOutcome(
                system_name="System 2 (Static 3FA)",
                authorized=True,
                fraud_prevented=True,
                factors_enforced=["PASSWORD", "OTP", "ADDITIONAL_CONFIRMATION"],
                friction_steps=3,
                security_verdict="BENIGN_AUTHORIZED_WITH_BURDEN",
                explanation="Legitimate transaction authorized, but forced redundant 3FA confirmation on trusted routine activity.",
            )

    # ── 3. SYSTEM 3: PROPOSED ADAPTIVE AUTHENTICATION ─────────────────────────
    def evaluate_system_3(self, scenario: AttackScenario) -> SystemEvaluationOutcome:
        """
        Proposed System 3:
        AI Risk Engine continuously evaluates context:
        - Low Risk (R < 0.30): 2FA only (frictionless).
        - Medium Risk (0.30 <= R < 0.70): Contextual warning banner informs victim of fraud indicators.
        - High Risk (R >= 0.70): Step-up to Transaction-Bound 3FA (Seal + Anti-Coercion Affirmation + PIN).
        """
        tx = scenario.transaction

        tx_context = {
            "amount": tx.amount,
            "user_avg_amount": tx.user_avg_amount,
            "is_new_beneficiary": tx.is_new_beneficiary,
            "beneficiary_name": tx.beneficiary_name,
            "hour_of_day": tx.hour_of_day,
            "velocity_last_hour": tx.velocity_last_hour,
        }

        decision = self.policy_engine.evaluate_transaction(tx_context)
        tier = decision.risk_tier.value
        score = decision.risk_score

        if scenario.is_fraud:
            if tier == "HIGH":
                # High-risk step-up triggers PSD2 Art. 97 Transaction-Bound Verification
                if not tx.victim_signs_affirmation or not tx.victim_knows_pin:
                    return SystemEvaluationOutcome(
                        system_name="System 3 (Proposed Adaptive)",
                        authorized=False,
                        fraud_prevented=True,
                        risk_tier=tier,
                        risk_score=score,
                        factors_enforced=["PASSWORD", "OTP", "TRANSACTION_BINDING_3FA"],
                        friction_steps=3,
                        security_verdict="PREVENTED",
                        explanation=f"Fraud Prevented: AI flagged High Risk (R={score:.2f}). Enforced transaction-bound seal & anti-coercion confirmation.",
                    )
                else:
                    return SystemEvaluationOutcome(
                        system_name="System 3 (Proposed Adaptive)",
                        authorized=True,
                        fraud_prevented=False,
                        risk_tier=tier,
                        risk_score=score,
                        factors_enforced=["PASSWORD", "OTP", "TRANSACTION_BINDING_3FA"],
                        friction_steps=3,
                        security_verdict="COMPROMISED",
                        explanation="Victim confirmed all high-risk step-up challenges.",
                    )
            elif tier == "MEDIUM":
                # Medium risk: warning banner displayed
                if tx.victim_heeds_warning_banner:
                    return SystemEvaluationOutcome(
                        system_name="System 3 (Proposed Adaptive)",
                        authorized=False,
                        fraud_prevented=True,
                        risk_tier=tier,
                        risk_score=score,
                        factors_enforced=["PASSWORD", "OTP"],
                        friction_steps=2,
                        security_verdict="PREVENTED",
                        explanation=f"Fraud Prevented: AI displayed Contextual Scam Advisory (R={score:.2f}). Victim alerted to impersonation and cancelled.",
                    )
                else:
                    return SystemEvaluationOutcome(
                        system_name="System 3 (Proposed Adaptive)",
                        authorized=True,
                        fraud_prevented=False,
                        risk_tier=tier,
                        risk_score=score,
                        factors_enforced=["PASSWORD", "OTP"],
                        friction_steps=2,
                        security_verdict="COMPROMISED",
                        explanation="Victim overlooked warning banner and proceeded with OTP.",
                    )
            else:
                # Low risk on fraud (False Negative)
                return SystemEvaluationOutcome(
                    system_name="System 3 (Proposed Adaptive)",
                    authorized=True,
                    fraud_prevented=False,
                    risk_tier=tier,
                    risk_score=score,
                    factors_enforced=["PASSWORD", "OTP"],
                    friction_steps=2,
                    security_verdict="FALSE_NEGATIVE",
                    explanation="AI misclassified fraud as low risk; 2FA authorized transfer.",
                )
        else:
            # Benign control
            if tier == "LOW":
                return SystemEvaluationOutcome(
                    system_name="System 3 (Proposed Adaptive)",
                    authorized=True,
                    fraud_prevented=True,
                    risk_tier=tier,
                    risk_score=score,
                    factors_enforced=["PASSWORD", "OTP"],
                    friction_steps=2,
                    security_verdict="OPTIMAL_BENIGN_AUTHORIZED",
                    explanation=f"Optimal UX: Low risk (R={score:.2f}) routine transfer authorized in 2 steps with zero unnecessary friction.",
                )
            else:
                return SystemEvaluationOutcome(
                    system_name="System 3 (Proposed Adaptive)",
                    authorized=True,
                    fraud_prevented=True,
                    risk_tier=tier,
                    risk_score=score,
                    factors_enforced=["PASSWORD", "OTP"],
                    friction_steps=2 if tier == "MEDIUM" else 3,
                    security_verdict="BENIGN_STEPPED_UP",
                    explanation=f"Benign transaction triggered elevated policy (R={score:.2f}).",
                )

    def execute_scenario(self, scenario: AttackScenario) -> ScenarioExecutionReport:
        """Executes a single scenario across all three systems and compares outcomes."""
        s1 = self.evaluate_system_1(scenario)
        s2 = self.evaluate_system_2(scenario)
        s3 = self.evaluate_system_3(scenario)

        return ScenarioExecutionReport(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            category=scenario.category,
            is_fraud=scenario.is_fraud,
            severity=scenario.severity,
            system_1_baseline=s1,
            system_2_static_3fa=s2,
            system_3_adaptive=s3,
        )

    def run_all(self, catalog=None) -> List[ScenarioExecutionReport]:
        """Runs the entire scenario catalog and returns structured execution reports."""
        cat = catalog or default_catalog
        return [self.execute_scenario(s) for s in cat.all()]
