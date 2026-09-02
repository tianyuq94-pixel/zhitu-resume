from fastapi import Response

from app.core.config import get_settings
from app.models.user import User, UserProfile
from app.schemas.auth import UserView
from app.services.security import create_csrf_token, create_session_token


def is_profile_complete(profile: UserProfile | None) -> bool:
    if profile is None:
        return False
    return all(
        [
            profile.school,
            profile.major,
            profile.degree,
            profile.graduation_year,
            profile.career_direction,
            profile.job_type,
        ]
    )


def user_to_view(user: User) -> UserView:
    return UserView(
        id=user.id,
        username=user.username,
        profile_completed=is_profile_complete(user.profile),
        created_at=user.created_at,
    )


def set_auth_cookies(response: Response, user: User) -> None:
    settings = get_settings()
    max_age = settings.auth_token_minutes * 60
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(user),
        max_age=max_age,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=create_csrf_token(),
        max_age=max_age,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")

