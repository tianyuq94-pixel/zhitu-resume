from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


def default_storage_root() -> Path:
    return Path(__file__).resolve().parents[3] / "storage" / "uploads" / "resumes"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_CAREER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "职途简历 API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"])
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "ai_career"
    db_user: str = "ai_career"
    db_password: str = ""

    auth_secret: SecretStr = Field(min_length=32)
    auth_token_minutes: int = 60 * 24 * 7
    session_cookie_name: str = "ai_career_session"
    csrf_cookie_name: str = "ai_career_csrf"
    secure_cookies: bool = False

    storage_root: Path = Field(default_factory=default_storage_root)
    resume_max_bytes: int = 10 * 1024 * 1024
    resume_photo_max_bytes: int = 2 * 1024 * 1024
    resume_min_text_chars: int = 30
    resume_max_text_chars: int = 200_000
    resume_max_pdf_pages: int = 50
    docx_max_uncompressed_bytes: int = 50 * 1024 * 1024

    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: float = 60.0
    deepseek_max_tokens: int = 5000
    deepseek_max_attempts: int = 3
    ai_resume_max_chars: int = 60_000
    pdf_font_path: Path | None = None

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env.casefold() != "production":
            return self
        if not self.secure_cookies:
            raise ValueError("production requires AI_CAREER_SECURE_COOKIES=true")
        if not self.cors_origins:
            raise ValueError("production requires an explicit HTTPS CORS origin")
        unsafe_origins = {
            origin
            for origin in self.cors_origins
            if "localhost" in origin.casefold() or "127.0.0.1" in origin
        }
        if unsafe_origins:
            raise ValueError("production CORS origins must use the public HTTPS domain")
        if any(not origin.casefold().startswith("https://") for origin in self.cors_origins):
            raise ValueError("production CORS origins must use HTTPS")
        if not self.allowed_hosts or "*" in self.allowed_hosts:
            raise ValueError("production requires explicit AI_CAREER_ALLOWED_HOSTS")
        auth_secret = self.auth_secret.get_secret_value().strip()
        if auth_secret.casefold().startswith("replace-with"):
            raise ValueError("production requires a real AI_CAREER_AUTH_SECRET")
        if not self.db_password.strip() or self.db_password.casefold().startswith("replace-with"):
            raise ValueError("production requires a real AI_CAREER_DB_PASSWORD")
        if self.deepseek_api_key is None or not self.deepseek_api_key.get_secret_value().strip():
            raise ValueError("production requires AI_CAREER_DEEPSEEK_API_KEY")
        if self.deepseek_api_key.get_secret_value().strip().casefold().startswith("replace-with"):
            raise ValueError("production requires a real AI_CAREER_DEEPSEEK_API_KEY")
        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
