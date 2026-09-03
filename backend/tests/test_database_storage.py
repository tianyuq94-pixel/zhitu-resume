from pathlib import Path

import pytest

from app.storage.database import DatabaseResumeStorage


class FakeDatabase:
    def __init__(self, records: dict[str, object]) -> None:
        self.records = records

    def __enter__(self) -> "FakeDatabase":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def add(self, record: object) -> None:
        self.records[record.storage_key] = record  # type: ignore[attr-defined]

    def get(self, _model: object, storage_key: str) -> object | None:
        return self.records.get(storage_key)

    def delete(self, record: object) -> None:
        self.records.pop(record.storage_key, None)  # type: ignore[attr-defined]

    def commit(self) -> None:
        return None


def test_database_storage_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    records: dict[str, object] = {}
    monkeypatch.setattr(
        "app.storage.database.SessionLocal",
        lambda: FakeDatabase(records),
    )
    storage = DatabaseResumeStorage("resumes")
    storage.cache_root = tmp_path

    storage_key = storage.save(7, ".pdf", b"example-pdf")

    assert storage_key.startswith("resumes/7/")
    assert storage.path_for(storage_key).read_bytes() == b"example-pdf"

    storage.delete(storage_key)
    assert storage_key not in records
    assert not storage.path_for(storage_key).exists()


def test_database_storage_rejects_key_from_another_namespace(tmp_path: Path) -> None:
    storage = DatabaseResumeStorage("resumes")
    storage.cache_root = tmp_path

    with pytest.raises(ValueError, match="Invalid storage key"):
        storage.path_for("custom-resume-photos/7/photo.jpg")
