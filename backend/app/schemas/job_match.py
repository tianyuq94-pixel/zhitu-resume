import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobMatchRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=100)
    company_name: str | None = Field(default=None, max_length=100)
    job_description: str = Field(min_length=30, max_length=20_000)

    @field_validator("job_title", "job_description")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(re.sub(r"\s+", "", normalized)) < 2:
            raise ValueError("Required content too short")
        return normalized

    @field_validator("company_name")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @field_validator("job_description")
    @classmethod
    def validate_job_description(cls, value: str) -> str:
        if len(re.sub(r"\s+", "", value)) < 30:
            raise ValueError("Job requirements must contain at least 30 valid characters")
        return value


class KeyRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=2, max_length=300)
    jd_evidence: str = Field(min_length=2, max_length=800)


class MatchedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=2, max_length=300)
    resume_evidence: str = Field(min_length=2, max_length=800)


class MissingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=2, max_length=300)
    explanation: str = Field(min_length=4, max_length=500)


class JobMatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    match_score: int = Field(ge=0, le=100)
    key_requirements: list[KeyRequirement] = Field(min_length=3, max_length=8)
    matched_items: list[MatchedItem] = Field(max_length=8)
    missing_items: list[MissingItem] = Field(max_length=8)
    verdict: Literal["recommend", "consider", "low"]
    verdict_reason: str = Field(min_length=10, max_length=1000)
    improvements: list[str] = Field(min_length=2, max_length=6)


class JobMatchView(JobMatchResult):
    id: int
    resume_version: int
    job_title: str
    company_name: str | None
    job_description: str
    created_at: datetime


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def validate_job_match_facts(result: JobMatchResult, resume_text: str, job_description: str) -> None:
    compact_resume = _compact(resume_text)
    compact_jd = _compact(job_description)
    requirement_names = {_compact(item.requirement) for item in result.key_requirements}
    if len(requirement_names) != len(result.key_requirements):
        raise ValueError("Key job requirements cannot be duplicated")

    for item in result.key_requirements:
        if _compact(item.jd_evidence) not in compact_jd:
            raise ValueError("The quoted text for a key job requirement is not in the JD")

    matched_names: set[str] = set()
    for item in result.matched_items:
        name = _compact(item.requirement)
        if name not in requirement_names:
            raise ValueError("A matched item has no corresponding key job requirement")
        if _compact(item.resume_evidence) not in compact_resume:
            raise ValueError("The content referenced by a matched item is not in the CV")
        matched_names.add(name)
    if len(matched_names) != len(result.matched_items):
        raise ValueError("Matched items cannot be duplicated")

    missing_names: set[str] = set()
    for item in result.missing_items:
        name = _compact(item.requirement)
        if name not in requirement_names:
            raise ValueError("No corresponding core job requirements for unaddressed items")
        explanation = item.explanation.casefold()
        evidence_gap = re.search(r"not (?:clearly )?(?:evidenced|reflected|demonstrated|shown|documented) in (?:the |your )?(?:cv|resume)", explanation)
        if not evidence_gap and "未体现" not in item.explanation and "未明确" not in item.explanation:
            raise ValueError("Items not shown must state that this is how the CV presents it")
        missing_names.add(name)
    if len(missing_names) != len(result.missing_items):
        raise ValueError("Items not shown cannot be repeated")

    if matched_names & missing_names:
        raise ValueError("The same requirement cannot be marked as both matched and not reflected")
    if matched_names | missing_names != requirement_names:
        raise ValueError("Every core role requirement must be marked with a match status")

    expected_verdict = "recommend" if result.match_score >= 75 else "consider" if result.match_score >= 50 else "low"
    if result.verdict != expected_verdict:
        raise ValueError("The application conclusion is inconsistent with the match score")
