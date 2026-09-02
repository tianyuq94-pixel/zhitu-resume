from pathlib import Path
from types import SimpleNamespace

import pytest

from app.storage import vercel_blob


class FakeBlobClient:
    def __init__(self) -> None:
        self.saved: tuple[str, bytes] | None = None
        self.deleted: str | None = None

    def put(self, pathname: str, content: bytes, **kwargs):
        assert kwargs["access"] == "private"
        assert kwargs["add_random_suffix"] is False
        self.saved = (pathname, content)
        return SimpleNamespace(pathname=pathname)

    def download_file(self, storage_key: str, destination: Path, **kwargs) -> str:
        assert kwargs["access"] == "private"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"downloaded")
        return str(destination)

    def delete(self, storage_key: str) -> None:
        self.deleted = storage_key


def test_private_blob_storage_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = FakeBlobClient()
    monkeypatch.setattr(vercel_blob, "BlobClient", lambda: client)
    monkeypatch.setattr(vercel_blob, "gettempdir", lambda: str(tmp_path))
    storage = vercel_blob.VercelBlobResumeStorage("resumes")

    storage_key = storage.save(7, ".pdf", b"resume-data")
    downloaded_path = storage.path_for(storage_key)

    assert storage_key.startswith("resumes/7/")
    assert storage_key.endswith(".pdf")
    assert client.saved == (storage_key, b"resume-data")
    assert downloaded_path.read_bytes() == b"downloaded"

    storage.delete(storage_key)
    assert client.deleted == storage_key
    assert not downloaded_path.exists()


def test_blob_storage_rejects_key_outside_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vercel_blob, "BlobClient", FakeBlobClient)
    storage = vercel_blob.VercelBlobResumeStorage("resumes")

    with pytest.raises(ValueError, match="Invalid storage key"):
        storage.path_for("other/7/file.pdf")
