"""Focused behavior tests for EVD-001 evidence metadata."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.evidence.repository as evidence_repository
import app.api.v1.modules.evidence.service as evidence_service
from app.api.v1.modules.evidence.schemas import EvidenceCreateRequest
from app.api.v1.modules.projects import repository as projects_repository
from app.models.citizen_comments import CitizenComment
from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import (
    CitizenIssueReport,
    Claim,
    ClaimSource,
    Project,
    Source,
    SourceRecord,
)

PROJECT_ID = uuid4()
COMMENT_ID = uuid4()
REPORT_ID = uuid4()
EVIDENCE_ID = uuid4()
UPLOADER_ID = uuid4()


def _project(project_id: object = PROJECT_ID) -> Project:
    return Project(
        id=project_id,
        demo_key="evidence-project",
        name="Evidence project",
        description="A project used by EVD-001 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=datetime(2026, 1, 1).date(),
        planned_completion_date=datetime(2026, 12, 31).date(),
    )


def _comment(project_id: object = PROJECT_ID) -> CitizenComment:
    return CitizenComment(
        id=COMMENT_ID,
        project_id=project_id,
        author_id=uuid4(),
        content="A citizen comment with evidence context.",
    )


def _report(project_id: object = PROJECT_ID) -> CitizenIssueReport:
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=project_id,
        category="QUALITY",
        description="A citizen issue report with evidence context.",
    )


def _payload(*, comment_id: object = None) -> EvidenceCreateRequest:
    return EvidenceCreateRequest(
        uploader_id=UPLOADER_ID,
        original_filename="site-photo.png",
        mime_type="image/png",
        file_size_bytes=4096,
        checksum_sha256="a" * 64,
        comment_id=comment_id,
    )


def _evidence(**values: object) -> EvidenceRecord:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": EVIDENCE_ID,
        "project_id": PROJECT_ID,
        "uploader_id": UPLOADER_ID,
        "original_filename": "site-photo.png",
        "mime_type": "image/png",
        "file_size_bytes": 4096,
        "checksum_sha256": "a" * 64,
        "storage_key": "evidence/generated-key",
        "created_at": now,
        "uploaded_at": now,
    }
    defaults.update(values)
    return EvidenceRecord(**defaults)


async def test_create_project_evidence_persists_required_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    create = AsyncMock(side_effect=lambda session, evidence: evidence)
    monkeypatch.setattr(evidence_repository, "create", create)

    response = await evidence_service.create_project_evidence(
        AsyncMock(), PROJECT_ID, _payload()
    )

    stored = create.await_args.args[1]
    assert response.project_id == PROJECT_ID
    assert response.uploader_id == UPLOADER_ID
    assert stored.file_size_bytes == 4096
    assert stored.checksum_sha256 == "a" * 64
    assert stored.storage_key.startswith("evidence/")
    assert stored.storage_key != "site-photo.png"


async def test_create_project_evidence_supports_valid_comment_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        evidence_service.comments_repository,
        "get_comment",
        AsyncMock(return_value=_comment()),
    )
    create = AsyncMock(side_effect=lambda session, evidence: evidence)
    monkeypatch.setattr(evidence_repository, "create", create)

    await evidence_service.create_project_evidence(
        AsyncMock(), PROJECT_ID, _payload(comment_id=COMMENT_ID)
    )

    assert create.await_args.args[1].comment_id == COMMENT_ID
    assert create.await_args.args[1].project_id == PROJECT_ID


async def test_create_report_evidence_supports_valid_report_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    session = AsyncMock()
    session.get.return_value = _report()
    create = AsyncMock(side_effect=lambda session, evidence: evidence)
    monkeypatch.setattr(evidence_repository, "create", create)

    await evidence_service.create_report_evidence(
        session, PROJECT_ID, REPORT_ID, _payload()
    )

    stored = create.await_args.args[1]
    assert stored.report_id == REPORT_ID
    assert stored.project_id == PROJECT_ID


@pytest.mark.parametrize(
    ("operation", "detail"),
    [
        ("project", "Project not found."),
        ("comment", "Comment not found for project."),
        ("report", "Citizen report not found for project."),
    ],
)
async def test_invalid_parent_relationships_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    detail: str,
) -> None:
    session = AsyncMock()
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    if operation == "project":
        call = evidence_service.create_project_evidence(session, PROJECT_ID, _payload())
    elif operation == "comment":
        monkeypatch.setattr(
            projects_repository, "get", AsyncMock(return_value=_project())
        )
        monkeypatch.setattr(
            evidence_service.comments_repository,
            "get_comment",
            AsyncMock(return_value=None),
        )
        call = evidence_service.create_project_evidence(
            session, PROJECT_ID, _payload(comment_id=COMMENT_ID)
        )
    else:
        monkeypatch.setattr(
            projects_repository, "get", AsyncMock(return_value=_project())
        )
        session.get.return_value = None
        call = evidence_service.create_report_evidence(
            session, PROJECT_ID, REPORT_ID, _payload()
        )

    with pytest.raises(HTTPException) as error:
        await call

    assert error.value.status_code == 404
    assert error.value.detail == detail


async def test_relationship_parent_mismatch_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        evidence_service.comments_repository,
        "get_comment",
        AsyncMock(return_value=_comment(project_id=uuid4())),
    )

    with pytest.raises(HTTPException) as error:
        await evidence_service.create_project_evidence(
            AsyncMock(), PROJECT_ID, _payload(comment_id=COMMENT_ID)
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Comment not found for project."


async def test_evidence_response_preserves_trust_and_lifecycle_metadata() -> None:
    evidence = _evidence(
        comment_id=COMMENT_ID,
        source_class=EvidenceSourceClass.CITIZEN_SUBMITTED.value,
        moderation_state=EvidenceModerationState.PENDING.value,
        processing_state=EvidenceProcessingState.RAW.value,
        visibility=EvidenceVisibility.PRIVATE.value,
        is_deleted=True,
    )

    response = evidence_service._response(evidence)

    assert response.source_class is EvidenceSourceClass.CITIZEN_SUBMITTED
    assert response.is_official_source is False
    assert response.trust_label == "CITIZEN_SUBMITTED_EVIDENCE"
    assert response.processing_state is EvidenceProcessingState.RAW
    assert response.moderation_state is EvidenceModerationState.PENDING
    assert response.visibility is EvidenceVisibility.PRIVATE
    assert response.is_deleted is True
    assert response.checksum_sha256 == "a" * 64
    assert response.file_size_bytes == 4096


async def test_evidence_metadata_can_be_retrieved_without_file_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = _evidence()
    monkeypatch.setattr(evidence_repository, "get", AsyncMock(return_value=evidence))

    response = await evidence_service.get_evidence(AsyncMock(), EVIDENCE_ID)

    assert response.id == EVIDENCE_ID
    assert response.storage_key == "evidence/generated-key"
    assert not hasattr(response, "file_content")


def test_evidence_is_separate_from_official_source_models() -> None:
    assert EvidenceRecord.__tablename__ == "evidence_records"
    assert Source.__tablename__ == "sources"
    assert SourceRecord.__tablename__ == "source_records"
    assert Claim.__tablename__ == "claims"
    assert ClaimSource.__tablename__ == "claim_sources"
    assert EvidenceRecord.__tablename__ not in {
        Source.__tablename__,
        SourceRecord.__tablename__,
        Claim.__tablename__,
        ClaimSource.__tablename__,
    }


def test_storage_key_uniqueness_constraint_is_declared() -> None:
    constraint_names = {
        constraint.name for constraint in EvidenceRecord.__table__.constraints
    }
    assert "uq_evidence_records_storage_key" in constraint_names
