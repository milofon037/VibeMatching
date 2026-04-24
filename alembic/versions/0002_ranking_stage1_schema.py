"""Add interests catalog and base_rank for ranking stage 1.

Revision ID: 0002_ranking_stage1_schema
Revises: 0001_init_schema
Create Date: 2026-04-13 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_ranking_stage1_schema"
down_revision: str | None = "0001_init_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("name", name="uq_interests_name"),
    )

    op.create_table(
        "profile_interests",
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interest_id",
            sa.Integer(),
            sa.ForeignKey("interests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "profile_id",
            "interest_id",
            name="uq_profile_interests_profile_interest",
        ),
    )
    op.create_index(
        "ix_profile_interests_profile_id",
        "profile_interests",
        ["profile_id"],
    )
    op.create_index(
        "ix_profile_interests_interest_id",
        "profile_interests",
        ["interest_id"],
    )

    op.add_column(
        "ratings",
        sa.Column("base_rank", sa.Float(), nullable=False, server_default="0"),
    )
    op.drop_column("ratings", "total_score")
    op.drop_column("ratings", "penalty_score")
    op.drop_column("ratings", "behavior_score")
    op.drop_column("ratings", "primary_score")

    op.bulk_insert(
        sa.table(
            "interests",
            sa.column("name", sa.String),
        ),
        [
            {"name": "music"},
            {"name": "movies"},
            {"name": "travel"},
            {"name": "sports"},
            {"name": "books"},
            {"name": "cooking"},
            {"name": "gaming"},
            {"name": "art"},
        ],
    )


def downgrade() -> None:
    op.add_column(
        "ratings",
        sa.Column("primary_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ratings",
        sa.Column("behavior_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ratings",
        sa.Column("penalty_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ratings",
        sa.Column("total_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.drop_column("ratings", "base_rank")

    op.drop_index("ix_profile_interests_interest_id", table_name="profile_interests")
    op.drop_index("ix_profile_interests_profile_id", table_name="profile_interests")
    op.drop_table("profile_interests")

    op.drop_table("interests")
