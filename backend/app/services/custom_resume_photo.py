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
        raise ResumePhotoError("ID photo must not exceed 2 MB")

    mime = (declared_mime_type or "").lower().split(";", maxsplit=1)[0].strip()
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        actual_mime, extension, filetype = "image/png", ".png", "png"
    elif content.startswith(b"\xff\xd8\xff"):
        actual_mime, extension, filetype = "image/jpeg", ".jpg", "jpeg"
    else:
        raise ResumePhotoError("ID photo only supports JPG or PNG images")
    if mime not in {"", "application/octet-stream", actual_mime}:
        raise ResumePhotoError("Image type does not match file content")

    try:
        with pymupdf.open(stream=content, filetype=filetype) as document:
            if document.page_count != 1:
                raise ResumePhotoError("ID photo file structure is abnormal")
            rect = document[0].rect
            if rect.width < 40 or rect.height < 40 or rect.width > 10_000 or rect.height > 10_000:
                raise ResumePhotoError("ID photo dimensions are unsuitable")
    except ResumePhotoError:
        raise
    except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
        raise ResumePhotoError("ID photo file is corrupted or unreadable") from exc
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
