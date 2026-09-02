"""Create users and user profiles.

Revision ID: 0001_users_profiles
Revises:
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_users_profiles"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("phone_verified_at", sa.DateTime(), nullable=True),
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("real_name", sa.String(length=50), nullable=True),
        sa.Column("school", sa.String(length=100), nullable=True),
        sa.Column("major", sa.String(length=100), nullable=True),
        sa.Column("degree", sa.String(length=30), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("career_direction", sa.String(length=100), nullable=True),
        sa.Column("desired_cities", sa.JSON(), nullable=False),
        sa.Column("job_type", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_profiles")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

