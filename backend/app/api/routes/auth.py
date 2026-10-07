from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
    request_client_key,
    require_csrf,
    require_trusted_origin,
)
from app.models.user import User, UserProfile
from app.schemas.auth import LoginRequest, PasswordUpdateRequest, RegisterRequest, UserView
from app.services.auth import clear_auth_cookies, set_auth_cookies, user_to_view
from app.services.rate_limit import auth_rate_limiter
from app.services.security import dummy_password_hash, hash_password, verify_password
from app.api.dependencies.auth import get_current_user
from uuid import uuid4
from app.services.agent_budget import check_budget

router = APIRouter()


@router.post('/guest', response_model=UserView, dependencies=[Depends(require_trusted_origin)])
def guest(request: Request, response: Response, database: DatabaseSession) -> UserView:
    try:
        user = get_current_user(request, database)
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
        check_budget(database, f'guest:{request_client_key(request)}', limit=10, window_seconds=3600)
        # An unguessable, non-login identity. All resources still require the signed cookie.
        user = User(username='guest_' + uuid4().hex[:26], password_hash=hash_password(uuid4().hex + uuid4().hex),
                    profile=UserProfile(desired_cities=[]))
        database.add(user)
        database.commit()
        database.refresh(user)
    set_auth_cookies(response, user)
    return user_to_view(user)


@router.post(
    "/register",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    database: DatabaseSession,
) -> UserView:
    auth_rate_limiter.check(
        f"register:{request_client_key(request)}",
        limit=5,
        window_seconds=600,
    )
    if database.scalar(select(User.id).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is already taken")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        profile=UserProfile(desired_cities=[]),
    )
    database.add(user)
    try:
        database.commit()
    except IntegrityError as exc:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is already taken") from exc
    database.refresh(user)
    user = database.scalar(
        select(User).options(selectinload(User.profile)).where(User.id == user.id)
    )
    assert user is not None
    set_auth_cookies(response, user)
    return user_to_view(user)


@router.post(
    "/login",
    response_model=UserView,
    dependencies=[Depends(require_trusted_origin)],
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    database: DatabaseSession,
) -> UserView:
    auth_rate_limiter.check(
        f"login:{request_client_key(request)}:{payload.username}",
        limit=10,
        window_seconds=300,
    )
    user = database.scalar(
        select(User).options(selectinload(User.profile)).where(User.username == payload.username)
    )
    encoded_password = user.password_hash if user is not None else dummy_password_hash
    password_valid = verify_password(payload.password, encoded_password)
    if user is None or user.status != "active" or not password_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    set_auth_cookies(response, user)
    return user_to_view(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def logout(response: Response) -> None:
    clear_auth_cookies(response)


@router.get("/me", response_model=UserView)
def get_me(current_user: CurrentUser) -> UserView:
    return user_to_view(current_user)


@router.put(
    "/password",
    response_model=UserView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def update_password(
    payload: PasswordUpdateRequest,
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> UserView:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the current password")

    current_user.password_hash = hash_password(payload.new_password)
    current_user.token_version += 1
    database.commit()
    database.refresh(current_user)
    set_auth_cookies(response, current_user)
    return user_to_view(current_user)
