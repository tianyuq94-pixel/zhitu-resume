import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
            raise ValueError("岗位名称不能少于 2 个有效字符")
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
            raise ValueError("回答不能少于 10 个有效字符")
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
        raise ValueError("面试题序号必须依次为 1 到 5")

    normalized_questions = {_compact(question.question_text) for question in result.questions}
    if len(normalized_questions) != 5:
        raise ValueError("五道面试题不能重复")

    compact_resume = _compact(resume_text)
    compact_job_source = _compact(job_title + "\n" + (job_requirements or ""))
    resume_evidence_count = 0
    for question in result.questions:
        if _compact(question.job_evidence) not in compact_job_source:
            raise ValueError("面试题引用的岗位依据不在岗位信息中")
        if question.resume_evidence:
            if _compact(question.resume_evidence) not in compact_resume:
                raise ValueError("面试题引用的经历不在主简历中")
            resume_evidence_count += 1
    if resume_evidence_count < 2:
        raise ValueError("至少两道面试题需要结合主简历经历")


def validate_final_report(report: InterviewFinalReport) -> None:
    values = list(report.dimension_scores.model_dump().values())
    average = sum(values) / len(values)
    if abs(report.overall_score - average) > 20:
        raise ValueError("综合分数与维度分数差异过大")


def validate_question_feedback(feedback: InterviewQuestionFeedback, source_text: str) -> None:
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?(?:MB|GB|KB)?", source_text, flags=re.IGNORECASE))
    feedback_text = "\n".join(
        feedback.strengths + feedback.issues + feedback.suggestions + feedback.answer_outline
    )
    feedback_numbers = set(
        re.findall(r"\d+(?:\.\d+)?%?(?:MB|GB|KB)?", feedback_text, flags=re.IGNORECASE)
    )
    if not feedback_numbers.issubset(source_numbers):
        raise ValueError("面试点评添加了用户输入中不存在的事实性数字")

    source_terms = {
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9.+#-]*", source_text)
    }
    evaluation_text = "\n".join(feedback.strengths + feedback.issues)
    evaluation_terms = {
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9.+#-]*", evaluation_text)
    }
    if not evaluation_terms.issubset(source_terms):
        raise ValueError("面试点评添加了输入中不存在的英文技术或术语")
