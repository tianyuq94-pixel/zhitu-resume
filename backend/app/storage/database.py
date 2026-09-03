from hashlib import sha256
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.stored_file import StoredFile


class DatabaseResumeStorage:
    """Persistent private file storage for hosts with ephemeral disks."""

    def __init__(self, namespace: str) -> None:
        clean_namespace = namespace.strip("/ ")
        if not clean_namespace or "/" in clean_namespace or "\\" in clean_namespace:
            raise ValueError("Invalid storage namespace")
        self.namespace = clean_namespace
        self.cache_root = Path(gettempdir()) / "zhitu-resume-database-cache"

    def _validate_key(self, storage_key: str) -> None:
        expected_prefix = f"{self.namespace}/"
        if not storage_key.startswith(expected_prefix) or ".." in Path(storage_key).parts:
            raise ValueError("Invalid storage key")

    def _cache_path(self, storage_key: str) -> Path:
        suffix = Path(storage_key).suffix
        cache_name = f"{sha256(storage_key.encode('utf-8')).hexdigest()}{suffix}"
        return self.cache_root / cache_name

    def save(self, user_id: int, extension: str, content: bytes) -> str:
        storage_key = f"{self.namespace}/{user_id}/{uuid4().hex}{extension}"
        with SessionLocal() as database:
            database.add(
                StoredFile(
                    storage_key=storage_key,
                    owner_user_id=user_id,
                    content=content,
                    size_bytes=len(content),
                )
            )
            database.commit()
        return storage_key

    def path_for(self, storage_key: str) -> Path:
        self._validate_key(storage_key)
        cache_path = self._cache_path(storage_key)
        if cache_path.is_file():
            return cache_path
        with SessionLocal() as database:
            stored_file = database.get(StoredFile, storage_key)
            if stored_file is None:
                return cache_path
            content = stored_file.content
        self.cache_root.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)
        return cache_path

    def delete(self, storage_key: str) -> None:
        self._validate_key(storage_key)
        with SessionLocal() as database:
            stored_file = database.get(StoredFile, storage_key)
            if stored_file is not None:
                database.delete(stored_file)
                database.commit()
        self._cache_path(storage_key).unlink(missing_ok=True)
