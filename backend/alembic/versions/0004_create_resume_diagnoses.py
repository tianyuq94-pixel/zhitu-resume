"""Create resume diagnoses and AI request logs.

Revision ID: 0004_resume_diagnoses
Revises: 0003_primary_resumes
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0004_resume_diagnoses"
down_revision: str | None = "0003_primary_resumes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_diagnoses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_version", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("dimension_scores", mysql.JSON(), nullable=True),
        sa.Column("strengths", mysql.JSON(), nullable=True),
        sa.Column("issues", mysql.JSON(), nullable=True),
        sa.Column("suggestions", mysql.JSON(), nullable=True),
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
    op.create_index("ix_resume_diagnoses_resume_id", "resume_diagnoses", ["resume_id"], unique=False)
    op.create_index("ix_resume_diagnoses_user_id", "resume_diagnoses", ["user_id"], unique=False)

    op.create_table(
        "ai_request_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("feature", sa.String(length=30), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", name="uq_ai_request_logs_request_id"),
    )
    op.create_index("ix_ai_request_logs_feature", "ai_request_logs", ["feature"], unique=False)
    op.create_index("ix_ai_request_logs_user_id", "ai_request_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_request_logs_user_id", table_name="ai_request_logs")
    op.drop_index("ix_ai_request_logs_feature", table_name="ai_request_logs")
    op.drop_table("ai_request_logs")
    op.drop_index("ix_resume_diagnoses_user_id", table_name="resume_diagnoses")
    op.drop_index("ix_resume_diagnoses_resume_id", table_name="resume_diagnoses")
    op.drop_table("resume_diagnoses")
