from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, DateTime, Numeric, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TransactionChallenge(Base):
    """
    Stores adaptive transaction authorization challenges for Step 9 (Proposed System 3).
    Dynamic Pipeline:
      Password -> AI Risk Scoring -> Adaptive Policy:
        - LOW (<0.30): OTP -> Authorize
        - MEDIUM (0.30-0.70): Warning Banner + OTP -> Authorize
        - HIGH (>=0.70): OTP -> Transaction-Bound Verification (Affirmations + Seal + PIN) -> Authorize
    """
    __tablename__ = "transaction_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("beneficiaries.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # AI Risk & Adaptive Policy State
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    auth_action: Mapped[str] = mapped_column(String(30), nullable=False)  # NORMAL, WARNING, STRONG_VERIFICATION
    warning_banner: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_reasons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded string
    requires_pin: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_cryptographic_seal: Mapped[bool] = mapped_column(Boolean, default=False)

    # Factor 2: OTP State
    otp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    otp_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Dynamic Stage & Factor 3 Cryptographic Binding (Step 8)
    stage: Mapped[str] = mapped_column(
        String(40), default="AWAITING_OTP"
    )  # AWAITING_OTP, AWAITING_HIGH_RISK_VERIFICATION, COMPLETED, EXPIRED, CANCELLED
    cryptographic_seal: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # HMAC-SHA256
    nonce: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    seal_timestamp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User")
    beneficiary = relationship("Beneficiary")
