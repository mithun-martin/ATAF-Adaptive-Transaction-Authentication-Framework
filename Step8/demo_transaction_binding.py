"""
Step 8 Demo: Interactive Transaction-Bound Verification Walkthrough
===================================================================
Demonstrates:
1. Exact ATAF Page 7 High-Risk Challenge display.
2. Successful cryptographically bound authorization.
3. Live detection and rejection of Man-in-the-Middle amount tampering.
4. Live detection and rejection of destination account redirection attack.
"""

from verification_service import VerificationService
from models import HighRiskTransactionInput, ConfirmationSubmission
from crypto_engine import CryptoBindingError


def run_demo():
    service = VerificationService()

    # Exact scenario from PDF Page 7:
    # ⚠️ HIGH-RISK TRANSACTION
    # ₹85,000 -> Account XXXX4821
    # Did you personally initiate this transaction?
    tx_input = HighRiskTransactionInput(
        user_id=402,
        sender_account="9000123456",
        beneficiary_name="Vishing Mule Account",
        beneficiary_account="123456784821",
        bank_name="Axis Bank",
        ifsc_code="UTIB0000456",
        amount=85000.0,
        currency="INR",
        remark="Urgent Verification Transfer",
    )

    print("=" * 80)
    print("  ATAF -- STEP 8: TRANSACTION-BOUND VERIFICATION DEMO (CRYPTOGRAPHY & AUTH)")
    print("=" * 80)
    print("  Standard: PSD2 Dynamic Linking (Art. 97) & NIST SP 800-63B Assertion Binding\n")

    # Step 1: Issue Challenge
    print("▶ [1] Issuing High-Risk Verification Challenge...")
    challenge = service.issue_challenge(tx_input, user_pin="1234")

    print("\n" + "┌" + "─" * 78 + "┐")
    print("│  ⚠️  HIGH-RISK TRANSACTION VERIFICATION CHALLENGE (ATAF SPECIFICATION)       │")
    print("├" + "─" * 78 + "┤")
    print(f"│  Amount            : {challenge.formatted_amount}                                              │")
    print(f"│  Destination       : Account {challenge.masked_beneficiary_account} ({challenge.beneficiary_name})    │")
    print(f"│  Bank & IFSC       : {challenge.bank_name} ({challenge.ifsc_code})                            │")
    print(f"│  HMAC-SHA256 Seal  : {challenge.cryptographic_seal[:36]}...             │")
    print(f"│  Challenge Nonce   : {challenge.nonce}                               │")
    print("├" + "─" * 78 + "┤")
    print(f"│  PROMPT            : \"{challenge.prompt_primary}\"            │")
    print(f"│  [x] Affirmation 1 : {challenge.prompt_affirmation_1[:52]}...│")
    print(f"│  [x] Affirmation 2 : {challenge.prompt_affirmation_2[:52]}...│")
    print("└" + "─" * 78 + "┘\n")

    # Step 2: Valid Authorization
    print("▶ [2] User submits Valid Affirmations and 4-digit Security PIN (1234)...")
    valid_submission = ConfirmationSubmission(
        challenge_id=challenge.challenge_id,
        transaction_pin="1234",
        explicit_confirmation=True,
        anti_coercion_confirmation=True,
    )
    cert = service.verify_and_authorize(valid_submission)
    print(f"  ✓ Status                  : {cert.status}")
    print(f"  ✓ Reference ID            : {cert.transaction_reference_id}")
    print(f"  ✓ Cryptographic Seal      : {cert.cryptographic_seal[:32]}...")
    print(f"  ✓ Non-Repudiation Receipt : {cert.authorization_receipt_hash[:32]}...")
    print("  -> Result: Transfer successfully bound and approved!\n")

    # Step 3: Attack Simulation 1 - Amount Tampering (AiTM)
    print("▶ [3] Attack Simulation: Man-in-the-Middle silently alters amount to ₹95,000...")
    chal2 = service.issue_challenge(tx_input, user_pin="1234")
    try:
        service.verify_and_authorize(
            ConfirmationSubmission(
                challenge_id=chal2.challenge_id,
                transaction_pin="1234",
                explicit_confirmation=True,
                anti_coercion_confirmation=True,
            ),
            tampered_parameters={"amount": 95000.0},
        )
        print("  ❌ ERROR: Tampered amount was not caught!")
    except CryptoBindingError as e:
        print(f"  🛡️ BLOCKED BY CRYPTO ENGINE: {e}")
        print("  -> Result: Mathematical seal mismatch prevented unauthorized excess debit!\n")

    # Step 4: Attack Simulation 2 - Destination Redirection Attack
    print("▶ [4] Attack Simulation: Attacker redirects destination to a mule account...")
    chal3 = service.issue_challenge(tx_input, user_pin="1234")
    try:
        service.verify_and_authorize(
            ConfirmationSubmission(
                challenge_id=chal3.challenge_id,
                transaction_pin="1234",
                explicit_confirmation=True,
                anti_coercion_confirmation=True,
            ),
            tampered_parameters={"beneficiary_account": "999900001111"},
        )
        print("  ❌ ERROR: Account redirection was not caught!")
    except CryptoBindingError as e:
        print(f"  🛡️ BLOCKED BY CRYPTO ENGINE: {e}")
        print("  -> Result: Recipient binding mismatch prevented funds diversion!\n")

    print("=" * 80)
    print("  Step 8 verification mechanism is fully operational and cryptographically verified!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
