from datetime import datetime, timezone, timedelta

from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config import settings
from database import Base


class OTP(Base):
    __tablename__ = "otps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), default="LOGIN", nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)
