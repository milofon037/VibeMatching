from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    referral_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    invited_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    complaints_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="userstatus",
        ),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    profile = relationship("Profile", back_populates="user", uselist=False)
