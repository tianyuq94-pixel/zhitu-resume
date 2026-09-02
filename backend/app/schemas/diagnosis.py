import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DimensionScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    information_completeness: int = Field(ge=0, le=100)
    content_quality: int = Field(ge=0, le=100)
    achievement_quantification: int = Field(ge=0, le=100)
    professional_expression: int = Field(ge=0, le=100)
    career_direction_fit: int = Field(ge=0, le=100)


class ResumeSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_text: str = Field(min_length=2, max_length=1000)
    suggested_text: str = Field(min_length=2, max_length=1500)
    reason: str = Field(min_length=4, max_length=500)


class ResumeDiagnosisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(ge=0, le=100)
    dimension_scores: DimensionScores
    strengths: list[str] = Field(min_length=3, max_length=5)
    issues: list[str] = Field(min_length=3, max_length=5)
    suggestions: list[ResumeSuggestion] = Field(min_length=1, max_length=8)


class ResumeDiagnosisView(ResumeDiagnosisResult):
    id: int
    resume_version: int
    created_at: datetime


def validate_diagnosis_facts(result: ResumeDiagnosisResult, resume_text: str) -> None:
    compact_resume = re.sub(r"\s+", "", resume_text).casefold()
    for suggestion in result.suggestions:
        compact_source = re.sub(r"\s+", "", suggestion.source_text).casefold()
        if len(compact_source) < 2 or compact_source not in compact_resume:
            raise ValueError("修改建议引用的原文不在简历中")

        source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", suggestion.source_text))
        suggested_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", suggestion.suggested_text))
        if not suggested_numbers.issubset(source_numbers):
            raise ValueError("修改建议添加了原文中不存在的数字")
