import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.models.user import User

password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash("dummy-password-used-for-timing-safety")


class InvalidSessionError(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_password: str) -> bool:
    return password_hash.verify(password, encoded_password)


def create_session_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user.id),
        "ver": user.token_version,
        "iat": now,
        "exp": now + timedelta(minutes=settings.auth_token_minutes),
    }
    return jwt.encode(
        payload,
        settings.auth_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_session_token(token: str) -> tuple[int, int]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "ver", "iat", "exp"]},
        )
        return int(payload["sub"]), int(payload["ver"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise InvalidSessionError from exc


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)
