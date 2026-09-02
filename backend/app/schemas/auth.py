import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


class UsernameMixin(BaseModel):
    username: str = Field(min_length=4, max_length=32)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise ValueError("用户名只能包含英文字母、数字和下划线")
        return normalized


class RegisterRequest(UsernameMixin):
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(UsernameMixin):
    password: str = Field(min_length=1, max_length=128)


class PasswordUpdateRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    profile_completed: bool
    created_at: datetime

