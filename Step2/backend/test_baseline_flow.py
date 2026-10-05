"""
Test suite for Step 2: Baseline Authentication (Password -> OTP -> Transaction)
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_baseline_flow():
    # 1. Register User
    reg_res = client.post("/auth/register", json={
        "name": "Aditya Test",
        "email": "aditya.test@example.com",
        "phone": "+919876543210",
        "password": "SecurePassword123!"
    })
    assert reg_res.status_code == 201, reg_res.text
    user_data = reg_res.json()

    # 2. Login
    login_res = client.post("/auth/login", json={
        "email": "aditya.test@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200, login_res.text
    login_data = login_res.json()
    token = login_data["access_token"]
    login_otp = login_data["otp_display"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify Login OTP
    otp_res = client.post("/auth/otp/verify", headers=headers, json={
        "code": login_otp,
        "purpose": "LOGIN"
    })
    assert otp_res.status_code == 200, otp_res.text

    # 3. Add Beneficiary
    ben_res = client.post("/beneficiaries", headers=headers, json={
        "name": "John Doe",
        "account_number": "987654321012",
        "ifsc_code": "HDFC0001234",
        "bank_name": "HDFC Bank",
        "nickname": "John"
    })
    assert ben_res.status_code == 201, ben_res.text
    ben_id = ben_res.json()["id"]

    # 4. Attempt Legacy Direct Transfer -> Should Fail (Blocked in Step 2)
    direct_res = client.post("/transactions", headers=headers, json={
        "beneficiary_id": ben_id,
        "amount": 2500.0,
        "remark": "Test"
    })
    assert direct_res.status_code == 400, "Direct transfer should be blocked in Step 2"

    # 5. Factor 1: Initiate Transfer with WRONG Password -> Should Fail
    wrong_pwd_res = client.post("/transactions/initiate", headers=headers, json={
        "beneficiary_id": ben_id,
        "amount": 2500.0,
        "remark": "Tuition Fees",
        "password": "WrongPassword!"
    })
    assert wrong_pwd_res.status_code == 401, "Wrong password should be rejected"

    # 6. Factor 1: Initiate Transfer with CORRECT Password -> Should Succeed and issue Challenge + OTP
    init_res = client.post("/transactions/initiate", headers=headers, json={
        "beneficiary_id": ben_id,
        "amount": 2500.0,
        "remark": "Tuition Fees",
        "password": "SecurePassword123!"
    })
    assert init_res.status_code == 200, init_res.text
    challenge = init_res.json()
    challenge_id = challenge["challenge_id"]
    tx_otp = challenge["otp_display"]
    assert challenge_id is not None
    assert len(tx_otp) == 6

    # 7. Factor 2: Verify with WRONG OTP -> Should Fail
    wrong_otp_res = client.post("/transactions/verify-otp", headers=headers, json={
        "challenge_id": challenge_id,
        "otp_code": "000000"
    })
    assert wrong_otp_res.status_code == 400, "Wrong OTP should be rejected"

    # 8. Factor 2: Verify with CORRECT OTP -> Should Finalize Transaction
    verify_res = client.post("/transactions/verify-otp", headers=headers, json={
        "challenge_id": challenge_id,
        "otp_code": tx_otp
    })
    assert verify_res.status_code == 201, verify_res.text
    tx_out = verify_res.json()
    assert tx_out["status"] == "COMPLETED"
    assert tx_out["amount"] == 2500.0
    assert tx_out["auth_mode"] == "BASELINE"
    assert tx_out["auth_factors"] == "PASSWORD,OTP"
    assert tx_out["reference_id"].startswith("TXN")

    # 9. Verify Transaction appears in History
    hist_res = client.get("/transactions", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 1
    assert history[0]["reference_id"] == tx_out["reference_id"]
    assert history[0]["auth_mode"] == "BASELINE"

    print("All Step 2 Baseline 2FA tests passed successfully!")

if __name__ == "__main__":
    test_baseline_flow()
