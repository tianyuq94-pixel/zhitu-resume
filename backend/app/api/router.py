from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.custom_resumes import router as custom_resumes_router
from app.api.routes.diagnoses import router as diagnoses_router
from app.api.routes.health import router as health_router
from app.api.routes.interviews import router as interviews_router
from app.api.routes.job_matches import router as job_matches_router
from app.api.routes.profile import router as profile_router
from app.api.routes.resumes import router as resumes_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(diagnoses_router, prefix="/resumes", tags=["resume-diagnoses"])
api_router.include_router(job_matches_router, prefix="/job-matches", tags=["job-matches"])
api_router.include_router(custom_resumes_router, prefix="/custom-resumes", tags=["custom-resumes"])
api_router.include_router(interviews_router, prefix="/interviews", tags=["interviews"])
