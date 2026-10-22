"""Focused tests for EVD-004: citizen images are public and metadata-free."""

import asyncio
import hashlib
from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import UploadFile
from PIL import Image, PngImagePlugin
from sqlalchemy.dialects import postgresql
from starlette.datastructures import Headers

import app.api.v1.modules.evidence.repository as evidence_repository
import app.api.v1.modules.evidence.service as evidence_service
from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import Project

PROJECT_ID = uuid4()
UPLOADER_ID = uuid4()
GPS_IFD = 0x8825
ORIENTATION = 0x0112


class FakeStorage:
    def __init__(self) -> None:
        self.stored: dict[str, bytes] = {}

    async def store(self, source_path: Path, storage_key: str) -> None:
        self.stored[storage_key] = await asyncio.to_thread(source_path.read_bytes)

    async def delete(self, storage_key: str) -> None:
        self.stored.pop(storage_key, None)


def _project() -> Project:
    return Project(
        id=PROJECT_ID,
        demo_key="evd-004-project",
        name="EVD-004 project",
        description="A project used by EVD-004 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2026, 1, 1),
        planned_completion_date=date(2026, 12, 31),
    )


def _jpeg_with_gps_and_rotation() -> bytes:
    """A 4x2 photo tagged 'rotate 90°' with GPS coordinates and a camera model."""
    exif = Image.Exif()
    exif[ORIENTATION] = 6
    exif[0x0110] = "Synthetic Phone"
    exif.get_ifd(GPS_IFD).update({1: "S", 2: (1.0, 17.0, 0.0)})
    buffer = BytesIO()
    Image.new("RGB", (4, 2), color="blue").save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def _png_with_text_chunk() -> bytes:
    info = PngImagePlugin.PngInfo()
    info.add_text("Author", "Private Citizen")
    buffer = BytesIO()
    Image.new("RGB", (2, 2), color="green").save(buffer, format="PNG", pnginfo=info)
    return buffer.getvalue()


def _upload(content: bytes, filename: str, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


async def _store(
    monkeypatch: pytest.MonkeyPatch, upload: UploadFile
) -> tuple[Any, bytes]:
    storage = FakeStorage()
    monkeypatch.setattr(evidence_service, "get_evidence_storage", lambda: storage)
    monkeypatch.setattr(
        evidence_service.projects_repository,
        "get",
        AsyncMock(return_value=_project()),
    )
    monkeypatch.setattr(
        evidence_repository,
        "create",
        AsyncMock(side_effect=lambda session, evidence: evidence),
    )
    response = await evidence_service.upload_project_evidence(
        object(), PROJECT_ID, UPLOADER_ID, None, upload
    )
    return response, next(iter(storage.stored.values()))


async def test_jpeg_upload_drops_gps_and_keeps_orientation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _jpeg_with_gps_and_rotation()
    with Image.open(BytesIO(original)) as source:
        assert source.getexif().get_ifd(GPS_IFD)

    response, stored = await _store(
        monkeypatch, _upload(original, "site.jpg", "image/jpeg")
    )

    with Image.open(BytesIO(stored)) as cleaned:
        assert not cleaned.getexif()
        assert "exif" not in cleaned.info
        assert cleaned.size == (2, 4)
    assert response.visibility is EvidenceVisibility.PUBLIC
    assert response.file_size_bytes == len(stored)
    assert response.checksum_sha256 == hashlib.sha256(stored).hexdigest()


async def test_png_upload_drops_text_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, stored = await _store(
        monkeypatch, _upload(_png_with_text_chunk(), "site.png", "image/png")
    )

    with Image.open(BytesIO(stored)) as cleaned:
        assert "Author" not in cleaned.info
    assert b"Private Citizen" not in stored


def _record(**overrides: Any) -> EvidenceRecord:
    values: dict[str, Any] = {
        "id": uuid4(),
        "project_id": PROJECT_ID,
        "uploader_id": UPLOADER_ID,
        "source_class": EvidenceSourceClass.CITIZEN_SUBMITTED.value,
        "original_filename": "site.png",
        "mime_type": "image/png",
        "file_size_bytes": 10,
        "checksum_sha256": "0" * 64,
        "storage_key": "evidence/x.png",
        "moderation_state": EvidenceModerationState.PENDING.value,
        "processing_state": EvidenceProcessingState.RAW.value,
        "visibility": EvidenceVisibility.PUBLIC.value,
        "uploaded_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return EvidenceRecord(**values)


async def test_public_list_excludes_private_hidden_and_deleted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    visible = _record()
    records = [
        visible,
        _record(visibility=EvidenceVisibility.PRIVATE.value),
        _record(moderation_state=EvidenceModerationState.HIDDEN.value),
        _record(is_deleted=True),
    ]
    monkeypatch.setattr(
        evidence_repository, "list_public", AsyncMock(return_value=records)
    )

    listed = await evidence_service.list_public_evidence(
        AsyncMock(), project_id=PROJECT_ID
    )

    assert [item.id for item in listed] == [visible.id]


async def test_list_public_query_filters_visibility_and_target() -> None:
    statements: list[Any] = []

    class FakeResult:
        def all(self) -> list[Any]:
            return []

    class FakeSession:
        async def exec(self, statement: Any) -> FakeResult:
            statements.append(statement)
            return FakeResult()

    await evidence_repository.list_public(
        FakeSession(),  # type: ignore[arg-type]
        project_id=None,
        report_id=uuid4(),
        comment_id=None,
    )

    sql = str(statements[0].compile(dialect=postgresql.dialect()))
    assert "evidence_records.visibility" in sql
    assert "evidence_records.moderation_state NOT IN" in sql
    assert "evidence_records.report_id" in sql
    assert "evidence_records.project_id" not in sql.split("WHERE", 1)[1]
