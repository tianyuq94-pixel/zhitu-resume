from fastapi import APIRouter, Depends

from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.schemas.profile import ProfileUpdateRequest, ProfileView
from app.services.auth import is_profile_complete

router = APIRouter()


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

