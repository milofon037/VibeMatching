from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Gender, SearchCityMode
from app.models.profile_interest import profile_interests  # noqa: F401


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (CheckConstraint("age >= 18", name="ck_profiles_age_adult"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[Gender] = mapped_column(
        Enum(
            Gender,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="gender",
        ),
        nullable=False,
    )
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_gender: Mapped[Gender | None] = mapped_column(
        Enum(
            Gender,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="gender",
        ),
        nullable=True,
    )
    preferred_age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_city_mode: Mapped[SearchCityMode] = mapped_column(
        Enum(
            SearchCityMode,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="searchcitymode",
        ),
        default=SearchCityMode.LOCAL,
        nullable=False,
    )

    user = relationship("User", back_populates="profile")
    photos = relationship("Photo", back_populates="profile", cascade="all, delete-orphan")
    interests_catalog = relationship(
        "Interest",
        secondary="profile_interests",
        back_populates="profiles",
        lazy="selectin",
    )
