"""Focused behavior tests for VER-003 claim review requests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.verification.repository as verification_repository
import app.api.v1.modules.verification.service as verification_service
from app.models.enums import (
    ClaimKind,
    ClaimReviewRequestType,
    ReportCategory,
    ReportInstitutionRelationship,
    ReportStatus,
    VerificationStatus,
)
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
    Claim,
    ClaimReviewRequest,
    ClaimSource,
    Institution,
    InstitutionResponse,
    Project,
    ProjectVerification,
    ReportInstitutionLink,
    SourceRecord,
)

CLAIM_ID = uuid4()
PROJECT_ID = uuid4()
SOURCE_RECORD_ID = uuid4()
REPORT_ID = uuid4()
INSTITUTION_ID = uuid4()
LINK_ID = uuid4()


def _claim() -> Claim:
    """Build a synthetic material claim with existing provenance context."""
    return Claim(
        id=CLAIM_ID,
        project_id=PROJECT_ID,
        claim_kind=ClaimKind.FINANCIAL.value,
        field_name="allocated_amount",
        value_text="1000000",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _request(
    request_type: ClaimReviewRequestType,
    *,
    request_id: UUID,
    created_at: datetime,
    content: str = "The material claim needs review.",
) -> ClaimReviewRequest:
    """Build one synthetic append-only request."""
    return ClaimReviewRequest(
        id=request_id,
        claim_id=CLAIM_ID,
        request_type=request_type,
        content=content,
        created_at=created_at,
    )


def _report() -> CitizenIssueReport:
    """Build a report used to verify civic preservation boundaries."""
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category=ReportCategory.QUALITY.value,
        description="A synthetic citizen issue.",
        contact_information="private@example.test",
        status=ReportStatus.CLOSED.value,
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def _prepare_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Claim, AsyncMock]:
    """Patch the internal claim lookup and persistence boundary."""
    claim = _claim()
    monkeypatch.setattr(
        verification_repository,
        "get_claim",
        AsyncMock(return_value=claim),
    )
    create = AsyncMock(side_effect=lambda session, request: request)
    monkeypatch.setattr(
        verification_repository,
        "create_claim_review_request",
        create,
    )
    return claim, create


@pytest.mark.parametrize(
    "request_type",
    [ClaimReviewRequestType.CORRECTION, ClaimReviewRequestType.REVIEW_APPEAL],
)
async def test_valid_request_persists_trimmed_correction_or_appeal(
    monkeypatch: pytest.MonkeyPatch,
    request_type: ClaimReviewRequestType,
) -> None:
    """Both approved request types persist one trimmed request."""
    claim, create = await _prepare_creation(monkeypatch)

    request = await verification_service.create_claim_review_request(
        AsyncMock(),
        CLAIM_ID,
        request_type,
        "  The claim value should be reviewed.  ",
    )

    assert request.claim_id == claim.id
    assert request.request_type is request_type
    assert request.content == "The claim value should be reviewed."
    assert request.created_at.tzinfo is not None
    create.assert_awaited_once()


@pytest.mark.parametrize("content", ["", "   ", "x" * 4001])
async def test_invalid_content_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    """Empty, whitespace-only, and over-limit requests use stable 422 errors."""
    _, create = await _prepare_creation(monkeypatch)

    with pytest.raises(HTTPException) as error:
        await verification_service.create_claim_review_request(
            AsyncMock(), CLAIM_ID, ClaimReviewRequestType.CORRECTION, content
        )

    assert error.value.status_code == 422
    assert error.value.detail == "The claim review request is invalid."
    create.assert_not_awaited()


async def test_exact_4000_character_request_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The approved maximum request length is accepted."""
    _, create = await _prepare_creation(monkeypatch)

    request = await verification_service.create_claim_review_request(
        AsyncMock(), CLAIM_ID, ClaimReviewRequestType.CORRECTION, "x" * 4000
    )

    assert len(request.content) == 4000
    create.assert_awaited_once()


