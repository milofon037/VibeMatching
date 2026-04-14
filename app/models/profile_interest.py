from sqlalchemy import Column, ForeignKey, Integer, Table, UniqueConstraint

from app.core.database import Base

profile_interests = Table(
    "profile_interests",
    Base.metadata,
    Column("profile_id", Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint("profile_id", "interest_id", name="uq_profile_interests_profile_interest"),
)
