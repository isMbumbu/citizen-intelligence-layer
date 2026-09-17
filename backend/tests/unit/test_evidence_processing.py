"""Focused tests for the EVD-003 evidence processing boundary."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

import app.api.v1.modules.evidence.repository as repository
import app.api.v1.modules.evidence.service as service
from app.models.enums import EvidenceProcessingState
from app.models.evidence import EvidenceRecord


class FailingStorage:
    """Storage double that fails without exposing file content."""

    async def read(self, storage_key: str, max_bytes: int) -> bytes:
        raise OSError("parser failure with sensitive details")


def _evidence(**values: object) -> EvidenceRecord:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "project_id": uuid4(),
        "uploader_id": uuid4(),
        "original_filename": "evidence.png",
        "mime_type": "image/png",
        "file_size_bytes": 10,
        "checksum_sha256": "a" * 64,
        "storage_key": "evidence/object",
        "uploaded_at": datetime.now(UTC),
    }
    defaults.update(values)
    return EvidenceRecord(**defaults)


async def test_valid_lifecycle_transitions_are_audited() -> None:
    evidence = _evidence()
    session = AsyncMock()
    session.add = Mock()

    validation = await service.transition_processing_state(
        session,
        evidence,
        EvidenceProcessingState.VALIDATION_PASSED,
        event_type="VALIDATION",
    )
    extracted = await service.transition_processing_state(
        session,
        evidence,
        EvidenceProcessingState.EXTRACTED,
        event_type="EXTRACTION",
    )
    indexed = await service.transition_processing_state(
        session,
        evidence,
        EvidenceProcessingState.INDEXED,
        event_type="INDEXING",
    )

    assert validation.from_state == EvidenceProcessingState.RAW.value
    assert extracted.from_state == EvidenceProcessingState.VALIDATION_PASSED.value
    assert indexed.from_state == EvidenceProcessingState.EXTRACTED.value
    assert evidence.processing_state == EvidenceProcessingState.INDEXED.value
    assert session.flush.await_count == 3


async def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid evidence processing transition"):
        await service.transition_processing_state(
            AsyncMock(),
            _evidence(),
            EvidenceProcessingState.INDEXED,
            event_type="INDEXING",
        )


async def test_processing_failure_is_bounded_and_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence()
    monkeypatch.setattr(repository, "get", AsyncMock(return_value=evidence))
    monkeypatch.setattr(repository, "create_processing_event", AsyncMock())
    session = AsyncMock()

    with pytest.raises(OSError):
        await service.process_evidence(session, evidence.id, storage=FailingStorage())

    failure = repository.create_processing_event.await_args.args[1]
    assert evidence.processing_state == EvidenceProcessingState.FAILED.value
    assert failure.error_code == "PROCESSING_FAILED"
    assert failure.error_message == "Evidence processing could not be completed."
    assert "parser failure" not in (failure.error_message or "")


async def test_duplicate_processing_after_extraction_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence(processing_state=EvidenceProcessingState.EXTRACTED.value)
    monkeypatch.setattr(repository, "get", AsyncMock(return_value=evidence))
    create_event = AsyncMock()
    monkeypatch.setattr(repository, "create_processing_event", create_event)

    state = await service.process_evidence(AsyncMock(), evidence.id)

    assert state is EvidenceProcessingState.EXTRACTED
    create_event.assert_not_awaited()
