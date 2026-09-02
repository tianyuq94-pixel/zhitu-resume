from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.core.config import get_settings
from app.models.resume import Resume
from app.parsers.resume import ResumeParseError, parse_resume
from app.schemas.resume import ResumeTextUpdateRequest, ResumeView
from app.services.rate_limit import auth_rate_limiter
from app.storage.local import get_resume_storage

router = APIRouter()


def _primary_resume(database: DatabaseSession, user_id: int) -> Resume | None:
    return database.scalar(select(Resume).where(Resume.user_id == user_id))


def _safe_original_name(value: str | None) -> str:
    name = (value or "resume").replace("\\", "/").split("/")[-1].strip()
    return name[:255] or "resume"


@router.get("/primary", response_model=ResumeView | None)
def get_primary_resume(current_user: CurrentUser, database: DatabaseSession) -> Resume | None:
    return _primary_resume(database, current_user.id)


@router.get("/primary/file")
def get_primary_resume_file(current_user: CurrentUser, database: DatabaseSession) -> FileResponse:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="尚未上传主简历")
    path = get_resume_storage().path_for(resume.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历原文件不存在")
    disposition = "inline" if resume.mime_type == "application/pdf" else "attachment"
    return FileResponse(
        path,
        media_type=resume.mime_type,
        filename=resume.original_name,
        content_disposition_type=disposition,
        headers={"Cache-Control": "private, no-store"},
    )


@router.post(
    "/primary",
    response_model=ResumeView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def upload_primary_resume(
    file: Annotated[UploadFile, File()],
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Resume:
    settings = get_settings()
    auth_rate_limiter.check(
        f"resume-upload:{current_user.id}",
        limit=10,
        window_seconds=3600,
    )
    content = await file.read(settings.resume_max_bytes + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传的文件为空")
    if len(content) > settings.resume_max_bytes:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="简历文件不能超过 10 MB")

    original_name = _safe_original_name(file.filename)
    try:
        parsed = parse_resume(content, original_name, file.content_type)
    except ResumeParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    storage = get_resume_storage()
    storage_key = storage.save(current_user.id, parsed.extension, content)
    resume = _primary_resume(database, current_user.id)
    previous_storage_key: str | None = None
    try:
        if resume is None:
            resume = Resume(
                user_id=current_user.id,
                original_name=original_name,
                storage_key=storage_key,
                mime_type=parsed.mime_type,
                size_bytes=len(content),
                parsed_text=parsed.text,
                parse_status="ready",
                content_version=1,
            )
            database.add(resume)
        else:
            previous_storage_key = resume.storage_key
            resume.original_name = original_name
            resume.storage_key = storage_key
            resume.mime_type = parsed.mime_type
            resume.size_bytes = len(content)
            resume.parsed_text = parsed.text
            resume.parse_status = "ready"
            resume.content_version += 1
            resume.confirmed_at = None
        database.commit()
        database.refresh(resume)
    except Exception:
        database.rollback()
        storage.delete(storage_key)
        raise

    if previous_storage_key and previous_storage_key != storage_key:
        storage.delete(previous_storage_key)
    return resume


@router.put(
    "/primary/text",
    response_model=ResumeView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def update_primary_resume_text(
    payload: ResumeTextUpdateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Resume:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="尚未上传主简历")
    resume.parsed_text = payload.parsed_text
    resume.content_version += 1
    resume.confirmed_at = datetime.now(UTC).replace(tzinfo=None)
    database.commit()
    database.refresh(resume)
    return resume


@router.delete(
    "/primary",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def delete_primary_resume(
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> None:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    storage_key = resume.storage_key
    database.delete(resume)
    database.commit()
    get_resume_storage().delete(storage_key)
