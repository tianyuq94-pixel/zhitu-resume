from functools import lru_cache

import pymupdf

from app.core.config import get_settings
from app.storage.local import LocalResumeStorage
from app.storage.vercel_blob import VercelBlobResumeStorage


class ResumePhotoError(ValueError):
    pass


def validate_resume_photo(content: bytes, declared_mime_type: str | None) -> tuple[str, str]:
    settings = get_settings()
    if not content or len(content) > settings.resume_photo_max_bytes:
        raise ResumePhotoError("证件照不能超过 2 MB")

    mime = (declared_mime_type or "").lower().split(";", maxsplit=1)[0].strip()
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        actual_mime, extension, filetype = "image/png", ".png", "png"
    elif content.startswith(b"\xff\xd8\xff"):
        actual_mime, extension, filetype = "image/jpeg", ".jpg", "jpeg"
    else:
        raise ResumePhotoError("证件照只支持 JPG 或 PNG 图片")
    if mime not in {"", "application/octet-stream", actual_mime}:
        raise ResumePhotoError("图片类型与文件内容不一致")

    try:
        with pymupdf.open(stream=content, filetype=filetype) as document:
            if document.page_count != 1:
                raise ResumePhotoError("证件照文件结构异常")
            rect = document[0].rect
            if rect.width < 40 or rect.height < 40 or rect.width > 10_000 or rect.height > 10_000:
                raise ResumePhotoError("证件照尺寸不合适")
    except ResumePhotoError:
        raise
    except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
        raise ResumePhotoError("证件照文件损坏或无法读取") from exc
    return actual_mime, extension


@lru_cache
def get_custom_resume_photo_storage():
    settings = get_settings()
    if settings.storage_backend == "vercel_blob":
        return VercelBlobResumeStorage("custom-resume-photos")
    if settings.storage_backend == "database":
        from app.storage.database import DatabaseResumeStorage

        return DatabaseResumeStorage("custom-resume-photos")
    return LocalResumeStorage(settings.storage_root.parent / "custom-resume-photos")
