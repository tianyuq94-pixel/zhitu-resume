"""Create job matches.

Revision ID: 0005_job_matches
Revises: 0004_resume_diagnoses
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0005_job_matches"
down_revision: str | None = "0004_resume_diagnoses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_matches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_version", sa.Integer(), nullable=False),
        sa.Column("job_title", sa.String(length=100), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=True),
        sa.Column("job_description", mysql.LONGTEXT(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("key_requirements", mysql.JSON(), nullable=True),
        sa.Column("matched_items", mysql.JSON(), nullable=True),
        sa.Column("missing_items", mysql.JSON(), nullable=True),
        sa.Column("verdict", sa.String(length=20), nullable=True),
        sa.Column("verdict_reason", sa.String(length=1000), nullable=True),
        sa.Column("improvements", mysql.JSON(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_matches_resume_id", "job_matches", ["resume_id"], unique=False)
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_matches_user_id", table_name="job_matches")
    op.drop_index("ix_job_matches_resume_id", table_name="job_matches")
    op.drop_table("job_matches")
