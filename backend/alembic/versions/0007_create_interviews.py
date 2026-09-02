"""Create interview sessions and questions.

Revision ID: 0007_interviews
Revises: 0006_custom_resumes
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0007_interviews"
down_revision: str | None = "0006_custom_resumes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_id", sa.BigInteger(), nullable=False),
        sa.Column("resume_version", sa.Integer(), nullable=False),
        sa.Column("job_match_id", sa.BigInteger(), nullable=True),
        sa.Column("job_title", sa.String(length=100), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=True),
        sa.Column("job_requirements", mysql.LONGTEXT(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_question_index", sa.Integer(), nullable=False),
        sa.Column("final_feedback", mysql.JSON(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=30), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["job_match_id"], ["job_matches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_job_match_id", "interview_sessions", ["job_match_id"], unique=False)
    op.create_index("ix_interview_sessions_resume_id", "interview_sessions", ["resume_id"], unique=False)
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"], unique=False)

    op.create_table(
        "interview_questions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.BigInteger(), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(length=1000), nullable=False),
        sa.Column("focus_area", sa.String(length=100), nullable=False),
        sa.Column("answer_text", mysql.LONGTEXT(), nullable=True),
        sa.Column("feedback", mysql.JSON(), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence_no", name="uq_interview_question_sequence"),
    )
    op.create_index("ix_interview_questions_session_id", "interview_questions", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_interview_questions_session_id", table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_resume_id", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_job_match_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
