from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResumeTextUpdateRequest(BaseModel):
    parsed_text: str = Field(min_length=30, max_length=200_000)

    @field_validator("parsed_text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.replace("\x00", "").strip()
        if len("".join(normalized.split())) < 30:
            raise ValueError("简历文字不能少于 30 个有效字符")
        return normalized


class ResumeView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    mime_type: str
    size_bytes: int
    parsed_text: str
    parse_status: str
    content_version: int
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime

