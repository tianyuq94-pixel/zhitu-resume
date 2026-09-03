"""Create persistent database-backed file storage.

Revision ID: 0008_stored_files
Revises: 0007_interviews
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0008_stored_files"
down_revision: str | None = "0007_interviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stored_files",
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),
        sa.Column("content", mysql.LONGBLOB(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("storage_key"),
    )
    op.create_index("ix_stored_files_owner_user_id", "stored_files", ["owner_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stored_files_owner_user_id", table_name="stored_files")
    op.drop_table("stored_files")
