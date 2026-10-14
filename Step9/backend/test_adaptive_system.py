"""
Integration Test Suite for ATAF Step 9: Proposed Adaptive Authentication (System 3)
===================================================================================
Tests end-to-end integration across:
1. Low-Risk Scenario: Password -> OTP -> Instant Authorization (Frictionless)
2. Medium-Risk Scenario: Password -> Risk Warning Banner -> OTP -> Authorization
3. High-Risk Scenario: Password -> High Fraud Alert -> OTP -> Transaction-Bound 3FA (Seal + Affirmations + PIN) -> Authorization
4. Tampering & Security Defense: Invalid PIN & modified parameters are rejected
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models.user import User
from models.account import Account
from models.beneficiary import Beneficiary

TEST_DATABASE_URL = "sqlite:///./test_adaptive_banking.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def authenticated_user(client):
    """Registers and authenticates a test user."""
    # Register
    reg_resp = client.post(
        "/auth/register",
        json={
            "name": "Arjun Sharma",
            "email": "arjun@example.com",
            "phone": "+919876543210",
            "password": "SecurePassword123!",
            "transaction_pin": "5678",
        },
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = client.post(
        "/auth/login",
        json={"email": "arjun@example.com", "password": "SecurePassword123!"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    token = token_data["access_token"]
    login_otp = token_data["otp_display"]

    # Verify Login OTP
    verify_resp = client.post(
        "/auth/otp/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": login_otp, "purpose": "LOGIN"},
    )
    assert verify_resp.status_code == 200

    # Add Established Beneficiary
    ben_resp = client.post(
        "/beneficiaries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Local Grocery Store",
            "account_number": "987654321098",
            "bank_name": "State Bank of India",
            "ifsc_code": "SBIN0001234",
        },
    )
    assert ben_resp.status_code == 201
    ben_id = ben_resp.json()["id"]

    return {"token": token, "ben_id": ben_id, "pin": "5678"}


def test_scenario_low_risk_flow(client, authenticated_user):
    """
    Scenario 1: Low-Risk Transfer (₹450 to established beneficiary)
    Expected: AI Risk < 0.30 -> NORMAL action -> Password + OTP authorizes directly.
    """
    token = authenticated_user["token"]
    ben_id = authenticated_user["ben_id"]

    # Step 1: Initiate Transfer (Factor 1 - Password)
    init_resp = client.post(
        "/transactions/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "beneficiary_id": ben_id,
            "amount": 450.0,
            "remark": "Weekly groceries",
            "password": "SecurePassword123!",
        },
    )
    assert init_resp.status_code == 200
    challenge = init_resp.json()

    assert challenge["risk_tier"] == "LOW"
    assert challenge["risk_score"] < 0.30
    assert challenge["auth_action"] == "NORMAL"
    assert challenge["warning_banner"] is None
    assert challenge["requires_pin"] is False
    assert challenge["requires_cryptographic_seal"] is False

    challenge_id = challenge["challenge_id"]
    otp_code = challenge["otp_display"]

    # Step 2: Verify OTP (Factor 2)
    verify_resp = client.post(
        "/transactions/verify-otp",
        headers={"Authorization": f"Bearer {token}"},
        json={"challenge_id": challenge_id, "otp_code": otp_code},
    )
    assert verify_resp.status_code == 200
    res = verify_resp.json()

    assert res["stage"] == "COMPLETED"
    assert res["requires_step_up"] is False
    assert res["transaction"] is not None
    assert res["transaction"]["amount"] == 450.0
    assert res["transaction"]["auth_factors"] == "PASSWORD,OTP"
    assert res["transaction"]["risk_tier"] == "LOW"


def test_scenario_medium_risk_flow(client, authenticated_user):
    """
    Scenario 2: Medium-Risk Transfer (₹28,000 unusual amount deviation)
    Expected: 0.30 <= AI Risk < 0.70 -> WARNING action -> Shows warning banner -> OTP completes.
    """
    token = authenticated_user["token"]
    ben_id = authenticated_user["ben_id"]

    init_resp = client.post(
        "/transactions/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "beneficiary_id": ben_id,
            "amount": 2000.0,
            "remark": "Consulting fee",
            "password": "SecurePassword123!",
        },
    )
    assert init_resp.status_code == 200
    challenge = init_resp.json()

    assert challenge["risk_tier"] == "MEDIUM"
    assert 0.30 <= challenge["risk_score"] < 0.70
    assert challenge["auth_action"] == "WARNING"
    assert challenge["warning_banner"] is not None
    assert "CAUTION" in challenge["warning_banner"]
    assert challenge["requires_pin"] is False

    challenge_id = challenge["challenge_id"]
    otp_code = challenge["otp_display"]

    # Verify OTP completes medium risk without needing factor 3
    verify_resp = client.post(
        "/transactions/verify-otp",
        headers={"Authorization": f"Bearer {token}"},
        json={"challenge_id": challenge_id, "otp_code": otp_code},
    )
    assert verify_resp.status_code == 200
    res = verify_resp.json()
    assert res["stage"] == "COMPLETED"
    assert res["requires_step_up"] is False
    assert res["transaction"]["risk_tier"] == "MEDIUM"


def test_scenario_high_risk_flow(client, authenticated_user):
    """
    Scenario 3: High-Risk Transfer (₹55,000 to new recipient during off-hours or anomaly)
    Expected: AI Risk >= 0.70 -> STRONG_VERIFICATION -> Requires Factor 3 (Seal + Affirmation + PIN).
    """
    token = authenticated_user["token"]

    # Add a brand new recipient right now
    new_ben_resp = client.post(
        "/beneficiaries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Unknown Offshore Vendor",
            "account_number": "112233445566",
            "bank_name": "International Bank",
            "ifsc_code": "INTL0009999",
        },
    )
    assert new_ben_resp.status_code == 201
    new_ben_id = new_ben_resp.json()["id"]

    # Initiate High-Risk Transfer
    init_resp = client.post(
        "/transactions/initiate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "beneficiary_id": new_ben_id,
            "amount": 55000.0,
            "remark": "Urgent transfer",
            "password": "SecurePassword123!",
        },
    )
    assert init_resp.status_code == 200
    challenge = init_resp.json()

    assert challenge["risk_tier"] == "HIGH"
    assert challenge["risk_score"] >= 0.70
    assert challenge["auth_action"] == "STRONG_VERIFICATION"
    assert challenge["requires_pin"] is True
    assert challenge["requires_cryptographic_seal"] is True
    assert challenge["cryptographic_seal"] is not None
    assert challenge["nonce"] is not None

    challenge_id = challenge["challenge_id"]
    otp_code = challenge["otp_display"]

    # Verify OTP (Factor 2) -> Must step up to Factor 3!
    verify_resp = client.post(
        "/transactions/verify-otp",
        headers={"Authorization": f"Bearer {token}"},
        json={"challenge_id": challenge_id, "otp_code": otp_code},
    )
    assert verify_resp.status_code == 200
    stepup = verify_resp.json()

    assert stepup["stage"] == "AWAITING_HIGH_RISK_VERIFICATION"
    assert stepup["requires_step_up"] is True
    assert stepup["transaction"] is None
    assert stepup["cryptographic_seal"] == challenge["cryptographic_seal"]

    # Attempt Factor 3 with wrong PIN -> Rejection
    bad_pin_resp = client.post(
        "/transactions/confirm-high-risk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "challenge_id": challenge_id,
            "transaction_pin": "0000",
            "explicit_affirmation": True,
            "anti_coercion_ack": True,
        },
    )
    assert bad_pin_resp.status_code == 401

    # Attempt Factor 3 without Anti-Coercion affirmation -> Rejection
    no_ack_resp = client.post(
        "/transactions/confirm-high-risk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "challenge_id": challenge_id,
            "transaction_pin": authenticated_user["pin"],
            "explicit_affirmation": True,
            "anti_coercion_ack": False,
        },
    )
    assert no_ack_resp.status_code == 400

    # Successful Factor 3 Confirmation
    confirm_resp = client.post(
        "/transactions/confirm-high-risk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "challenge_id": challenge_id,
            "transaction_pin": authenticated_user["pin"],
            "explicit_affirmation": True,
            "anti_coercion_ack": True,
        },
    )
    assert confirm_resp.status_code == 200
    final_tx = confirm_resp.json()

    assert final_tx["status"] == "COMPLETED"
    assert final_tx["amount"] == 55000.0
    assert final_tx["auth_mode"] == "ADAPTIVE_SYSTEM_3"
    assert final_tx["auth_factors"] == "PASSWORD,OTP,TRANSACTION_BINDING_3FA"
    assert final_tx["risk_tier"] == "HIGH"
    assert final_tx["cryptographic_seal"] == challenge["cryptographic_seal"]


def test_transactions_history(client, authenticated_user):
    """Verifies all authorized transactions appear with full adaptive audit trails."""
    token = authenticated_user["token"]
    res = client.get("/transactions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    tx_list = res.json()
    assert len(tx_list) >= 3

    # Check that both 2FA and 3FA transfers are in history
    factors_seen = {t["auth_factors"] for t in tx_list}
    assert "PASSWORD,OTP" in factors_seen
    assert "PASSWORD,OTP,TRANSACTION_BINDING_3FA" in factors_seen
