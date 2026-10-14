"""
Step 8: Models & Data Contracts for Transaction-Bound Verification
===================================================================
Defines schemas for high-risk verification challenges, explicit user
affirmations, and cryptographic authorization certificates.
"""

from typing import Optional
from pydantic import BaseModel, Field


class HighRiskTransactionInput(BaseModel):
    """Input payload for a high-risk transfer requiring transaction-bound verification."""
    user_id: int
    sender_account: str
    beneficiary_name: str
    beneficiary_account: str
    bank_name: str
    ifsc_code: str
    amount: float = Field(gt=0, description="Exact transfer amount")
    currency: str = "INR"
    remark: Optional[str] = None


class TransactionBoundChallenge(BaseModel):
    """
    Challenge payload displayed in the UI matching PDF Page 7 specification:
    ⚠️ HIGH-RISK TRANSACTION
    ₹85,000 -> Account XXXX4821
    Did you personally initiate this transaction?
    """
    challenge_id: str
    timestamp: int
    nonce: str
    cryptographic_seal: str
    ttl_seconds: int = 300

    # Display attributes (exact transaction parameters)
    amount: float
    formatted_amount: str
    currency: str
    beneficiary_name: str
    beneficiary_account: str
    masked_beneficiary_account: str
    bank_name: str
    ifsc_code: str
    sender_account: str
    masked_sender_account: str

    # Explicit Affirmation Prompts
    prompt_primary: str = "Did you personally initiate this transaction?"
    prompt_affirmation_1: str = "I verify that I personally initiated this transfer to the exact recipient and account number shown above."
    prompt_affirmation_2: str = "I confirm that I am not following instructions from an unknown phone caller, remote screen share, or urgent refund claim."


class ConfirmationSubmission(BaseModel):
    """User submission to authorize the high-risk transaction."""
    challenge_id: str
    transaction_pin: str = Field(min_length=4, max_length=6, description="4-digit Transaction Security PIN")
    explicit_confirmation: bool = Field(description="Must be True: affirms personal initiation")
    anti_coercion_confirmation: bool = Field(description="Must be True: affirms absence of third-party coercion")


class AuthorizationCertificate(BaseModel):
    """
    Cryptographic certificate emitted upon successful verification.
    Guarantees non-repudiation and transaction binding.
    """
    status: str = "AUTHORIZED"
    challenge_id: str
    transaction_reference_id: str
    amount: float
    beneficiary_account: str
    cryptographic_seal: str
    authorization_receipt_hash: str
    authorized_at: int
    verified_factors: list[str] = ["PASSWORD", "OTP", "TRANSACTION_BOUND_AFFIRMATION", "SECURITY_PIN"]
