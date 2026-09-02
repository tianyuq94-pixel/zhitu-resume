from time import perf_counter
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import desc, select

from app.ai.custom_resume import generate_custom_resume
from app.ai.errors import AIServiceError
from app.ai.prompts.custom_resume import PROMPT_VERSION
from app.api.ai_support import profile_payload, public_ai_error
from app.api.dependencies.auth import CurrentUser, DatabaseSession, require_csrf, require_trusted_origin
from app.core.config import get_settings
from app.models.ai import AIRequestLog, CustomResume, JobMatch
from app.models.resume import Resume
from app.schemas.custom_resume import (
    CustomResumeCreateRequest,
    CustomResumeSection,
    CustomResumeSummary,
    CustomResumeUpdateRequest,
    CustomResumeView,
    ResumeHeader,
    build_editable_sections,
)
from app.services.custom_resume_photo import (
    ResumePhotoError,
    get_custom_resume_photo_storage,
    validate_resume_photo,
)
from app.services.custom_resume_docx import build_custom_resume_docx
from app.services.custom_resume_pdf import build_custom_resume_pdf
from app.services.rate_limit import auth_rate_limiter
from app.services.resume_header import extract_resume_header

router = APIRouter()


def _primary_resume(database: DatabaseSession, user_id: int) -> Resume | None:
    return database.scalar(select(Resume).where(Resume.user_id == user_id))


