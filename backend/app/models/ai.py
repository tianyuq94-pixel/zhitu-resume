from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ResumeDiagnosis(TimestampMixin, Base):
    __tablename__ = "resume_diagnoses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_version: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dimension_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    issues: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)


class JobMatch(TimestampMixin, Base):
    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_version: Mapped[int] = mapped_column(Integer, nullable=False)
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_description: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key_requirements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    matched_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    missing_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verdict_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    improvements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)


class CustomResume(TimestampMixin, Base):
    __tablename__ = "custom_resumes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_resume_version: Mapped[int] = mapped_column(Integer, nullable=False)
    job_match_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("job_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_description: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    change_notes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="generating")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)


class InterviewSession(TimestampMixin, Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_version: Mapped[int] = mapped_column(Integer, nullable=False)
    job_match_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("job_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_requirements: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="preparing")
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    final_feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewQuestion(TimestampMixin, Base):
    __tablename__ = "interview_questions"
    __table_args__ = (UniqueConstraint("session_id", "sequence_no", name="uq_interview_question_sequence"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    focus_area: Mapped[str] = mapped_column(String(100), nullable=False)
    answer_text: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AIRequestLog(TimestampMixin, Base):
    __tablename__ = "ai_request_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
