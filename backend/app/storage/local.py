import os
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from app.core.config import get_settings


class LocalResumeStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Invalid storage key")
        return candidate

    def save(self, user_id: int, extension: str, content: bytes) -> str:
        storage_key = f"{user_id}/{uuid4().hex}{extension}"
        destination = self._resolve(storage_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink(missing_ok=True)
        return storage_key

    def path_for(self, storage_key: str) -> Path:
        return self._resolve(storage_key)

    def delete(self, storage_key: str) -> None:
        path = self._resolve(storage_key)
        path.unlink(missing_ok=True)
        try:
            path.parent.rmdir()
        except OSError:
            pass


@lru_cache
def get_resume_storage():
    settings = get_settings()
    if settings.storage_backend == "vercel_blob":
        from app.storage.vercel_blob import VercelBlobResumeStorage

        return VercelBlobResumeStorage("resumes")
    if settings.storage_backend == "database":
        from app.storage.database import DatabaseResumeStorage

        return DatabaseResumeStorage("resumes")
    return LocalResumeStorage(settings.storage_root)