def _owned_custom_resume(database: DatabaseSession, user_id: int, custom_resume_id: int) -> CustomResume:
    custom_resume = database.scalar(
        select(CustomResume).where(CustomResume.id == custom_resume_id, CustomResume.user_id == user_id)
    )
    if custom_resume is None or custom_resume.status not in {"draft", "ready"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到这份定制简历")
    return custom_resume


def _pending_count(custom_resume: CustomResume) -> int:
    sections = (custom_resume.content or {}).get("sections", [])
    return sum(
        1
        for section in sections
        for item in section.get("items", [])
        if item.get("decision") == "pending"
    )


def _header_view(custom_resume: CustomResume, resume_text: str | None = None) -> ResumeHeader:
    header = (custom_resume.content or {}).get("header", {})
    if not any(header.get(field) for field in ResumeHeader.model_fields if field != "has_photo") and resume_text:
        header = {**extract_resume_header(resume_text), **header}
    public_fields = {field: header.get(field, "") for field in ResumeHeader.model_fields if field != "has_photo"}
    return ResumeHeader(
        **public_fields,
        has_photo=bool(header.get("_photo_storage_key")),
    )


def _to_summary(custom_resume: CustomResume) -> CustomResumeSummary:
    return CustomResumeSummary(
        id=custom_resume.id,
        source_resume_version=custom_resume.source_resume_version,
        job_match_id=custom_resume.job_match_id,
        job_title=custom_resume.job_title,
        company_name=custom_resume.company_name,
        status=custom_resume.status,
        pending_count=_pending_count(custom_resume),
        created_at=custom_resume.created_at,
        updated_at=custom_resume.updated_at,
    )


def _to_view(custom_resume: CustomResume, resume_text: str | None = None) -> CustomResumeView:
    content = custom_resume.content or {}
    change_notes = custom_resume.change_notes or {}
    return CustomResumeView(
        **_to_summary(custom_resume).model_dump(),
        job_description=custom_resume.job_description,
        header=_header_view(custom_resume, resume_text),
        sections=[CustomResumeSection.model_validate(section) for section in content.get("sections", [])],
        missing_information_warnings=change_notes.get("missing_information_warnings", []),
    )


@router.get("", response_model=list[CustomResumeSummary])
def list_custom_resumes(current_user: CurrentUser, database: DatabaseSession) -> list[CustomResumeSummary]:
    rows = database.scalars(
        select(CustomResume)
        .where(CustomResume.user_id == current_user.id, CustomResume.status.in_(["draft", "ready"]))
        .order_by(desc(CustomResume.updated_at), desc(CustomResume.id))
    ).all()
    return [_to_summary(row) for row in rows]


@router.post(
    "",
    response_model=CustomResumeView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def create_custom_resume(
    payload: CustomResumeCreateRequest,
    response: Response,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> CustomResumeView:
    resume = _primary_resume(database, current_user.id)
    if resume is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先上传主简历")
    if resume.confirmed_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请先检查并确认简历文字")

    job_match: JobMatch | None = None
    if payload.job_match_id is not None:
        job_match = database.scalar(
            select(JobMatch).where(
                JobMatch.id == payload.job_match_id,
                JobMatch.user_id == current_user.id,
                JobMatch.status == "completed",
            )
        )
        if job_match is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到对应的岗位匹配结果")
        if job_match.resume_id != resume.id or job_match.resume_version != resume.content_version:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="主简历已更新，请重新进行岗位匹配")
        job_title = job_match.job_title
        company_name = job_match.company_name
        job_description = job_match.job_description
    else:
        job_title = payload.job_title or ""
        company_name = payload.company_name
        job_description = payload.job_description or ""

    auth_rate_limiter.check(f"custom-resume:{current_user.id}", limit=5, window_seconds=3600)
    settings = get_settings()
    request_id = str(uuid4())
    response.headers["X-Request-ID"] = request_id
    custom_resume = CustomResume(
        user_id=current_user.id,
        source_resume_id=resume.id,
        source_resume_version=resume.content_version,
        job_match_id=job_match.id if job_match else None,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
        model_name=settings.deepseek_model,
        prompt_version=PROMPT_VERSION,
        status="generating",
    )
    database.add(custom_resume)
    database.commit()
    database.refresh(custom_resume)
    started_at = perf_counter()

    try:
        generated = await generate_custom_resume(
            resume.parsed_text,
            profile_payload(current_user),
            job_title,
            company_name,
            job_description,
        )
        custom_resume.content = {
            "template_name": "简历模板",
            "header": extract_resume_header(resume.parsed_text),
            "sections": build_editable_sections(generated.result),
        }
        custom_resume.change_notes = {
            "missing_information_warnings": generated.result.missing_information_warnings
        }
        custom_resume.status = "draft"
        database.add(
            AIRequestLog(
                user_id=current_user.id,
                feature="custom_resume",
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
        database.refresh(custom_resume)
        return _to_view(custom_resume, resume.parsed_text)
    except AIServiceError as exc:
        custom_resume.status = "failed"
        custom_resume.error_code = exc.code
        database.add(
            AIRequestLog(
                user_id=current_user.id,
                feature="custom_resume",
                request_id=request_id,
                model_name=settings.deepseek_model,
                prompt_version=PROMPT_VERSION,
                status="timeout" if exc.code == "AI_TIMEOUT" else "failed",
                latency_ms=round((perf_counter() - started_at) * 1000),
                error_code=exc.code,
            )
        )
        database.commit()
        status_code, message = public_ai_error(exc, "AI 暂时无法生成定制简历，请稍后重试")
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/{custom_resume_id}", response_model=CustomResumeView)
def get_custom_resume(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> CustomResumeView:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    source_resume = database.get(Resume, custom_resume.source_resume_id)
    return _to_view(custom_resume, source_resume.parsed_text if source_resume else None)


@router.put(
    "/{custom_resume_id}",
    response_model=CustomResumeView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def update_custom_resume(
    custom_resume_id: int,
    payload: CustomResumeUpdateRequest,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> CustomResumeView:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    existing_sections = (custom_resume.content or {}).get("sections", [])
    existing_header = (custom_resume.content or {}).get("header", {})
    if len(payload.sections) != len(existing_sections):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="简历栏目结构与原版本不一致")

    merged_sections: list[dict] = []
    for existing_section, update_section in zip(existing_sections, payload.sections, strict=True):
        existing_items = existing_section.get("items", [])
        if len(update_section.items) != len(existing_items):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="简历内容结构与原版本不一致")
        merged_items = []
        for existing_item, update_item in zip(existing_items, update_section.items, strict=True):
            decision = update_item.decision
            if decision in {"pending", "rejected"}:
                final_text = existing_item["source_text"]
            elif decision == "accepted":
                final_text = existing_item["suggested_text"]
            else:
                final_text = update_item.final_text
            merged_items.append({**existing_item, "decision": decision, "final_text": final_text})
        merged_sections.append({"title": update_section.title, "items": merged_items})

    merged_header = payload.header.model_dump()
    for private_key in ("_photo_storage_key", "_photo_mime"):
        if existing_header.get(private_key):
            merged_header[private_key] = existing_header[private_key]
    custom_resume.content = {
        "template_name": "简历模板",
        "header": merged_header,
        "sections": merged_sections,
    }
    custom_resume.status = (
        "draft"
        if not merged_header.get("name")
        or any(item["decision"] == "pending" for section in merged_sections for item in section["items"])
        else "ready"
    )
    database.commit()
    database.refresh(custom_resume)
    return _to_view(custom_resume)


@router.post(
    "/{custom_resume_id}/export",
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def export_custom_resume(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Response:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    if custom_resume.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请填写姓名、处理完全部 AI 建议并保存")
    pdf_bytes = build_custom_resume_pdf(custom_resume)
    safe_title = "".join(character for character in custom_resume.job_title if character not in '\\/:*?"<>|')[:50]
    filename = f"{safe_title or '岗位'}-定制简历.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=custom-resume.pdf; filename*=UTF-8''{quote(filename)}"},
    )


@router.post(
    "/{custom_resume_id}/export/word",
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def export_custom_resume_word(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Response:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    if custom_resume.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="请填写姓名、处理完全部 AI 建议并保存")
    docx_bytes = build_custom_resume_docx(custom_resume)
    safe_title = "".join(character for character in custom_resume.job_title if character not in '\\/:*?"<>|')[:50]
    filename = f"{safe_title or '岗位'}-定制简历.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=custom-resume.docx; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/{custom_resume_id}/photo")
def get_custom_resume_photo(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Response:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    header = (custom_resume.content or {}).get("header", {})
    storage_key = header.get("_photo_storage_key")
    if not storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="这份简历还没有证件照")
    path = get_custom_resume_photo_storage().path_for(storage_key)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="证件照文件不存在")
    return Response(
        content=path.read_bytes(),
        media_type=header.get("_photo_mime") or "image/jpeg",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.post(
    "/{custom_resume_id}/photo",
    response_model=CustomResumeView,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
async def upload_custom_resume_photo(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
    photo: UploadFile = File(...),
) -> CustomResumeView:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    declared_mime_type = photo.content_type
    content_bytes = await photo.read(get_settings().resume_photo_max_bytes + 1)
    await photo.close()
    try:
        mime_type, extension = validate_resume_photo(content_bytes, declared_mime_type)
    except ResumePhotoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    storage = get_custom_resume_photo_storage()
    storage_key = storage.save(current_user.id, extension, content_bytes)
    content = dict(custom_resume.content or {})
    header = dict(content.get("header") or {})
    old_storage_key = header.get("_photo_storage_key")
    header["_photo_storage_key"] = storage_key
    header["_photo_mime"] = mime_type
    content["header"] = header
    custom_resume.content = content
    database.commit()
    database.refresh(custom_resume)
    if old_storage_key:
        storage.delete(old_storage_key)
    return _to_view(custom_resume)


@router.delete(
    "/{custom_resume_id}/photo",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def delete_custom_resume_photo(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Response:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    content = dict(custom_resume.content or {})
    header = dict(content.get("header") or {})
    storage_key = header.pop("_photo_storage_key", None)
    header.pop("_photo_mime", None)
    content["header"] = header
    custom_resume.content = content
    database.commit()
    if storage_key:
        get_custom_resume_photo_storage().delete(storage_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{custom_resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin), Depends(require_csrf)],
)
def delete_custom_resume(
    custom_resume_id: int,
    current_user: CurrentUser,
    database: DatabaseSession,
) -> Response:
    custom_resume = _owned_custom_resume(database, current_user.id, custom_resume_id)
    photo_storage_key = ((custom_resume.content or {}).get("header") or {}).get("_photo_storage_key")
    database.delete(custom_resume)
    database.commit()
    if photo_storage_key:
        get_custom_resume_photo_storage().delete(photo_storage_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
