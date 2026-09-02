from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, select

from app.ai.errors import AIServiceError
from app.ai.prompts.resume_diagnosis import PROMPT_VERSION
from app.ai.resume_diagnosis import generate_resume_diagnosis
from app.api.ai_support import profile_payload, public_ai_error
from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.core.config import get_settings
from app.models.ai import AIRequestLog, ResumeDiagnosis
from app.models.resume import Resume
from app.schemas.diagnosis import ResumeDiagnosisResult, ResumeDiagnosisView
from app.services.rate_limit import auth_rate_limiter

router = APIRouter()


def _primary_resume(database: DatabaseSession, user_id: int) -> Resume | None:
    return database.scalar(select(Resume).where(Resume.user_id == user_id))


def _to_view(diagnosis: ResumeDiagnosis) -> ResumeDiagnosisView:
    result = ResumeDiagnosisResult.model_validate(
        {
            "overall_score": diagnosis.overall_score,
            "dimension_scores": diagnosis.dimension_scores,
            "strengths": diagnosis.strengths,
            "issues": diagnosis.issues,
            "suggestions": diagnosis.suggestions,
        }
    )
    return ResumeDiagnosisView(
        id=diagnosis.id,
        resume_version=diagnosis.resume_version,
        created_at=diagnosis.created_at,
        **result.model_dump(),
    )


@router.get("/primary/diagnoses/latest", response_model=ResumeDiagnosisView | None)
def get_latest_resume_diagnosis(
    current_user: CurrentUser,
    database: DatabaseSession,
) -> ResumeDiagnosisView | None:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        return None
    diagnosis = database.scalar(
        select(ResumeDiagnosis)
        .where(
            ResumeDiagnosis.user_id == current_user.id,
            ResumeDiagnosis.resume_id == resume.id,
            ResumeDiagnosis.resume_version == resume.content_version,
            ResumeDiagnosis.status == "completed",
        )
        .order_by(desc(ResumeDiagnosis.created_at), desc(ResumeDiagnosis.id))
        .limit(1)
    )
    return _to_view(diagnosis) if diagnosis is not None else None


@router.post(
    "/primary/diagnoses",
    response_model=ResumeDiagnosisView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def create_resume_diagnosis(
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> ResumeDiagnosisView:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先上传主简历")
    if resume.confirmed_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先检查并确认简历文字")

    auth_rate_limiter.check(f"resume-diagnosis:{current_user.id}", limit=5, window_seconds=3600)
    settings = get_settings()
    request_id = str(uuid4())
    response.headers["X-Request-ID"] = request_id
    diagnosis = ResumeDiagnosis(
        user_id=current_user.id,
        resume_id=resume.id,
        resume_version=resume.content_version,
        model_name=settings.deepseek_model,
        prompt_version=PROMPT_VERSION,
        status="processing",
    )
    database.add(diagnosis)
    database.commit()
    database.refresh(diagnosis)
    started_at = perf_counter()

    try:
        generated = await generate_resume_diagnosis(resume.parsed_text, profile_payload(current_user))
        result = generated.result
        diagnosis.overall_score = result.overall_score
        diagnosis.dimension_scores = result.dimension_scores.model_dump()
        diagnosis.strengths = result.strengths
        diagnosis.issues = result.issues
        diagnosis.suggestions = [item.model_dump() for item in result.suggestions]
        diagnosis.status = "completed"
        log = AIRequestLog(
            user_id=current_user.id,
            feature="resume_diagnosis",
            request_id=request_id,
            model_name=settings.deepseek_model,
            prompt_version=PROMPT_VERSION,
            status="success",
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
            latency_ms=round((perf_counter() - started_at) * 1000),
        )
        database.add(log)
        database.commit()
        database.refresh(diagnosis)
        return _to_view(diagnosis)
    except AIServiceError as exc:
        diagnosis.status = "failed"
        diagnosis.error_code = exc.code
        database.add(
            AIRequestLog(
                user_id=current_user.id,
                feature="resume_diagnosis",
                request_id=request_id,
                model_name=settings.deepseek_model,
                prompt_version=PROMPT_VERSION,
                status="timeout" if exc.code == "AI_TIMEOUT" else "failed",
                latency_ms=round((perf_counter() - started_at) * 1000),
                error_code=exc.code,
            )
        )
        database.commit()
        status_code, message = public_ai_error(exc, "AI 暂时无法完成诊断，请稍后重试")
        raise HTTPException(status_code=status_code, detail=message) from exc
