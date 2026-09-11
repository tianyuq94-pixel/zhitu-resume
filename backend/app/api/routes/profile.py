from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy import update
from app.models.user import UserProfile
from app.services.career_facts import CareerFacts, facts_view

from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.schemas.profile import ProfileUpdateRequest, ProfileView
from app.services.auth import is_profile_complete

router = APIRouter()


@router.get("/facts", response_model=CareerFacts)
def get_facts(current_user: CurrentUser) -> CareerFacts:
    return facts_view(current_user)


@router.put("/facts", response_model=CareerFacts, dependencies=[Depends(require_trusted_origin), Depends(require_csrf)])
def save_facts(payload: CareerFacts, current_user: CurrentUser, database: DatabaseSession) -> CareerFacts:
    changed = database.execute(update(UserProfile).where(
        UserProfile.user_id == current_user.id, UserProfile.facts_revision == payload.revision
    ).values(extra_facts=payload.model_dump(exclude={"revision"}), facts_revision=payload.revision + 1))
    if changed.rowcount != 1:
        database.rollback()
        raise HTTPException(409, "资料已在其他页面更新，请先复制当前编辑内容，再刷新核对")
    database.commit()
    database.refresh(current_user.profile)
    return facts_view(current_user)


def profile_to_view(current_user: CurrentUser) -> ProfileView:
    profile = current_user.profile
    return ProfileView(
        real_name=profile.real_name,
        school=profile.school,
        major=profile.major,
        degree=profile.degree,
        graduation_year=profile.graduation_year,
        career_direction=profile.career_direction,
        desired_cities=profile.desired_cities or [],
        job_type=profile.job_type,
        profile_completed=is_profile_complete(profile),
    )


@router.get("", response_model=ProfileView)
def get_profile(current_user: CurrentUser) -> ProfileView:
    return profile_to_view(current_user)


@router.put(
    "",
    response_model=ProfileView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> ProfileView:
    profile = current_user.profile
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    database.commit()
    database.refresh(profile)
    return profile_to_view(current_user)
