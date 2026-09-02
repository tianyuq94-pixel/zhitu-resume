from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.dependencies.auth import require_trusted_origin
from app.services.security import (
    create_session_token,
    decode_session_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_and_verified() -> None:
    password = "StrongPassword123"
    encoded = hash_password(password)

    assert encoded != password
    assert verify_password(password, encoded)
    assert not verify_password("WrongPassword123", encoded)


def test_session_token_contains_user_and_version() -> None:
    user = SimpleNamespace(id=42, token_version=3)

    token = create_session_token(user)  # type: ignore[arg-type]

    assert decode_session_token(token) == (42, 3)


def _request_with_headers(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "http",
            "path": "/api/v1/profile",
            "raw_path": b"/api/v1/profile",
            "query_string": b"",
            "server": ("127.0.0.1", 80),
            "client": ("127.0.0.1", 12345),
            "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
        }
    )


def test_dynamic_https_same_origin_is_trusted_behind_proxy() -> None:
    request = _request_with_headers(
        {
            "origin": "https://preview-name.vercel.app",
            "host": "preview-name.vercel.app",
            "x-forwarded-proto": "https",
        }
    )

    require_trusted_origin(request)


def test_cross_site_origin_is_rejected_behind_proxy() -> None:
    request = _request_with_headers(
        {
            "origin": "https://attacker.example",
            "host": "preview-name.vercel.app",
            "x-forwarded-proto": "https",
        }
    )

    with pytest.raises(HTTPException) as error:
        require_trusted_origin(request)

    assert error.value.status_code == 403
