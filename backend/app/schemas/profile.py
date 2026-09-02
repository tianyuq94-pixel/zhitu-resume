from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileUpdateRequest(BaseModel):
    real_name: str | None = Field(default=None, max_length=50)
    school: str | None = Field(default=None, max_length=100)
    major: str | None = Field(default=None, max_length=100)
    degree: str | None = Field(default=None, max_length=30)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    career_direction: str | None = Field(default=None, max_length=100)
    desired_cities: list[str] = Field(default_factory=list, max_length=10)
    job_type: str | None = Field(default=None, max_length=30)

    @field_validator("real_name", "school", "major", "degree", "career_direction", "job_type")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    @field_validator("desired_cities")
    @classmethod
    def normalize_cities(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            city = value.strip()
            if city and city not in result:
                result.append(city)
        return result


class ProfileView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    real_name: str | None
    school: str | None
    major: str | None
    degree: str | None
    graduation_year: int | None
    career_direction: str | None
    desired_cities: list[str]
    job_type: str | None
    profile_completed: bool

