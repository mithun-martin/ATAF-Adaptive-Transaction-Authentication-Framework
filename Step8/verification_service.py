"""
Step 8: Transaction-Bound Verification Service
===============================================
Coordinates challenge generation, cryptographic parameter binding,
explicit affirmation validation, and tamper-resistant authorization.
"""

import time
import uuid
import random
import string
from typing import Dict, Any, Optional

from crypto_engine import (
    TransactionCryptoEngine,
    CryptoBindingError,
    ChallengeExpiredError,
    ReplayAttackError,
)
from models import (
    HighRiskTransactionInput,
    TransactionBoundChallenge,
    ConfirmationSubmission,
    AuthorizationCertificate,
)


def mask_account(account_number: str) -> str:
    """Masks all but the last 4 digits (e.g. XXXX4821)."""
    acc = str(account_number).strip()
    if len(acc) <= 4:
        return acc
    return "X" * (len(acc) - 4) + acc[-4:]


class VerificationService:
    """
    High-risk transaction authorization coordinator.
    """

    def __init__(self, crypto_engine: Optional[TransactionCryptoEngine] = None):
        self.crypto = crypto_engine or TransactionCryptoEngine()
        # Challenge storage: challenge_id -> {challenge, user_pin, status}
        self._active_challenges: Dict[str, Dict[str, Any]] = {}

    def issue_challenge(
        self,
        tx: HighRiskTransactionInput,
        user_pin: str = "1234",
    ) -> TransactionBoundChallenge:
        """
        Creates a high-risk transaction challenge bound cryptographically to exact parameters.
        """
        challenge_id = f"CHAL-{uuid.uuid4()}"
        timestamp = int(time.time())
        nonce = self.crypto.generate_nonce(16)

        seal = self.crypto.compute_transaction_seal(
            challenge_id=challenge_id,
            sender_account=tx.sender_account,
            beneficiary_account=tx.beneficiary_account,
            amount=tx.amount,
            timestamp=timestamp,
            nonce=nonce,
            currency=tx.currency,
        )

        formatted_amount = f"₹{tx.amount:,.2f}"

        challenge = TransactionBoundChallenge(
            challenge_id=challenge_id,
            timestamp=timestamp,
            nonce=nonce,
            cryptographic_seal=seal,
            ttl_seconds=300,
            amount=tx.amount,
            formatted_amount=formatted_amount,
            currency=tx.currency,
            beneficiary_name=tx.beneficiary_name,
            beneficiary_account=tx.beneficiary_account,
            masked_beneficiary_account=mask_account(tx.beneficiary_account),
            bank_name=tx.bank_name,
            ifsc_code=tx.ifsc_code,
            sender_account=tx.sender_account,
            masked_sender_account=mask_account(tx.sender_account),
        )

        # Store internal verification context
        self._active_challenges[challenge_id] = {
            "challenge": challenge,
            "raw_input": tx,
            "expected_pin": user_pin,
            "status": "PENDING",
            "created_at": timestamp,
        }

        return challenge

    def verify_and_authorize(
        self,
        submission: ConfirmationSubmission,
        tampered_parameters: Optional[Dict[str, Any]] = None,
    ) -> AuthorizationCertificate:
        """
        Validates the user's explicit affirmations, PIN, and cryptographic binding.
        """
        record = self._active_challenges.get(submission.challenge_id)
        if not record:
            raise CryptoBindingError("Invalid or nonexistent transaction challenge ID.")

        if record["status"] != "PENDING":
            raise CryptoBindingError(f"Challenge is no longer active (status: {record['status']}).")

        challenge: TransactionBoundChallenge = record["challenge"]
        tx: HighRiskTransactionInput = record["raw_input"]

        # 1. Affirmation Checks
        if not submission.explicit_confirmation:
            raise CryptoBindingError("Explicit confirmation that you personally initiated this transaction is mandatory.")

        if not submission.anti_coercion_confirmation:
            raise CryptoBindingError("Confirmation that you are not under third-party coercion is mandatory.")

        # 2. Knowledge Factor (PIN) Check
        if submission.transaction_pin != record["expected_pin"]:
            raise CryptoBindingError("Authentication failed: Invalid Transaction Security PIN.")

        # 3. Cryptographic Binding & Tampering Check
        # If testing tampering simulation, use altered parameters:
        eval_amount = tx.amount
        eval_beneficiary = tx.beneficiary_account
        if tampered_parameters:
            eval_amount = tampered_parameters.get("amount", eval_amount)
            eval_beneficiary = tampered_parameters.get("beneficiary_account", eval_beneficiary)

        valid, error_msg = self.crypto.verify_transaction_seal(
            expected_seal=challenge.cryptographic_seal,
            challenge_id=challenge.challenge_id,
            sender_account=tx.sender_account,
            beneficiary_account=eval_beneficiary,
            amount=eval_amount,
            timestamp=challenge.timestamp,
            nonce=challenge.nonce,
            ttl_seconds=challenge.ttl_seconds,
            currency=tx.currency,
        )

        if not valid:
            record["status"] = "TAMPER_DETECTED"
            raise CryptoBindingError(error_msg or "Transaction binding seal verification failed.")

        # 4. Generate Non-Repudiation Certificate
        now = int(time.time())
        receipt_hash = self.crypto.sign_authorization_receipt(
            challenge_id=challenge.challenge_id,
            seal=challenge.cryptographic_seal,
            user_id=tx.user_id,
            authorized_at=now,
        )

        chars = string.ascii_uppercase + string.digits
        ref_id = "TXN" + "".join(random.choices(chars, k=10))

        record["status"] = "AUTHORIZED"

        return AuthorizationCertificate(
            status="AUTHORIZED",
            challenge_id=challenge.challenge_id,
            transaction_reference_id=ref_id,
            amount=tx.amount,
            beneficiary_account=mask_account(tx.beneficiary_account),
            cryptographic_seal=challenge.cryptographic_seal,
            authorization_receipt_hash=receipt_hash,
            authorized_at=now,
        )
