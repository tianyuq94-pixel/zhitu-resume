from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select

from app.ai.errors import AIServiceError
from app.ai.job_match import generate_job_match
from app.ai.prompts.job_match import PROMPT_VERSION
from app.api.ai_support import profile_payload, public_ai_error
from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.core.config import get_settings
from app.models.ai import AIRequestLog, JobMatch
from app.models.resume import Resume
from app.schemas.job_match import JobMatchRequest, JobMatchResult, JobMatchView
from app.services.rate_limit import auth_rate_limiter

router = APIRouter()


def _primary_resume(database: DatabaseSession, user_id: int) -> Resume | None:
    return database.scalar(select(Resume).where(Resume.user_id == user_id))


def _to_view(job_match: JobMatch) -> JobMatchView:
    result = JobMatchResult.model_validate(
        {
            "match_score": job_match.match_score,
            "key_requirements": job_match.key_requirements,
            "matched_items": job_match.matched_items,
            "missing_items": job_match.missing_items,
            "verdict": job_match.verdict,
            "verdict_reason": job_match.verdict_reason,
            "improvements": job_match.improvements,
        }
    )
    return JobMatchView(
        id=job_match.id,
        resume_version=job_match.resume_version,
        job_title=job_match.job_title,
        company_name=job_match.company_name,
        job_description=job_match.job_description,
        created_at=job_match.created_at,
        **result.model_dump(),
    )


@router.get("/current", response_model=JobMatchView | None)
def get_current_job_match(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> JobMatchView | None:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        return None
    job_match = database.scalar(
        select(JobMatch)
        .where(
            JobMatch.user_id == current_user.id,
            JobMatch.resume_id == resume.id,
            JobMatch.resume_version == resume.content_version,
            JobMatch.status == "completed",
        )
        .order_by(desc(JobMatch.created_at), desc(JobMatch.id))
        .limit(1)
    )
    return _to_view(job_match) if job_match is not None else None


@router.post(
    "",
    response_model=JobMatchView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def create_job_match(
    payload: JobMatchRequest,
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> JobMatchView:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先上传主简历")
    if resume.confirmed_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先检查并确认简历文字")

    auth_rate_limiter.check(f"job-match:{current_user.id}", limit=5, window_seconds=3600)
    settings = get_settings()
    request_id = str(uuid4())
    response.headers["X-Request-ID"] = request_id
    job_match = JobMatch(
        user_id=current_user.id,
        resume_id=resume.id,
        resume_version=resume.content_version,
        job_title=payload.job_title,
        company_name=payload.company_name,
        job_description=payload.job_description,
        model_name=settings.deepseek_model,
        prompt_version=PROMPT_VERSION,
        status="processing",
    )
    database.add(job_match)
    database.commit()
    database.refresh(job_match)
    started_at = perf_counter()

    try:
        generated = await generate_job_match(
            resume.parsed_text,
            profile_payload(current_user),
            payload.job_title,
            payload.company_name,
            payload.job_description,
        )
        result = generated.result
        job_match.match_score = result.match_score
        job_match.key_requirements = [item.model_dump() for item in result.key_requirements]
        job_match.matched_items = [item.model_dump() for item in result.matched_items]
        job_match.missing_items = [item.model_dump() for item in result.missing_items]
        job_match.verdict = result.verdict
        job_match.verdict_reason = result.verdict_reason
        job_match.improvements = result.improvements
        job_match.status = "completed"
        database.add(
            AIRequestLog(
                user_id=current_user.id,
                feature="job_match",
                request_id=request_id,
                model_name=settings.deepseek_model,
                prompt_version=PROMPT_VERSION,
                status="success",
                input_tokens=generated.input_tokens,
                output_tokens=generated.output_tokens,
                latency_ms=round((perf_counter() - started_at) * 1000),
            )
        )
        database.commit()
        database.refresh(job_match)
        return _to_view(job_match)
    except AIServiceError as exc:
        job_match.status = "failed"
        job_match.error_code = exc.code
        database.add(
            AIRequestLog(
                user_id=current_user.id,
                feature="job_match",
                request_id=request_id,
                model_name=settings.deepseek_model,
                prompt_version=PROMPT_VERSION,
                status="timeout" if exc.code == "AI_TIMEOUT" else "failed",
                latency_ms=round((perf_counter() - started_at) * 1000),
                error_code=exc.code,
            )
        )
        database.commit()
        status_code, message = public_ai_error(exc, "AI 暂时无法完成岗位匹配，请稍后重试")
        raise HTTPException(status_code=status_code, detail=message) from exc
