from hashlib import sha256
from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from vercel.blob import BlobClient, BlobNotFoundError


class VercelBlobResumeStorage:
    """Private persistent storage for serverless deployments."""

    def __init__(self, namespace: str) -> None:
        clean_namespace = namespace.strip("/ ")
        if not clean_namespace or "/" in clean_namespace or "\\" in clean_namespace:
            raise ValueError("Invalid storage namespace")
        self.namespace = clean_namespace
        self.client = BlobClient()
        self.cache_root = Path(gettempdir()) / "zhitu-resume-blob-cache"

    def save(self, user_id: int, extension: str, content: bytes) -> str:
        pathname = f"{self.namespace}/{user_id}/{uuid4().hex}{extension}"
        result = self.client.put(
            pathname,
            content,
            access="private",
            add_random_suffix=False,
            overwrite=False,
        )
        return result.pathname

    def path_for(self, storage_key: str) -> Path:
        expected_prefix = f"{self.namespace}/"
        if not storage_key.startswith(expected_prefix) or ".." in Path(storage_key).parts:
            raise ValueError("Invalid storage key")
        suffix = Path(storage_key).suffix
        cache_name = f"{sha256(storage_key.encode('utf-8')).hexdigest()}{suffix}"
        cache_path = self.cache_root / cache_name
        if cache_path.is_file():
            return cache_path
        try:
            self.client.download_file(
                storage_key,
                cache_path,
                access="private",
                overwrite=True,
                create_parents=True,
            )
        except BlobNotFoundError:
            cache_path.unlink(missing_ok=True)
        return cache_path

    def delete(self, storage_key: str) -> None:
        expected_prefix = f"{self.namespace}/"
        if not storage_key.startswith(expected_prefix) or ".." in Path(storage_key).parts:
            raise ValueError("Invalid storage key")
        try:
            self.client.delete(storage_key)
        except BlobNotFoundError:
            pass
        suffix = Path(storage_key).suffix
        cache_name = f"{sha256(storage_key.encode('utf-8')).hexdigest()}{suffix}"
        (self.cache_root / cache_name).unlink(missing_ok=True)
