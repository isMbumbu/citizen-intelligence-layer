"""Focused tests for EVD-005: browsing public evidence without identifiers."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

import app.api.v1.modules.evidence.repository as evidence_repository
import app.api.v1.modules.evidence.service as evidence_service
from app.api.v1.modules.evidence.schemas import PublicEvidenceItem
from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.evidence import EvidenceRecord

PROJECT_ID = uuid4()
UPLOADER_ID = uuid4()


def _record(**overrides: Any) -> EvidenceRecord:
    values: dict[str, Any] = {
        "id": uuid4(),
        "project_id": PROJECT_ID,
        "uploader_id": UPLOADER_ID,
        "source_class": EvidenceSourceClass.CITIZEN_SUBMITTED.value,
        "original_filename": "jane-doe-house.jpg",
        "mime_type": "image/jpeg",
        "file_size_bytes": 10,
        "checksum_sha256": "a" * 64,
        "storage_key": "evidence/secret.jpg",
        "moderation_state": EvidenceModerationState.PENDING.value,
        "processing_state": EvidenceProcessingState.RAW.value,
        "visibility": EvidenceVisibility.PUBLIC.value,
        "uploaded_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return EvidenceRecord(**values)


async def test_browse_maps_context_and_hides_identifying_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    on_report = _record(report_id=uuid4())
    flagged_pdf = _record(
        mime_type="application/pdf",
        moderation_state=EvidenceModerationState.FLAGGED.value,
    )
    private = _record(visibility=EvidenceVisibility.PRIVATE.value)
    rows = [
        (record, "Synthetic Project", "Garissa", "Health")
        for record in (on_report, flagged_pdf, private)
    ]
    browse = AsyncMock(return_value=(rows, 3))
    monkeypatch.setattr(evidence_repository, "browse_public", browse)

    page = await evidence_service.browse_public_evidence(
        AsyncMock(),
        project_id=None,
        category_id=None,
        county="Garissa",
        kind=None,
        page=2,
        page_size=10,
    )

    assert [item.id for item in page.items] == [on_report.id, flagged_pdf.id]
    first, second = page.items
    assert (first.attached_to, first.kind, first.review_status) == (
        "report",
        "image",
        "NOT_YET_REVIEWED",
    )
    assert (second.attached_to, second.kind, second.review_status) == (
        "project",
        "document",
        "UNDER_REVIEW",
    )
    dumped = page.model_dump_json()
    for secret in (str(UPLOADER_ID), "jane-doe-house", "a" * 64, "evidence/secret"):
        assert secret not in dumped
    assert browse.await_args is not None
    assert browse.await_args.kwargs["offset"] == 10


def test_public_evidence_item_has_no_identifying_fields() -> None:
    fields = set(PublicEvidenceItem.model_fields)
    assert not fields & {
        "uploader_id",
        "original_filename",
        "checksum_sha256",
        "storage_key",
        "moderation_state",
    }


async def test_browse_query_joins_project_context_and_filters() -> None:
    statements: list[Any] = []

    class FakeResult:
        def all(self) -> list[Any]:
            return []

        def one(self) -> int:
            return 0

    class FakeSession:
        async def exec(self, statement: Any) -> FakeResult:
            statements.append(statement)
            return FakeResult()

    await evidence_repository.browse_public(
        FakeSession(),  # type: ignore[arg-type]
        project_id=None,
        category_id=uuid4(),
        county="Garissa",
        kind="document",
        offset=0,
        limit=24,
    )

    page_sql, count_sql = (
        str(statement.compile(dialect=postgresql.dialect())) for statement in statements
    )
    for sql in (page_sql, count_sql):
        assert "JOIN projects ON evidence_records.project_id = projects.id" in sql
        assert "JOIN counties ON sub_counties.county_id = counties.id" in sql
        assert "evidence_records.visibility" in sql
        assert "lower(counties.name)" in sql
        assert "evidence_records.mime_type NOT LIKE" in sql
    assert "ORDER BY evidence_records.uploaded_at DESC" in page_sql
