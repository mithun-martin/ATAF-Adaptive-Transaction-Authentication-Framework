"""
Step 10: Test Suite for Social-Engineering Attack Scenarios
============================================================
Validates scenario catalog completeness, threat model classifications,
and simulation engine evaluation across all 3 systems.
"""

import pytest
from scenarios.catalog import default_catalog
from scenarios.models import AttackCategory, SeverityLevel
from attack_simulator import AttackSimulator


@pytest.fixture
def simulator():
    return AttackSimulator()


def test_catalog_integrity():
    """Validates that the scenario catalog is properly loaded and formatted."""
    scenarios = default_catalog.all()
    assert len(scenarios) == 8, f"Expected 8 scenarios, found {len(scenarios)}"

    fraud_scenarios = default_catalog.get_fraud_scenarios()
    control_scenarios = default_catalog.get_control_scenarios()
    assert len(fraud_scenarios) == 6
    assert len(control_scenarios) == 2

    # Verify all categories are covered
    categories = {s.category for s in scenarios}
    assert AttackCategory.OTP_HARVESTING in categories
    assert AttackCategory.BENEFICIARY_MULE in categories
    assert AttackCategory.REMOTE_ACCESS_TAKEOVER in categories
    assert AttackCategory.OFF_HOURS_COERCION in categories
    assert AttackCategory.VOLUME_ANOMALY in categories
    assert AttackCategory.COMPOUND_SUSPICIOUS in categories
    assert AttackCategory.BENIGN_CONTROL in categories


def test_scenario_lookup_and_filtering():
    """Tests scenario query methods."""
    scn = default_catalog.get("SCN-01-OTP-VISHING")
    assert scn is not None
    assert scn.name == "Classic OTP Voice Phishing (Bank Impersonation)"
    assert scn.is_fraud is True

    mule_scenarios = default_catalog.filter_by_category(AttackCategory.BENEFICIARY_MULE)
    assert len(mule_scenarios) >= 1
    assert mule_scenarios[0].id == "SCN-02-NEW-BENEFICIARY-MULE"


def test_system_1_baseline_vulnerability(simulator):
    """
    Validates that System 1 (Password + OTP) is completely compromised by
    social-engineering attacks where victims are deceived into providing OTPs.
    """
    fraud_scenarios = default_catalog.get_fraud_scenarios()
    for scn in fraud_scenarios:
        res = simulator.evaluate_system_1(scn)
        assert res.authorized is True, f"System 1 should have authorized {scn.id} due to victim OTP entry"
        assert res.fraud_prevented is False
        assert res.security_verdict == "COMPROMISED"
        assert res.friction_steps == 2


def test_system_2_static_3fa_defense_and_burden(simulator):
    """
    Validates that System 2 (Static 3FA) prevents fraud via parameter display and PIN,
    but imposes 3-factor friction on 100% of benign routine transfers.
    """
    # 1. Attacks are prevented
    for scn in default_catalog.get_fraud_scenarios():
        res = simulator.evaluate_system_2(scn)
        assert res.fraud_prevented is True
        assert res.security_verdict == "PREVENTED"
        assert res.friction_steps == 3

    # 2. Benign transfers bear high friction burden
    for scn in default_catalog.get_control_scenarios():
        res = simulator.evaluate_system_2(scn)
        assert res.authorized is True
        assert res.friction_steps == 3
        assert res.security_verdict == "BENIGN_AUTHORIZED_WITH_BURDEN"


def test_system_3_adaptive_optimization(simulator):
    """
    Validates that System 3:
    1. Prevents 100% of social-engineering attacks.
    2. Minimizes friction to 2 steps on benign routine transfers.
    """
    # 1. Fraud Prevention
    for scn in default_catalog.get_fraud_scenarios():
        res = simulator.evaluate_system_3(scn)
        assert res.fraud_prevented is True, f"System 3 failed to prevent {scn.id}"
        assert res.security_verdict == "PREVENTED"
        assert res.risk_tier in ["MEDIUM", "HIGH"]

    # 2. Benign Usability (Zero extra friction)
    for scn in default_catalog.get_control_scenarios():
        res = simulator.evaluate_system_3(scn)
        assert res.authorized is True
        assert res.friction_steps == 2, f"System 3 imposed unnecessary friction on {scn.id}"
        assert res.security_verdict == "OPTIMAL_BENIGN_AUTHORIZED"
        assert res.risk_tier == "LOW"
        assert res.risk_score < 0.30
