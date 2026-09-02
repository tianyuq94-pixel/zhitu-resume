"""Create custom resumes.

Revision ID: 0006_custom_resumes
Revises: 0005_job_matches
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0006_custom_resumes"
down_revision: str | None = "0005_job_matches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "custom_resumes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("source_resume_id", sa.BigInteger(), nullable=False),
        sa.Column("source_resume_version", sa.Integer(), nullable=False),
        sa.Column("job_match_id", sa.BigInteger(), nullable=True),
        sa.Column("job_title", sa.String(length=100), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=True),
        sa.Column("job_description", mysql.LONGTEXT(), nullable=False),
        sa.Column("content", mysql.JSON(), nullable=True),
        sa.Column("change_notes", mysql.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["job_match_id"], ["job_matches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_custom_resumes_job_match_id", "custom_resumes", ["job_match_id"], unique=False)
    op.create_index("ix_custom_resumes_source_resume_id", "custom_resumes", ["source_resume_id"], unique=False)
    op.create_index("ix_custom_resumes_user_id", "custom_resumes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_custom_resumes_user_id", table_name="custom_resumes")
    op.drop_index("ix_custom_resumes_source_resume_id", table_name="custom_resumes")
    op.drop_index("ix_custom_resumes_job_match_id", table_name="custom_resumes")
    op.drop_table("custom_resumes")
