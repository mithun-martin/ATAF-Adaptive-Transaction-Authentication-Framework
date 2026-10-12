"""
Step 7 Demo: Interactive Adaptive Security Policy Evaluation
=============================================================
Runs 5 realistic banking transaction scenarios through the Adaptive
Security Policy Engine and displays the security enforcement matrix.
"""

from policy_engine import AdaptivePolicyEngine
from threshold_config import RiskTier, AuthAction


def run_demo():
    engine = AdaptivePolicyEngine()

    scenarios = [
        {
            "name": "Scenario 1: Routine Grocery Transfer",
            "description": "User transferring ₹650 to an established local vendor at 2 PM.",
            "tx": {
                "amount": 650.0,
                "beneficiary_name": "Fresh Market",
                "user_avg_amount": 4500.0,
                "is_new_beneficiary": False,
                "hour_of_day": 14,
                "velocity_last_hour": 0,
            },
        },
        {
            "name": "Scenario 2: Moderate Rent Payment",
            "description": "User transferring ₹15,000 to an existing landlord contact during daytime.",
            "tx": {
                "amount": 15000.0,
                "beneficiary_name": "Landlord Sharma",
                "user_avg_amount": 6000.0,
                "is_new_beneficiary": False,
                "hour_of_day": 11,
                "velocity_last_hour": 0,
            },
        },
        {
            "name": "Scenario 3: Unfamiliar New Recipient",
            "description": "User transferring ₹18,000 to a newly added contact within 1 hour of addition.",
            "tx": {
                "amount": 18000.0,
                "beneficiary_name": "Alex Tech Services",
                "user_avg_amount": 5000.0,
                "is_new_beneficiary": True,
                "hour_of_day": 19,
                "velocity_last_hour": 1,
            },
        },
        {
            "name": "Scenario 4: High-Velocity Spike",
            "description": "Third rapid transfer within 45 minutes to different beneficiaries.",
            "tx": {
                "amount": 32000.0,
                "beneficiary_name": "Online Payment Desk",
                "user_avg_amount": 4000.0,
                "is_new_beneficiary": True,
                "hour_of_day": 22,
                "velocity_last_hour": 3,
            },
        },
        {
            "name": "Scenario 5: Urgent Social Engineering Scam (Vishing)",
            "description": "Victim pressured by a fake support caller to send ₹85,000 to a new account at 3:15 AM.",
            "tx": {
                "amount": 85000.0,
                "beneficiary_name": "Fast Settlement Corp",
                "user_avg_amount": 3500.0,
                "is_new_beneficiary": True,
                "hour_of_day": 3,
                "velocity_last_hour": 2,
            },
        },
    ]

    print("=" * 80)
    print("  ATAF -- STEP 7: ADAPTIVE SECURITY POLICY EVALUATION DEMO")
    print("=" * 80)
    print("  Decision Matrix: LOW (<0.30) -> Normal | MEDIUM (0.30-0.70) -> Warning | HIGH (>=0.70) -> Strong 3FA\n")

    for s in scenarios:
        print(f"▶ {s['name']}")
        print(f"  Context: {s['description']}")
        decision = engine.evaluate_transaction(s["tx"])

        # Color badges
        if decision.risk_tier == RiskTier.LOW:
            tier_badge = "🟢 LOW RISK"
            action_badge = "Normal Authentication (Password + OTP)"
        elif decision.risk_tier == RiskTier.MEDIUM:
            tier_badge = "🟡 MEDIUM RISK"
            action_badge = "Advisory Warning Banner + OTP"
        else:
            tier_badge = "🔴 HIGH RISK"
            action_badge = "Strong Verification (HMAC-SHA256 Seal + Security PIN)"

        print(f"  Risk Probability : {decision.risk_score:.4f}  [{tier_badge}]")
        print(f"  Policy Directive : {action_badge}")
        print(f"  Enforced Factors : {' -> '.join(decision.required_factors)}")
        if decision.risk_reasons:
            print("  Triggered Flags  :")
            for r in decision.risk_reasons:
                print(f"    • {r}")
        if decision.warning_banner:
            print(f"  Displayed Banner : \"{decision.warning_banner[:110]}...\"")
        print("-" * 80)


if __name__ == "__main__":
    run_demo()
