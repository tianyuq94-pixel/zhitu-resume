from types import SimpleNamespace

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

