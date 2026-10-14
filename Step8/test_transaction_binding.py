"""
Test Suite for Step 8: Transaction-Bound Verification Mechanism
===============================================================
Verifies cryptographic parameter binding, anti-tampering protection,
explicit user affirmation checks, and replay defense.
"""

import pytest
import time
from crypto_engine import (
    TransactionCryptoEngine,
    CryptoBindingError,
    ReplayAttackError,
    ChallengeExpiredError,
)
from models import (
    HighRiskTransactionInput,
    ConfirmationSubmission,
)
from verification_service import VerificationService, mask_account


@pytest.fixture
def service():
    return VerificationService()


@pytest.fixture
def sample_high_risk_tx():
    # Matches the exact example from the ATAF project plan (PDF Page 7):
    # ₹85,000 -> Account XXXX4821
    return HighRiskTransactionInput(
        user_id=101,
        sender_account="1000000001",
        beneficiary_name="Suspicious Beneficiary",
        beneficiary_account="987654324821",
        bank_name="HDFC Bank",
        ifsc_code="HDFC0001234",
        amount=85000.0,
        currency="INR",
        remark="Urgent Settlement",
    )


# ─── 1. Core Workflow Verification ────────────────────────────────────────────

def test_challenge_issuance_matches_specification(service, sample_high_risk_tx):
    challenge = service.issue_challenge(sample_high_risk_tx, user_pin="1234")

    # Verify attributes matching PDF Page 7
    assert challenge.amount == 85000.0
    assert challenge.formatted_amount == "₹85,000.00"
    assert challenge.masked_beneficiary_account == "XXXXXXXX4821"
    assert challenge.prompt_primary == "Did you personally initiate this transaction?"
    assert len(challenge.cryptographic_seal) == 64  # SHA-256 hex
    assert len(challenge.nonce) == 32


def test_successful_authorization(service, sample_high_risk_tx):
    challenge = service.issue_challenge(sample_high_risk_tx, user_pin="1234")

    submission = ConfirmationSubmission(
        challenge_id=challenge.challenge_id,
        transaction_pin="1234",
        explicit_confirmation=True,
        anti_coercion_confirmation=True,
    )

    cert = service.verify_and_authorize(submission)
    assert cert.status == "AUTHORIZED"
    assert cert.challenge_id == challenge.challenge_id
    assert cert.amount == 85000.0
    assert cert.transaction_reference_id.startswith("TXN")
    assert len(cert.authorization_receipt_hash) == 64


# ─── 2. Tampering & Security Attack Tests ─────────────────────────────────────

def test_tampered_amount_detected(service, sample_high_risk_tx):
    challenge = service.issue_challenge(sample_high_risk_tx, user_pin="1234")

    submission = ConfirmationSubmission(
        challenge_id=challenge.challenge_id,
        transaction_pin="1234",
        explicit_confirmation=True,
        anti_coercion_confirmation=True,
    )

    # Attacker alters transfer amount from ₹85,000 to ₹95,000
    with pytest.raises(CryptoBindingError) as exc_info:
        service.verify_and_authorize(submission, tampered_parameters={"amount": 95000.0})

    assert "tampered" in str(exc_info.value).lower()


def test_tampered_beneficiary_redirection_detected(service, sample_high_risk_tx):
    challenge = service.issue_challenge(sample_high_risk_tx, user_pin="1234")

    submission = ConfirmationSubmission(
        challenge_id=challenge.challenge_id,
        transaction_pin="1234",
        explicit_confirmation=True,
        anti_coercion_confirmation=True,
    )

    # Attacker redirects funds to another account
    with pytest.raises(CryptoBindingError) as exc_info:
        service.verify_and_authorize(
            submission,
            tampered_parameters={"beneficiary_account": "999999999999"}
        )

    assert "tampered" in str(exc_info.value).lower()


def test_missing_explicit_affirmation_rejected(service, sample_high_risk_tx):
    challenge = service.issue_challenge(sample_high_risk_tx, user_pin="1234")

    submission = ConfirmationSubmission(
        challenge_id=challenge.challenge_id,
        transaction_pin="1234",
        explicit_confirmation=False,  # Unchecked!
        anti_coercion_confirmation=True,
    )

    with pytest.raises(CryptoBindingError) as exc:
        service.verify_and_authorize(submission)
    assert "mandatory" in str(exc.value).lower()


def test_incorrect_security_pin_rejected(service, sample_high_risk_tx):
    challenge = service.issue_challenge(sample_high_risk_tx, user_pin="1234")

    submission = ConfirmationSubmission(
        challenge_id=challenge.challenge_id,
        transaction_pin="9999",  # Wrong PIN
        explicit_confirmation=True,
        anti_coercion_confirmation=True,
    )

    with pytest.raises(CryptoBindingError) as exc:
        service.verify_and_authorize(submission)
    assert "invalid transaction security pin" in str(exc.value).lower()


def test_nonce_replay_attack_rejected():
    crypto = TransactionCryptoEngine()
    nonce = crypto.generate_nonce()
    timestamp = int(time.time())

    seal = crypto.compute_transaction_seal(
        challenge_id="CHAL-1",
        sender_account="111",
        beneficiary_account="222",
        amount=5000.0,
        timestamp=timestamp,
        nonce=nonce,
    )

    # First verification passes
    valid, _ = crypto.verify_transaction_seal(
        expected_seal=seal,
        challenge_id="CHAL-1",
        sender_account="111",
        beneficiary_account="222",
        amount=5000.0,
        timestamp=timestamp,
        nonce=nonce,
    )
    assert valid is True

    # Replaying same nonce must raise ReplayAttackError
    with pytest.raises(ReplayAttackError):
        crypto.verify_transaction_seal(
            expected_seal=seal,
            challenge_id="CHAL-1",
            sender_account="111",
            beneficiary_account="222",
            amount=5000.0,
            timestamp=timestamp,
            nonce=nonce,
        )


def test_challenge_expired():
    crypto = TransactionCryptoEngine()
    nonce = crypto.generate_nonce()
    old_timestamp = int(time.time()) - 400  # 400s ago (TTL is 300s)

    seal = crypto.compute_transaction_seal(
        challenge_id="CHAL-OLD",
        sender_account="111",
        beneficiary_account="222",
        amount=5000.0,
        timestamp=old_timestamp,
        nonce=nonce,
    )

    with pytest.raises(ChallengeExpiredError):
        crypto.verify_transaction_seal(
            expected_seal=seal,
            challenge_id="CHAL-OLD",
            sender_account="111",
            beneficiary_account="222",
            amount=5000.0,
            timestamp=old_timestamp,
            nonce=nonce,
            ttl_seconds=300,
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
