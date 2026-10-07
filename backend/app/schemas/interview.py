import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.factual_terms import technical_terms


class InterviewCreateRequest(BaseModel):
    job_match_id: int | None = Field(default=None, ge=1)
    job_title: str = Field(min_length=2, max_length=100)
    company_name: str | None = Field(default=None, max_length=100)
    job_requirements: str | None = Field(default=None, max_length=20_000)

    @field_validator("job_title")
    @classmethod
    def trim_job_title(cls, value: str) -> str:
        normalized = value.strip()
        if len(re.sub(r"\s+", "", normalized)) < 2:
            raise ValueError("Job title must contain at least 2 valid characters")
        return normalized

    @field_validator("company_name", "job_requirements")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class GeneratedInterviewQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence_no: int = Field(ge=1, le=5)
    question_text: str = Field(min_length=10, max_length=1000)
    focus_area: str = Field(min_length=2, max_length=100)
    resume_evidence: str | None = Field(default=None, max_length=1000)
    job_evidence: str = Field(min_length=2, max_length=1000)


class GeneratedInterviewQuestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[GeneratedInterviewQuestion] = Field(min_length=5, max_length=5)


class InterviewAnswerRequest(BaseModel):
    question_id: int = Field(ge=1)
    answer_text: str = Field(min_length=10, max_length=5000)

    @field_validator("answer_text")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        normalized = value.strip()
        if len(re.sub(r"\s+", "", normalized)) < 10:
            raise ValueError("The answer must contain at least 10 valid characters")
        return normalized


class InterviewDimensionScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relevance: int = Field(ge=0, le=100)
    specificity: int = Field(ge=0, le=100)
    structure: int = Field(ge=0, le=100)
    communication: int = Field(ge=0, le=100)


class InterviewQuestionFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    dimension_scores: InterviewDimensionScores
    strengths: list[str] = Field(min_length=1, max_length=3)
    issues: list[str] = Field(min_length=1, max_length=3)
    suggestions: list[str] = Field(min_length=2, max_length=4)
    answer_outline: list[str] = Field(min_length=3, max_length=5)


class InterviewReportDimensionScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: int = Field(ge=0, le=100)
    role_understanding: int = Field(ge=0, le=100)
    experience_evidence: int = Field(ge=0, le=100)
    answer_structure: int = Field(ge=0, le=100)


class InterviewFinalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=20, max_length=1200)
    dimension_scores: InterviewReportDimensionScores
    strengths: list[str] = Field(min_length=2, max_length=5)
    improvements: list[str] = Field(min_length=2, max_length=5)
    practice_focus: list[str] = Field(min_length=3, max_length=5)


class InterviewQuestionView(BaseModel):
    id: int
    sequence_no: int
    question_text: str
    focus_area: str
    answer_text: str | None
    feedback: InterviewQuestionFeedback | None
    answered_at: datetime | None


class InterviewSessionView(BaseModel):
    id: int
    resume_version: int
    job_match_id: int | None
    job_title: str
    company_name: str | None
    job_requirements: str | None
    status: Literal["answering", "reporting", "completed", "abandoned"]
    current_question_index: int
    questions: list[InterviewQuestionView]
    final_feedback: InterviewFinalReport | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def validate_generated_questions(
    result: GeneratedInterviewQuestions,
    resume_text: str,
    job_title: str,
    job_requirements: str | None,
) -> None:
    expected_sequence = [1, 2, 3, 4, 5]
    actual_sequence = [question.sequence_no for question in result.questions]
    if actual_sequence != expected_sequence:
        raise ValueError("Interview question numbers must be 1 to 5 in order")

    normalized_questions = {_compact(question.question_text) for question in result.questions}
    if len(normalized_questions) != 5:
        raise ValueError("The five interview questions cannot repeat")

    compact_resume = _compact(resume_text)
    compact_job_source = _compact(job_title + "\n" + (job_requirements or ""))
    resume_evidence_count = 0
    for question in result.questions:
        if _compact(question.job_evidence) not in compact_job_source:
            raise ValueError("The role basis cited by the interview question is not in the role information")
        if question.resume_evidence:
            if _compact(question.resume_evidence) not in compact_resume:
                raise ValueError("The experience cited by the interview question is not in the main CV")
            resume_evidence_count += 1
    if resume_evidence_count < 2:
        raise ValueError("At least two interview questions need to draw on experience from the main CV")


def validate_final_report(report: InterviewFinalReport) -> None:
    values = list(report.dimension_scores.model_dump().values())
    average = sum(values) / len(values)
    if abs(report.overall_score - average) > 20:
        raise ValueError("The overall score differs too much from the dimension scores")


def validate_question_feedback(feedback: InterviewQuestionFeedback, source_text: str) -> None:
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?(?:MB|GB|KB)?", source_text, flags=re.IGNORECASE))
    feedback_text = "\n".join(
        feedback.strengths + feedback.issues + feedback.suggestions + feedback.answer_outline
    )
    feedback_numbers = set(
        re.findall(r"\d+(?:\.\d+)?%?(?:MB|GB|KB)?", feedback_text, flags=re.IGNORECASE)
    )
    if not feedback_numbers.issubset(source_numbers):
        raise ValueError("The interview feedback added factual figures that were not present in the user input")

    source_terms = technical_terms(source_text)
    evaluation_text = "\n".join(feedback.strengths + feedback.issues)
    evaluation_terms = technical_terms(evaluation_text)
    if not evaluation_terms.issubset(source_terms):
        raise ValueError("The interview feedback added English technical terms or terminology that were not present in the input")
