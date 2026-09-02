import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.security import InvalidSessionError, decode_session_token

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    request: Request,
    database: DatabaseSession,
) -> User:
    session_token = request.cookies.get(get_settings().session_cookie_name)
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    try:
        user_id, token_version = decode_session_token(session_token)
    except InvalidSessionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效") from exc

    user = database.scalar(
        select(User).options(selectinload(User.profile)).where(User.id == user_id)
    )
    if user is None or user.status != "active" or user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_csrf(request: Request) -> None:
    settings = get_settings()
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")
    if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="请求校验失败，请刷新页面后重试")


def require_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in set(get_settings().cors_origins):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="请求来源不受信任")


def request_client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"
