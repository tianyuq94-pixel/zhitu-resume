"""Create primary resumes.

Revision ID: 0003_primary_resumes
Revises: 0002_username_index
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0003_primary_resumes"
down_revision: str | None = "0002_username_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("parsed_text", mysql.LONGTEXT(), nullable=False),
        sa.Column("parse_status", sa.String(length=20), server_default="ready", nullable=False),
        sa.Column("content_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_resumes_storage_key"),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")

