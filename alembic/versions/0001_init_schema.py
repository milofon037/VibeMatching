"""Create initial schema for VibeMatching backend.

Revision ID: 0001_init_schema
Revises:
Create Date: 2026-03-29 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_init_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_status_enum = sa.Enum("active", "banned", "shadow_banned", name="userstatus")
gender_enum = sa.Enum("male", "female", "other", name="gender")
search_city_mode_enum = sa.Enum("local", "global", name="searchcitymode")
swipe_action_enum = sa.Enum("like", "skip", name="swipeaction")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("referral_code", sa.String(length=64), nullable=True),
        sa.Column("invited_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("complaints_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", user_status_enum, nullable=False, server_default="active"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", gender_enum, nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("interests", sa.Text(), nullable=True),
        sa.Column("preferred_gender", gender_enum, nullable=True),
        sa.Column("preferred_age_min", sa.Integer(), nullable=True),
        sa.Column("preferred_age_max", sa.Integer(), nullable=True),
        sa.Column("search_city_mode", search_city_mode_enum, nullable=False, server_default="local"),
        sa.CheckConstraint("age >= 18", name="ck_profiles_age_adult"),
        sa.UniqueConstraint("user_id", name="uq_profiles_user_id"),
    )

    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_url", sa.String(length=512), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("profile_id", "position", name="uq_photos_profile_position"),
    )
    op.create_index("ix_photos_profile_id", "photos", ["profile_id"])

    op.create_table(
        "swipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_profile_id", sa.Integer(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", swipe_action_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("from_user_id", "to_profile_id", name="uq_swipes_unique_user_profile"),
    )
    op.create_index("ix_swipes_from_user_id", "swipes", ["from_user_id"])
    op.create_index("ix_swipes_to_profile_id", "swipes", ["to_profile_id"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user1_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user2_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("dialog_started", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("user1_id", "user2_id", name="uq_matches_unique_pair"),
    )
    op.create_index("ix_matches_user1_id", "matches", ["user1_id"])
    op.create_index("ix_matches_user2_id", "matches", ["user2_id"])

    op.create_table(
        "ratings",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("primary_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("behavior_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("penalty_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "rating_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rating_history_user_id", "rating_history", ["user_id"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_complaints_from_user_id", "complaints", ["from_user_id"])
    op.create_index("ix_complaints_to_user_id", "complaints", ["to_user_id"])


def downgrade() -> None:
    op.drop_index("ix_complaints_to_user_id", table_name="complaints")
    op.drop_index("ix_complaints_from_user_id", table_name="complaints")
    op.drop_table("complaints")

    op.drop_index("ix_rating_history_user_id", table_name="rating_history")
    op.drop_table("rating_history")

    op.drop_table("ratings")

    op.drop_index("ix_matches_user2_id", table_name="matches")
    op.drop_index("ix_matches_user1_id", table_name="matches")
    op.drop_table("matches")

    op.drop_index("ix_swipes_to_profile_id", table_name="swipes")
    op.drop_index("ix_swipes_from_user_id", table_name="swipes")
    op.drop_table("swipes")

    op.drop_index("ix_photos_profile_id", table_name="photos")
    op.drop_table("photos")

    op.drop_table("profiles")

    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
