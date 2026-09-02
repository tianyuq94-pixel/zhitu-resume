import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


VALID_PRODUCTION_SECRETS = {
    "db_password": "a-real-production-database-password",
    "deepseek_api_key": "sk-real-test-key-for-settings-validation",
}


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="SECURE_COOKIES"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_secret="test-production-secret-with-more-than-32-characters",
            secure_cookies=False,
            cors_origins=["https://resume.example.com"],
            allowed_hosts=["resume.example.com"],
            **VALID_PRODUCTION_SECRETS,
        )


def test_production_rejects_local_or_non_https_origins() -> None:
    with pytest.raises(ValidationError, match="public HTTPS domain"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_secret="test-production-secret-with-more-than-32-characters",
            secure_cookies=True,
            cors_origins=["http://127.0.0.1:5173"],
            allowed_hosts=["resume.example.com"],
            **VALID_PRODUCTION_SECRETS,
        )

    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_secret="test-production-secret-with-more-than-32-characters",
            secure_cookies=True,
            cors_origins=["http://resume.example.com"],
            allowed_hosts=["resume.example.com"],
            **VALID_PRODUCTION_SECRETS,
        )


def test_production_requires_explicit_allowed_hosts() -> None:
    with pytest.raises(ValidationError, match="ALLOWED_HOSTS"):
        Settings(
            _env_file=None,
            app_env="production",
            auth_secret="test-production-secret-with-more-than-32-characters",
            secure_cookies=True,
            cors_origins=["https://resume.example.com"],
            allowed_hosts=["*"],
            **VALID_PRODUCTION_SECRETS,
        )


def test_valid_production_settings_are_accepted() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_secret="test-production-secret-with-more-than-32-characters",
        secure_cookies=True,
        cors_origins=["https://resume.example.com"],
        allowed_hosts=["resume.example.com"],
        **VALID_PRODUCTION_SECRETS,
    )

    assert settings.app_env == "production"


def test_production_application_hides_docs_and_enables_hsts(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_secret="test-production-secret-with-more-than-32-characters",
        secure_cookies=True,
        cors_origins=["https://resume.example.com"],
        allowed_hosts=["resume.example.com"],
        **VALID_PRODUCTION_SECRETS,
    )
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    application = create_app()

    response = TestClient(application).get(
        "/api/v1/health",
        headers={"Host": "resume.example.com"},
    )

    assert response.status_code == 200
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")
    assert application.docs_url is None
    assert application.openapi_url is None
