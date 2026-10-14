from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey, Numeric, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reference_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    sender_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("beneficiaries.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # COMPLETED, FAILED, PENDING
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Adaptive Framework Metadata (System 3)
    auth_mode: Mapped[str] = mapped_column(String(30), default="ADAPTIVE_SYSTEM_3", nullable=False)
    auth_factors: Mapped[str] = mapped_column(String(150), nullable=False)  # e.g., PASSWORD,OTP or PASSWORD,OTP,TRANSACTION_BINDING_3FA
    risk_score: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)
    cryptographic_seal: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sender_account = relationship("Account", back_populates="transactions")
    beneficiary = relationship("Beneficiary", back_populates="transactions")
