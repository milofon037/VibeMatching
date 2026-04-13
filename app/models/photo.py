from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Photo(Base):
    __tablename__ = "photos"
    __table_args__ = (
        UniqueConstraint("profile_id", "position", name="uq_photos_profile_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    photo_url: Mapped[str] = mapped_column(String(512), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    profile = relationship("Profile", back_populates="photos")
