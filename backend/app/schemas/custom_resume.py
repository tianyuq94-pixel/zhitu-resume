import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CustomResumeCreateRequest(BaseModel):
    job_match_id: int | None = Field(default=None, ge=1)
    job_title: str | None = Field(default=None, max_length=100)
    company_name: str | None = Field(default=None, max_length=100)
    job_description: str | None = Field(default=None, max_length=20_000)

    @field_validator("job_title", "company_name", "job_description")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def require_job_information(self) -> "CustomResumeCreateRequest":
        if self.job_match_id is not None:
            return self
        if self.job_title is None or len(re.sub(r"\s+", "", self.job_title)) < 2:
            raise ValueError("岗位名称不能少于 2 个有效字符")
        if self.job_description is None or len(re.sub(r"\s+", "", self.job_description)) < 30:
            raise ValueError("岗位要求不能少于 30 个有效字符")
        return self


class GeneratedCustomResumeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_type: Literal["heading", "bullet"] = "bullet"
    source_text: str = Field(min_length=2, max_length=2000)
    suggested_text: str = Field(min_length=2, max_length=2000)
    reason: str = Field(min_length=4, max_length=500)


class GeneratedCustomResumeSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=50)
    items: list[GeneratedCustomResumeItem] = Field(min_length=1, max_length=12)


class GeneratedCustomResumeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[GeneratedCustomResumeSection] = Field(min_length=1, max_length=10)
    missing_information_warnings: list[str] = Field(max_length=8)

    @model_validator(mode="after")
    def validate_total_items(self) -> "GeneratedCustomResumeResult":
        total = sum(len(section.items) for section in self.sections)
        if total < 2 or total > 60:
            raise ValueError("定制简历内容条目数量不合理")
        return self


Decision = Literal["pending", "accepted", "rejected", "custom"]


class CustomResumeItem(GeneratedCustomResumeItem):
    decision: Decision
    final_text: str = Field(min_length=2, max_length=2000)


class CustomResumeSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=50)
    items: list[CustomResumeItem] = Field(min_length=1, max_length=12)


class CustomResumeUpdateItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Decision
    final_text: str = Field(min_length=2, max_length=2000)

    @field_validator("final_text")
    @classmethod
    def trim_final_text(cls, value: str) -> str:
        return value.strip()


class CustomResumeUpdateSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=50)
    items: list[CustomResumeUpdateItem] = Field(min_length=1, max_length=12)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        return value.strip()


class ResumeHeaderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="", max_length=40)
    political_status: str = Field(default="", max_length=40)
    phone: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=100)
    location: str = Field(default="", max_length=100)
    birth_date: str = Field(default="", max_length=40)

    @field_validator("name", "political_status", "phone", "email", "location", "birth_date")
    @classmethod
    def trim_header_text(cls, value: str) -> str:
        return value.strip()


class ResumeHeader(ResumeHeaderUpdate):
    has_photo: bool = False


class CustomResumeUpdateRequest(BaseModel):
    header: ResumeHeaderUpdate
    sections: list[CustomResumeUpdateSection] = Field(min_length=1, max_length=10)


class CustomResumeSummary(BaseModel):
    id: int
    source_resume_version: int
    job_match_id: int | None
    job_title: str
    company_name: str | None
    status: Literal["draft", "ready"]
    pending_count: int
    created_at: datetime
    updated_at: datetime


class CustomResumeView(CustomResumeSummary):
    job_description: str
    template_name: Literal["简历模板"] = "简历模板"
    header: ResumeHeader
    sections: list[CustomResumeSection]
    missing_information_warnings: list[str]


def validate_generated_custom_resume(result: GeneratedCustomResumeResult, resume_text: str) -> None:
    compact_resume = re.sub(r"\s+", "", resume_text).casefold()
    seen_sources: set[str] = set()
    for section in result.sections:
        for item in section.items:
            compact_source = re.sub(r"\s+", "", item.source_text).casefold()
            if compact_source not in compact_resume:
                raise ValueError("定制建议引用的原文不在主简历中")
            if compact_source in seen_sources:
                raise ValueError("定制简历不能重复引用同一段原文")
            seen_sources.add(compact_source)

            source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", item.source_text))
            suggested_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", item.suggested_text))
            if not suggested_numbers.issubset(source_numbers):
                raise ValueError("定制建议添加了主简历中不存在的数字")

            source_terms = {
                token.casefold()
                for token in re.findall(r"[A-Za-z][A-Za-z0-9.+#-]*", item.source_text)
            }
            suggested_terms = {
                token.casefold()
                for token in re.findall(r"[A-Za-z][A-Za-z0-9.+#-]*", item.suggested_text)
            }
            if not suggested_terms.issubset(source_terms):
                raise ValueError("定制建议添加了原文中不存在的英文技能或术语")

            safe_connective_characters = set("的了并且及与和在于以为将把被对从由使通过进行完成相关其更等后中")
            source_chinese = set(re.findall(r"[\u3400-\u9fff]", item.source_text))
            suggested_chinese = set(re.findall(r"[\u3400-\u9fff]", item.suggested_text))
            if suggested_chinese - source_chinese - safe_connective_characters:
                raise ValueError("定制建议添加了原文中不存在的事实性中文词语")


def build_editable_sections(result: GeneratedCustomResumeResult) -> list[dict]:
    return [
        {
            "title": section.title,
            "items": [
                {
                    **item.model_dump(),
                    "decision": "pending",
                    "final_text": item.source_text,
                }
                for item in section.items
            ],
        }
        for section in result.sections
    ]
