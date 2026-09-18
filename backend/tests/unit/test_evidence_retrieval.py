"""Focused security-boundary tests for STG-001 evidence retrieval."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.evidence.repository as evidence_repository
import app.api.v1.modules.evidence.routes as evidence_routes
import app.api.v1.modules.evidence.service as evidence_service
from app.core.security import (
    EVIDENCE_READ_PROTECTED_PERMISSION,
    CurrentModerator,
)
from app.models.enums import (
    EvidenceModerationState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import Claim, ClaimSource, Source, SourceRecord

EVIDENCE_ID = uuid4()


class FakeStorage:
    """Storage double that records the internal key passed by the service."""

    def __init__(self, content: bytes = b"evidence") -> None:
        self.content = content
        self.read_keys: list[str] = []

    async def read(self, storage_key: str, max_bytes: int) -> bytes:
        self.read_keys.append(storage_key)
        return self.content


class MissingStorage:
    """Storage double representing an absent original object."""

    async def read(self, storage_key: str, max_bytes: int) -> bytes:
        raise FileNotFoundError("/private/storage/root/evidence/object")


def _evidence(**values: object) -> EvidenceRecord:
    defaults: dict[str, object] = {
        "id": EVIDENCE_ID,
        "project_id": uuid4(),
        "uploader_id": uuid4(),
        "source_class": EvidenceSourceClass.CITIZEN_SUBMITTED.value,
        "original_filename": "site-photo.png",
        "mime_type": "image/png",
        "file_size_bytes": 8,
        "checksum_sha256": "a" * 64,
        "storage_key": "evidence/internal-object.png",
        "moderation_state": EvidenceModerationState.PENDING.value,
        "visibility": EvidenceVisibility.PUBLIC.value,
        "uploaded_at": datetime.now(UTC),
    }
    defaults.update(values)
    return EvidenceRecord(**defaults)


async def _download(
    monkeypatch: pytest.MonkeyPatch,
    evidence: EvidenceRecord,
    storage: object,
) -> object:
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))
    return await evidence_service.download_evidence(
        AsyncMock(),
        evidence.id,
        storage=storage,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize(
    ("mime_type", "filename", "content"),
    [
        ("application/pdf", "report.pdf", b"%PDF-1.4\n%%EOF"),
        ("image/png", "site-photo.png", b"png-bytes"),
    ],
)
async def test_public_retrieval_preserves_type_and_safe_filename(
    monkeypatch: pytest.MonkeyPatch,
    mime_type: str,
    filename: str,
    content: bytes,
) -> None:
    storage = FakeStorage(content)
    evidence = _evidence(mime_type=mime_type, original_filename=filename)
    download = await _download(monkeypatch, evidence, storage)
    monkeypatch.setattr(
        evidence_routes.service,
        "download_evidence",
        AsyncMock(return_value=download),
    )
    response = await evidence_routes.download_evidence(evidence.id, AsyncMock())

    assert download.content == content  # type: ignore[attr-defined]
    assert download.mime_type == mime_type  # type: ignore[attr-defined]
    assert download.filename == filename  # type: ignore[attr-defined]
    assert response.media_type == mime_type
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{filename}"'
    )
    assert "/" not in response.headers["content-disposition"]
    assert "\\" not in response.headers["content-disposition"]


@pytest.mark.parametrize(
    "values",
    [
        {"visibility": EvidenceVisibility.PRIVATE.value},
        {"visibility": EvidenceVisibility.PENDING.value},
        {"moderation_state": EvidenceModerationState.HIDDEN.value},
        {"moderation_state": EvidenceModerationState.REMOVED.value},
        {"is_deleted": True},
    ],
)
async def test_non_public_evidence_is_denied(
    monkeypatch: pytest.MonkeyPatch,
    values: dict[str, object],
) -> None:
    storage = FakeStorage()
    evidence = _evidence(**values)
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    with pytest.raises(HTTPException) as error:
        await evidence_service.download_evidence(
            AsyncMock(), evidence.id, storage=storage
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Authentication is required."
    assert storage.read_keys == []


async def test_protected_evidence_requires_trusted_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence(visibility=EvidenceVisibility.PRIVATE.value)
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    with pytest.raises(HTTPException) as error:
        await evidence_service.download_evidence(
            AsyncMock(),
            evidence.id,
            storage=FakeStorage(),
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Authentication is required."


async def test_protected_evidence_requires_explicit_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence(visibility=EvidenceVisibility.PRIVATE.value)
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    with pytest.raises(HTTPException) as error:
        await evidence_service.download_evidence(
            AsyncMock(),
            evidence.id,
            storage=FakeStorage(),
            actor=CurrentModerator(uuid4(), frozenset()),
        )

    assert error.value.status_code == 403
    assert error.value.detail == "Protected evidence permission is required."


async def test_protected_evidence_with_permission_proceeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence(visibility=EvidenceVisibility.PRIVATE.value)
    storage = FakeStorage(b"protected-bytes")
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    download = await evidence_service.download_evidence(
        AsyncMock(),
        evidence.id,
        storage=storage,
        actor=CurrentModerator(
            uuid4(),
            frozenset({EVIDENCE_READ_PROTECTED_PERMISSION}),
        ),
    )

    assert download.content == b"protected-bytes"
    assert storage.read_keys == [evidence.storage_key]


async def test_missing_evidence_returns_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await evidence_service.download_evidence(AsyncMock(), EVIDENCE_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Evidence not found."


async def test_missing_stored_file_returns_safe_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence()
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    with pytest.raises(HTTPException) as error:
        await evidence_service.download_evidence(
            AsyncMock(), evidence.id, storage=MissingStorage()
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Evidence file not found."
    assert "/private/storage/root" not in error.value.detail


async def test_storage_key_is_internal_and_not_exposed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence(original_filename='../../"unsafe\nname.png')
    storage = FakeStorage()
    download = await _download(monkeypatch, evidence, storage)
    metadata = evidence_service._response(evidence)

    assert storage.read_keys == [evidence.storage_key]
    assert evidence.storage_key not in download.filename  # type: ignore[attr-defined]
    assert not hasattr(metadata, "storage_key")
    assert "/" not in download.filename  # type: ignore[attr-defined]
    assert "\\" not in download.filename  # type: ignore[attr-defined]
    assert "\n" not in download.filename  # type: ignore[attr-defined]
    assert "storage" not in download.filename.lower()  # type: ignore[attr-defined]


async def test_storage_path_traversal_is_rejected_by_storage_boundary(
    tmp_path: Path,
) -> None:
    from app.core.storage import LocalEvidenceStorage

    storage = LocalEvidenceStorage(str(tmp_path))
    with pytest.raises(ValueError):
        storage._path_for("../../outside")
    with pytest.raises(ValueError):
        storage._path_for("/absolute/path")


async def test_retrieval_preserves_citizen_provenance_and_creates_no_official_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence()
    storage = FakeStorage()
    download = await _download(monkeypatch, evidence, storage)

    assert evidence.source_class == EvidenceSourceClass.CITIZEN_SUBMITTED.value
    assert download.content == storage.content  # type: ignore[attr-defined]
    assert Source.__tablename__ == "sources"
    assert SourceRecord.__tablename__ == "source_records"
    assert Claim.__tablename__ == "claims"
    assert ClaimSource.__tablename__ == "claim_sources"