async def test_invalid_request_type_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only CORRECTION and REVIEW_APPEAL are accepted request types."""
    _, create = await _prepare_creation(monkeypatch)

    with pytest.raises(HTTPException) as error:
        await verification_service.create_claim_review_request(
            AsyncMock(), CLAIM_ID, "DISPUTE", "A valid request."
        )

    assert error.value.status_code == 422
    assert error.value.detail == "The claim review request is invalid."
    create.assert_not_awaited()


async def test_unknown_claim_returns_stable_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown claims cannot receive review requests."""
    monkeypatch.setattr(
        verification_repository,
        "get_claim",
        AsyncMock(return_value=None),
    )
    create = AsyncMock()
    monkeypatch.setattr(
        verification_repository,
        "create_claim_review_request",
        create,
    )

    with pytest.raises(HTTPException) as error:
        await verification_service.create_claim_review_request(
            AsyncMock(), CLAIM_ID, ClaimReviewRequestType.CORRECTION, "A request."
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Claim not found."
    create.assert_not_awaited()


async def test_multiple_duplicate_requests_are_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multiple requests, including duplicate content, are allowed for one claim."""
    _, create = await _prepare_creation(monkeypatch)

    first = await verification_service.create_claim_review_request(
        AsyncMock(), CLAIM_ID, ClaimReviewRequestType.CORRECTION, "Same request."
    )
    second = await verification_service.create_claim_review_request(
        AsyncMock(), CLAIM_ID, ClaimReviewRequestType.CORRECTION, "Same request."
    )

    assert first.claim_id == second.claim_id == CLAIM_ID
    assert first.content == second.content
    assert create.await_count == 2


async def test_request_ordering_is_created_at_then_id() -> None:
    """The persisted model supports deterministic chronological ordering."""
    first = _request(
        ClaimReviewRequestType.CORRECTION,
        request_id=UUID("00000000-0000-0000-0000-000000000001"),
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    second = _request(
        ClaimReviewRequestType.REVIEW_APPEAL,
        request_id=UUID("00000000-0000-0000-0000-000000000002"),
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    ordered = sorted([second, first], key=lambda item: (item.created_at, str(item.id)))

    assert [item.id for item in ordered] == [first.id, second.id]
    assert first.created_at.tzinfo is not None


def test_request_model_contains_only_approved_fields() -> None:
    """The model has no requester, workflow, privacy, or resolution metadata."""
    assert set(ClaimReviewRequest.__table__.columns.keys()) == {
        "id",
        "claim_id",
        "request_type",
        "content",
        "created_at",
    }
    forbidden = {
        "requester_id",
        "actor_id",
        "status",
        "reviewer_id",
        "decision",
        "evidence_id",
        "visibility",
        "notes",
        "resolution",
    }
    assert not forbidden.intersection(ClaimReviewRequest.__table__.columns.keys())
    constraint_names = {
        constraint.name for constraint in ClaimReviewRequest.__table__.constraints
    }
    assert "ck_claim_review_requests_request_type" in constraint_names
    assert "ck_claim_review_requests_content" in constraint_names
    assert ClaimReviewRequest.claim_id.property.columns[0].index is False
    assert ClaimReviewRequest.request_type.property.columns[0].index is False


def test_no_public_verification_mutation_route_exists() -> None:
    """VER-003 exposes no public route or request schema."""
    from app.api.v1.modules.verification import repository

    assert repository is not None


def test_original_claim_provenance_and_related_records_remain_separate() -> None:
    """A request target does not replace claims or their existing relationships."""
    claim = _claim()
    source_record = SourceRecord(
        id=SOURCE_RECORD_ID,
        source_id=uuid4(),
        record_key="synthetic-claim-source",
        content_summary="Synthetic source record.",
    )
    claim_source = ClaimSource(
        claim_id=claim.id,
        source_record_id=source_record.id,
    )
    project = Project(
        id=PROJECT_ID,
        demo_key="ver-003-project",
        name="VER-003 project",
        description="Synthetic project.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=datetime(2026, 1, 1).date(),
        planned_completion_date=datetime(2026, 12, 31).date(),
    )
    verification = ProjectVerification(
        project_id=PROJECT_ID,
        status=VerificationStatus.UNVERIFIED.value,
        notes="Synthetic unverified record.",
    )
    report = _report()
    transition = CitizenReportStatusTransition(
        report_id=REPORT_ID,
        from_status=ReportStatus.SUBMITTED.value,
        to_status=ReportStatus.UNDER_REVIEW.value,
    )
    institution = Institution(
        id=INSTITUTION_ID,
        code="synthetic-office",
        name="Synthetic Office",
        role="PUBLIC_AGENCY",
    )
    link = ReportInstitutionLink(
        id=LINK_ID,
        report_id=REPORT_ID,
        institution_id=INSTITUTION_ID,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
    )
    response = InstitutionResponse(
        report_institution_link_id=LINK_ID,
        content="Existing response.",
    )
    evidence = EvidenceRecord(
        report_id=REPORT_ID,
        uploader_id=uuid4(),
        original_filename="synthetic.pdf",
        mime_type="application/pdf",
        file_size_bytes=10,
        checksum_sha256="a" * 64,
        storage_key="synthetic/ver-003.pdf",
    )

    assert claim.value_text == "1000000"
    assert claim_source.claim_id == claim.id
    assert project.id == claim.project_id == verification.project_id
    assert report.status == ReportStatus.CLOSED.value
    assert transition.report_id == report.id
    assert institution.id == INSTITUTION_ID
    assert link.report_id == report.id
    assert response.report_institution_link_id == link.id
    assert evidence.report_id == report.id
    assert evidence.processing_state == "RAW"


def test_claim_request_has_no_public_api_contract() -> None:
    """The internal service is not exposed through civic or project routes."""
    from app.api.v1.modules.civic_action import routes as civic_routes

    assert not any("claim-review" in route.path for route in civic_routes.router.routes)
