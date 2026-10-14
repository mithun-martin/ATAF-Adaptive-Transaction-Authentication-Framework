from datetime import datetime

from sqlalchemy import String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    ifsc_code: Mapped[str] = mapped_column(String(11), default="SIMB0001234", nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(14, 2), default=100000.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="account")
    transactions = relationship("Transaction", back_populates="sender_account")
