from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, DateTime, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class TransactionChallenge(Base):
    """
    Stores pending transaction authorization challenges for Baseline Authentication (Step 2).
    Flow: Password verified -> Challenge created with OTP -> User submits OTP -> Transaction executed.
    """
    __tablename__ = "transaction_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("beneficiaries.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    otp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING_OTP")  # PENDING_OTP, VERIFIED, EXPIRED, CANCELLED
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User")
    beneficiary = relationship("Beneficiary")
