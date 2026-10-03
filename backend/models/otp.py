from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class OTP(Base):
    """Stores OTPs for login and transaction verification.
    
    In this simulation, OTPs are displayed in the UI instead of being
    sent via SMS. This keeps the app self-contained while preserving
    the real OTP workflow for authentication research.
    """
    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)  # LOGIN, TRANSACTION
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
