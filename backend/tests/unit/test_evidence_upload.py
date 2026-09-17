"""Focused security-boundary tests for EVD-002 evidence uploads."""

import asyncio
import hashlib
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image
from starlette.datastructures import Headers

import app.api.v1.modules.evidence.repository as evidence_repository
import app.api.v1.modules.evidence.service as evidence_service
from app.core import config
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import CitizenIssueReport, Project

PROJECT_ID = uuid4()
REPORT_ID = uuid4()
UPLOADER_ID = uuid4()


def _png_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (2, 2), color="red")
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


def _upload(
    content: bytes,
    *,
    filename: str = "photo.png",
    content_type: str = "image/png",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def _project() -> Project:
    return Project(
        id=PROJECT_ID,
        demo_key="upload-project",
        name="Upload project",
        description="A project used by EVD-002 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2026, 1, 1),
        planned_completion_date=date(2026, 12, 31),
    )


class FakeStorage:
    def __init__(self, *, fail_store: bool = False) -> None:
        self.fail_store = fail_store
        self.stored: dict[str, bytes] = {}
        self.deleted: list[str] = []

    async def store(self, source_path: Path, storage_key: str) -> None:
        self.stored[storage_key] = await asyncio.to_thread(source_path.read_bytes)
        if self.fail_store:
            raise OSError("storage failed")

    async def delete(self, storage_key: str) -> None:
        self.deleted.append(storage_key)
        self.stored.pop(storage_key, None)


async def _prepare_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        evidence_service.projects_repository,
        "get",
        AsyncMock(return_value=_project()),
    )
    monkeypatch.setattr(
        evidence_service,
        "get_evidence_storage",
        lambda: FakeStorage(),
    )


async def test_valid_png_upload_generates_metadata_and_storage_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _prepare_project(monkeypatch)
    storage = FakeStorage()
    monkeypatch.setattr(evidence_service, "get_evidence_storage", lambda: storage)
    created: list[EvidenceRecord] = []

    async def create(session: object, evidence: EvidenceRecord) -> EvidenceRecord:
        created.append(evidence)
        return evidence

    monkeypatch.setattr(evidence_repository, "create", create)
    content = _png_bytes()

    response = await evidence_service.upload_project_evidence(
        object(), PROJECT_ID, UPLOADER_ID, None, _upload(content)
    )

    assert len(created) == 1
    assert response.mime_type == "image/png"
    assert response.file_size_bytes == len(content)
    assert response.checksum_sha256 == hashlib.sha256(content).hexdigest()
    assert response.storage_key.startswith("evidence/")
    assert response.storage_key.endswith(".png")
    assert "photo.png" not in response.storage_key
    assert storage.stored[response.storage_key] == content


async def test_valid_pdf_upload_supports_report_association(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _prepare_project(monkeypatch)
    storage = FakeStorage()
    monkeypatch.setattr(evidence_service, "get_evidence_storage", lambda: storage)
    monkeypatch.setattr(
        evidence_service,
        "get_evidence_storage",
        lambda: storage,
    )
    session = AsyncMock()
    session.get.return_value = _report()
    monkeypatch.setattr(
        evidence_repository,
        "create",
        AsyncMock(side_effect=lambda session, evidence: evidence),
    )

    response = await evidence_service.upload_report_evidence_by_id(
        session,
        REPORT_ID,
        UPLOADER_ID,
        _upload(_pdf_bytes(), filename="report.pdf", content_type="application/pdf"),
    )

    assert response.report_id == REPORT_ID
    assert response.mime_type == "application/pdf"
    assert response.storage_key.endswith(".pdf")


def _report() -> CitizenIssueReport:
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category="QUALITY",
        description="A report used by EVD-002 tests.",
    )


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "detail"),
    [
        ("photo.exe", "application/octet-stream", b"MZ executable", "extension"),
        ("photo.png", "image/png", b"not an image", "malformed"),
        ("photo.jpg", "image/jpeg", _png_bytes(), "content"),
        ("photo.pdf", "application/pdf", b"%PDF-1.4\nnot complete", "malformed"),
        (
            "photo.pdf",
            "application/pdf",
            b"%PDF-1.4\n/JavaScript\n%%EOF",
            "malformed",
        ),
        ("photo.png", "application/x-msdownload", _png_bytes(), "MIME"),
    ],
)
async def test_invalid_uploads_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    content_type: str,
    content: bytes,
    detail: str,
) -> None:
    await _prepare_project(monkeypatch)

    with pytest.raises(HTTPException) as error:
        await evidence_service.upload_project_evidence(
            object(),
            PROJECT_ID,
            UPLOADER_ID,
            None,
            _upload(content, filename=filename, content_type=content_type),
        )

    assert error.value.status_code == 422
    assert detail.lower() in error.value.detail.lower()


async def test_oversized_upload_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    await _prepare_project(monkeypatch)
    monkeypatch.setattr(config.settings, "evidence_max_size_bytes", 3)

    with pytest.raises(HTTPException) as error:
        await evidence_service.upload_project_evidence(
            AsyncMock(), PROJECT_ID, UPLOADER_ID, None, _upload(_png_bytes())
        )

    assert error.value.status_code == 422
    assert "maximum size" in error.value.detail


async def test_filename_is_sanitized_and_never_used_as_storage_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _prepare_project(monkeypatch)
    storage = FakeStorage()
    monkeypatch.setattr(evidence_service, "get_evidence_storage", lambda: storage)
    monkeypatch.setattr(
        evidence_repository,
        "create",
        AsyncMock(side_effect=lambda session, evidence: evidence),
    )

    response = await evidence_service.upload_project_evidence(
        object(),
        PROJECT_ID,
        UPLOADER_ID,
        None,
        _upload(_png_bytes(), filename="../../dangerous name.png"),
    )

    assert response.original_filename == "dangerous_name.png"
    assert response.storage_key != response.original_filename
    assert ".." not in response.storage_key


async def test_storage_failure_does_not_persist_metadata_or_leave_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _prepare_project(monkeypatch)
    storage = FakeStorage(fail_store=True)
    monkeypatch.setattr(evidence_service, "get_evidence_storage", lambda: storage)
    create = AsyncMock()
    monkeypatch.setattr(evidence_repository, "create", create)

    with pytest.raises(HTTPException) as error:
        await evidence_service.upload_project_evidence(
            AsyncMock(), PROJECT_ID, UPLOADER_ID, None, _upload(_png_bytes())
        )

    assert error.value.status_code == 500
    assert not create.mock_calls
    assert len(storage.deleted) == 1
    assert not storage.stored


async def test_persistence_failure_cleans_up_stored_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _prepare_project(monkeypatch)
    storage = FakeStorage()
    monkeypatch.setattr(evidence_service, "get_evidence_storage", lambda: storage)

    async def fail_create(session: object, evidence: EvidenceRecord) -> EvidenceRecord:
        raise RuntimeError("database failed")

    monkeypatch.setattr(evidence_repository, "create", fail_create)

    with pytest.raises(HTTPException) as error:
        await evidence_service.upload_project_evidence(
            AsyncMock(), PROJECT_ID, UPLOADER_ID, None, _upload(_png_bytes())
        )

    assert error.value.status_code == 500
    assert len(storage.deleted) == 1
    assert not storage.stored


async def test_storage_rejects_path_traversal_keys(tmp_path: Path) -> None:
    from app.core.storage import LocalEvidenceStorage

    storage = LocalEvidenceStorage(str(tmp_path))
    with pytest.raises(ValueError):
        storage._path_for("../outside")
    with pytest.raises(ValueError):
        storage._path_for("/absolute/path")
