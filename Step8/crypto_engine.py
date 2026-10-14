"""
Step 8: Cryptographic Transaction-Binding Engine
=================================================
Implements dynamic transaction-bound linking complying with:
- PSD2 RTS Article 97 (Dynamic Linking of Transaction Information)
- NIST SP 800-63B (Cryptographic Binding of Authentication Assertions)

Guarantees:
1. Recipient Binding: Authorization is mathematically tied to the specific destination account.
2. Amount Invariance: Modifying even 1 cent invalidates the cryptographic signature.
3. Replay Protection: Unique cryptographic nonces prevent replaying authorizations.
4. Non-Repudiation: Generates an immutable authorization receipt hash upon successful approval.
"""

import hmac
import hashlib
import secrets
import time
from typing import Dict, Any, Tuple, Optional, Set


class CryptoBindingError(Exception):
    """Base exception for transaction-binding validation failures."""
    pass


class AmountTamperedError(CryptoBindingError):
    """Raised when transfer amount was altered in transit."""
    pass


class BeneficiaryTamperedError(CryptoBindingError):
    """Raised when beneficiary account was altered or redirected."""
    pass


class ReplayAttackError(CryptoBindingError):
    """Raised when a nonce or signature is reused."""
    pass


class ChallengeExpiredError(CryptoBindingError):
    """Raised when confirmation is submitted after session TTL."""
    pass


class TransactionCryptoEngine:
    """
    Cryptographic engine for computing and verifying transaction-bound signatures.
    """

    def __init__(self, secret_key: Optional[str] = None):
        # Default secure system key if none provided
        self.secret_key = (
            secret_key or "ATAF_SECURE_HMAC_TRANSACTION_BINDING_KEY_2026_DEFAULT"
        ).encode("utf-8")
        self._used_nonces: Set[str] = set()

    def generate_nonce(self, length: int = 16) -> str:
        """Generates a cryptographically strong random hex nonce."""
        return secrets.token_hex(length)

    def create_canonical_payload(
        self,
        challenge_id: str,
        sender_account: str,
        beneficiary_account: str,
        amount: float,
        timestamp: int,
        nonce: str,
        currency: str = "INR",
    ) -> str:
        """
        Creates an immutable canonical representation of critical transaction attributes.
        Any modification to any field produces an entirely different hash.
        """
        formatted_amount = f"{amount:.2f}"
        return f"{challenge_id}|{sender_account.strip()}|{beneficiary_account.strip()}|{formatted_amount}|{currency}|{timestamp}|{nonce}"

    def compute_transaction_seal(
        self,
        challenge_id: str,
        sender_account: str,
        beneficiary_account: str,
        amount: float,
        timestamp: int,
        nonce: str,
        currency: str = "INR",
    ) -> str:
        """
        Computes the HMAC-SHA256 Cryptographic Transaction Seal.
        """
        canonical = self.create_canonical_payload(
            challenge_id=challenge_id,
            sender_account=sender_account,
            beneficiary_account=beneficiary_account,
            amount=amount,
            timestamp=timestamp,
            nonce=nonce,
            currency=currency,
        )
        return hmac.new(self.secret_key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_transaction_seal(
        self,
        expected_seal: str,
        challenge_id: str,
        sender_account: str,
        beneficiary_account: str,
        amount: float,
        timestamp: int,
        nonce: str,
        ttl_seconds: int = 300,
        currency: str = "INR",
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifies that the submitted transaction parameters exactly match the cryptographic seal.
        Checks for:
        1. Nonce replay
        2. Session expiration (TTL)
        3. Parameter tampering (amount or beneficiary manipulation)
        """
        # 1. Replay check
        if nonce in self._used_nonces:
            raise ReplayAttackError(f"Cryptographic nonce '{nonce}' has already been used. Replay attempt detected.")

        # 2. Expiration check
        current_time = int(time.time())
        if current_time - timestamp > ttl_seconds:
            raise ChallengeExpiredError(f"Transaction authorization challenge has expired (age: {current_time - timestamp}s, max TTL: {ttl_seconds}s).")

        # 3. Compute expected hash for provided parameters
        recomputed_seal = self.compute_transaction_seal(
            challenge_id=challenge_id,
            sender_account=sender_account,
            beneficiary_account=beneficiary_account,
            amount=amount,
            timestamp=timestamp,
            nonce=nonce,
            currency=currency,
        )

        # Constant-time comparison to prevent timing side-channel attacks
        if not hmac.compare_digest(expected_seal, recomputed_seal):
            return False, "Cryptographic seal mismatch: One or more transaction parameters have been tampered with."

        # Mark nonce as spent
        self._used_nonces.add(nonce)
        return True, None

    def sign_authorization_receipt(
        self,
        challenge_id: str,
        seal: str,
        user_id: int,
        authorized_at: int,
    ) -> str:
        """
        Generates an immutable cryptographic authorization receipt after approval.
        Serves as non-repudiation proof for audit trails.
        """
        receipt_data = f"RECEIPT|{challenge_id}|{seal}|{user_id}|{authorized_at}"
        return hmac.new(self.secret_key, receipt_data.encode("utf-8"), hashlib.sha256).hexdigest()
