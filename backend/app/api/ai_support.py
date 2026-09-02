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
        return status.HTTP_503_SERVICE_UNAVAILABLE, "智能服务尚未配置，请联系网站管理员"
    if error.code == "AI_AUTH_FAILED":
        return status.HTTP_503_SERVICE_UNAVAILABLE, "智能服务配置异常，请联系网站管理员"
    if error.code == "AI_BALANCE_INSUFFICIENT":
        return status.HTTP_503_SERVICE_UNAVAILABLE, "智能服务暂时不可用，请稍后重试"
    if error.code == "AI_RATE_LIMITED":
        return status.HTTP_429_TOO_MANY_REQUESTS, "AI 服务请求较多，请稍后重试"
    if error.code == "AI_TIMEOUT":
        return status.HTTP_504_GATEWAY_TIMEOUT, "AI 分析超时，请重试"
    if error.code == "AI_INPUT_TOO_LONG":
        return status.HTTP_400_BAD_REQUEST, "输入内容过长，请精简后重试"
    return status.HTTP_503_SERVICE_UNAVAILABLE, fallback_message
