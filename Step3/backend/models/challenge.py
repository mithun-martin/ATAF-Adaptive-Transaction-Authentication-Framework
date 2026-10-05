from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, DateTime, Numeric, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TransactionChallenge(Base):
    """
    Stores 3FA transaction authorization challenges for Step 3 (Static 3FA).
    Pipeline: Password -> OTP -> Additional Confirmation -> Transaction
    """
    __tablename__ = "transaction_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("beneficiaries.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Factor 2: OTP State
    otp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    otp_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Factor 3: Additional Confirmation State & Cryptographic Binding
    stage: Mapped[str] = mapped_column(
        String(40), default="AWAITING_OTP"
    )  # AWAITING_OTP, AWAITING_ADDITIONAL_CONFIRMATION, VERIFIED, EXPIRED, CANCELLED
    cryptographic_seal: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # HMAC-SHA256
    nonce: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User")
    beneficiary = relationship("Beneficiary")
