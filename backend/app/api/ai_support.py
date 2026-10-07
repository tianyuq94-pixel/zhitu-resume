from fastapi import status

from app.ai.errors import AIServiceError
from app.api.dependencies.auth import CurrentUser


def profile_payload(current_user: CurrentUser) -> dict:
    profile = current_user.profile
    if profile is None:
        return {}
    values = {
        "school": profile.school,
        "major": profile.major,
        "degree": profile.degree,
        "graduation_year": profile.graduation_year,
        "career_direction": profile.career_direction,
        "desired_cities": profile.desired_cities,
        "job_type": profile.job_type,
    }
    return {key: value for key, value in values.items() if value not in (None, "", [])}


def public_ai_error(error: AIServiceError, fallback_message: str) -> tuple[int, str]:
    if error.code == "AI_NOT_CONFIGURED":
        return status.HTTP_503_SERVICE_UNAVAILABLE, "Smart service is not yet configured. Please contact the site administrator"
    if error.code == "AI_AUTH_FAILED":
        return status.HTTP_503_SERVICE_UNAVAILABLE, "Smart service configuration error. Please contact the site administrator"
    if error.code == "AI_BALANCE_INSUFFICIENT":
        return status.HTTP_503_SERVICE_UNAVAILABLE, "Smart service is temporarily unavailable. Please try again later"
    if error.code == "AI_RATE_LIMITED":
        return status.HTTP_429_TOO_MANY_REQUESTS, "The AI service is busy. Please try again later."
    if error.code == "AI_TIMEOUT":
        return status.HTTP_504_GATEWAY_TIMEOUT, "AI analysis timed out, please try again"
    if error.code == "AI_INPUT_TOO_LONG":
        return status.HTTP_400_BAD_REQUEST, "Input is too long, please shorten it and try again"
    return status.HTTP_503_SERVICE_UNAVAILABLE, fallback_message
