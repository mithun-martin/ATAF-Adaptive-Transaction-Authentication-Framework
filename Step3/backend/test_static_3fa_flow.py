"""
Test suite for Step 3: Static 3FA (Password -> OTP -> Additional Confirmation -> Transaction)
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_static_3fa_flow():
    # 1. Register User (sets default PIN 1234)
    reg_res = client.post("/auth/register", json={
        "name": "Aditya 3FA Test",
        "email": "aditya.3fa@example.com",
        "phone": "+919876543211",
        "password": "SecurePassword123!",
        "transaction_pin": "1234"
    })
    assert reg_res.status_code == 201, reg_res.text

    # 2. Login
    login_res = client.post("/auth/login", json={
        "email": "aditya.3fa@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    login_otp = login_res.json()["otp_display"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify Login OTP
    otp_res = client.post("/auth/otp/verify", headers=headers, json={
        "code": login_otp,
        "purpose": "LOGIN"
    })
    assert otp_res.status_code == 200

    # 3. Add Beneficiary
    ben_res = client.post("/beneficiaries", headers=headers, json={
        "name": "Alice Smith",
        "account_number": "112233445566",
        "ifsc_code": "ICIC0005678",
        "bank_name": "ICICI Bank"
    })
    assert ben_res.status_code == 201
    ben_id = ben_res.json()["id"]

    # 4. Direct Transfer Blocked
    direct_res = client.post("/transactions", headers=headers, json={
        "beneficiary_id": ben_id,
        "amount": 10000.0
    })
    assert direct_res.status_code == 400

    # 5. Factor 1: Wrong Password -> 401
    wrong_pwd = client.post("/transactions/initiate", headers=headers, json={
        "beneficiary_id": ben_id,
        "amount": 10000.0,
        "password": "WrongPassword!"
    })
    assert wrong_pwd.status_code == 401

    # 6. Factor 1: Correct Password -> Initiates challenge
    init_res = client.post("/transactions/initiate", headers=headers, json={
        "beneficiary_id": ben_id,
        "amount": 10000.0,
        "remark": "Project Equipment",
        "password": "SecurePassword123!"
    })
    assert init_res.status_code == 200, init_res.text
    challenge = init_res.json()
    challenge_id = challenge["challenge_id"]
    tx_otp = challenge["otp_display"]
    assert challenge["stage"] == "AWAITING_OTP"

    # 7. Factor 2: Wrong OTP -> 400
    wrong_otp = client.post("/transactions/verify-otp", headers=headers, json={
        "challenge_id": challenge_id,
        "otp_code": "999999"
    })
    assert wrong_otp.status_code == 400

    # 8. Factor 2: Correct OTP -> Advances to AWAITING_ADDITIONAL_CONFIRMATION
    stage2_res = client.post("/transactions/verify-otp", headers=headers, json={
        "challenge_id": challenge_id,
        "otp_code": tx_otp
    })
    assert stage2_res.status_code == 200, stage2_res.text
    stage2_data = stage2_res.json()
    assert stage2_data["stage"] == "AWAITING_ADDITIONAL_CONFIRMATION"
    assert "cryptographic_seal" in stage2_data
    seal = stage2_data["cryptographic_seal"]
    assert len(seal) == 64  # SHA-256 hex string

    # 9. Factor 3: Missing Confirmation Checkboxes -> 400
    no_check = client.post("/transactions/confirm-additional-verification", headers=headers, json={
        "challenge_id": challenge_id,
        "transaction_pin": "1234",
        "explicit_confirmation": False,
        "anti_coercion_confirmation": True
    })
    assert no_check.status_code == 400

    # 10. Factor 3: Wrong Security PIN -> 401
    wrong_pin = client.post("/transactions/confirm-additional-verification", headers=headers, json={
        "challenge_id": challenge_id,
        "transaction_pin": "9999",
        "explicit_confirmation": True,
        "anti_coercion_confirmation": True
    })
    assert wrong_pin.status_code == 401

    # 11. Factor 3: Correct PIN & Affirmations -> Finalizes Transaction!
    confirm_res = client.post("/transactions/confirm-additional-verification", headers=headers, json={
        "challenge_id": challenge_id,
        "transaction_pin": "1234",
        "explicit_confirmation": True,
        "anti_coercion_confirmation": True
    })
    assert confirm_res.status_code == 201, confirm_res.text
    tx_out = confirm_res.json()
    assert tx_out["status"] == "COMPLETED"
    assert tx_out["auth_mode"] == "STATIC_3FA"
    assert tx_out["auth_factors"] == "PASSWORD,OTP,ADDITIONAL_CONFIRMATION"
    assert tx_out["cryptographic_seal"] == seal

    # 12. Check Transaction History
    hist_res = client.get("/transactions", headers=headers)
    assert hist_res.status_code == 200
    txs = hist_res.json()
    assert len(txs) == 1
    assert txs[0]["auth_mode"] == "STATIC_3FA"
    assert txs[0]["cryptographic_seal"] == seal

    # 13. Test PIN update endpoint
    update_pin_res = client.post("/account/pin", headers=headers, json={
        "current_password": "SecurePassword123!",
        "new_pin": "5678"
    })
    assert update_pin_res.status_code == 200

    print("All Step 3 Static 3FA tests passed successfully!")

if __name__ == "__main__":
    test_static_3fa_flow()
