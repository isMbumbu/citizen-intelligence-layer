"""Focused behavior tests for RESP-003 report comparison."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.civic_action.repository as reports_repository
import app.api.v1.modules.civic_action.routes as reports_routes
import app.api.v1.modules.civic_action.service as reports_service
from app.models.enums import (
    InstitutionRole,
    ReportCategory,
    ReportInstitutionRelationship,
    ReportStatus,
)
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import (
    CitizenIssueReport,
    Institution,
    InstitutionResponse,
    ReportingChannel,
    ReportInstitutionLink,
)

REPORT_ID = uuid4()
PROJECT_ID = uuid4()
INSTITUTION_ID = uuid4()
LINK_ID = uuid4()


def _report(status: ReportStatus = ReportStatus.CLOSED) -> CitizenIssueReport:
    """Build a synthetic citizen issue containing private contact data."""
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category=ReportCategory.QUALITY.value,
        description="The citizen-submitted issue to compare.",
        contact_information="private@example.test",
        status=status.value,
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _institution() -> Institution:
    """Build a synthetic public institution fixture."""
    return Institution(
        id=INSTITUTION_ID,
        code="synthetic-office",
        name="Synthetic Public Office",
        role=InstitutionRole.PUBLIC_AGENCY,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _link() -> ReportInstitutionLink:
    """Build the existing RESP-001 relationship fixture."""
    return ReportInstitutionLink(
        id=LINK_ID,
        report_id=REPORT_ID,
        institution_id=INSTITUTION_ID,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _response(
    link: ReportInstitutionLink,
    response_id: UUID,
    created_at: datetime,
    content: str,
) -> InstitutionResponse:
    """Build an existing RESP-002 response fixture."""
    return InstitutionResponse(
        id=response_id,
        report_institution_link_id=link.id,
        content=content,
        created_at=created_at,
    )


async def test_comparison_returns_separate_issue_and_ordered_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public comparison preserves issue/response origins and ordering."""
    report = _report()
    institution = _institution()
    link = _link()
    late = _response(
        link,
        UUID("00000000-0000-0000-0000-000000000002"),
        datetime(2026, 1, 3, tzinfo=UTC),
        "A later institutional clarification.",
    )
    early = _response(
        link,
        UUID("00000000-0000-0000-0000-000000000001"),
        datetime(2026, 1, 2, tzinfo=UTC),
        "An earlier institutional clarification.",
    )
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_institution_responses",
        AsyncMock(return_value=[(late, link, institution), (early, link, institution)]),
    )

    comparison = await reports_service.get_report_comparison(AsyncMock(), REPORT_ID)

    assert comparison.issue.report_id == REPORT_ID
    assert comparison.issue.category is ReportCategory.QUALITY
    assert comparison.issue.description == report.description
    assert comparison.issue.submitted_at == report.submitted_at
    assert [item.response_id for item in comparison.responses] == [early.id, late.id]
    assert comparison.responses[0].content == early.content
    assert comparison.responses[0].institution_id == institution.id
    assert comparison.responses[0].relationship_type is link.relationship_type


def test_comparison_contract_contains_only_approved_public_fields() -> None:
    """The comparison schemas expose only the approved issue/response fields."""
    from app.api.v1.modules.civic_action.schemas import (
        ReportComparisonResponse,
        ReportIssueComparisonResponse,
    )

    assert set(ReportIssueComparisonResponse.model_fields) == {
        "report_id",
        "category",
        "description",
        "submitted_at",
    }
    assert set(ReportComparisonResponse.model_fields) == {"issue", "responses"}
    assert set(InstitutionResponse.__table__.columns.keys()) == {
        "id",
        "report_institution_link_id",
        "content",
        "created_at",
    }
    assert "status" not in InstitutionResponse.__table__.columns
    assert "visibility" not in InstitutionResponse.__table__.columns


async def test_comparison_privacy_excludes_contact_and_internal_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Private report and institution fields are absent from public output."""
    report = _report()
    institution = _institution()
    link = _link()
    response = _response(
        link,
        uuid4(),
        datetime(2026, 1, 2, tzinfo=UTC),
        "A public institutional clarification.",
    )
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_institution_responses",
        AsyncMock(return_value=[(response, link, institution)]),
    )

    comparison = await reports_service.get_report_comparison(AsyncMock(), REPORT_ID)
    payload = comparison.model_dump_json()

    assert report.description in payload
    assert report.contact_information not in payload
    assert institution.code not in payload
    assert "actor" not in payload
    assert "request" not in payload
    assert "credentials" not in payload
    assert "internal_notes" not in payload
    assert "evidence" not in payload
    assert "storage_key" not in payload


async def test_empty_comparison_returns_empty_response_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A known report without institutional responses returns an empty list."""
    report = _report()
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_institution_responses",
        AsyncMock(return_value=[]),
    )

    comparison = await reports_service.get_report_comparison(AsyncMock(), REPORT_ID)

    assert comparison.issue.report_id == REPORT_ID
    assert comparison.responses == []


async def test_unknown_comparison_report_uses_stable_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown comparison reports use the existing safe 404 contract."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=None))
    list_responses = AsyncMock()
    monkeypatch.setattr(
        reports_repository, "list_institution_responses", list_responses
    )

    with pytest.raises(HTTPException) as error:
        await reports_service.get_report_comparison(AsyncMock(), REPORT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Report not found."
    list_responses.assert_not_awaited()


async def test_comparison_preserves_report_response_evidence_and_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Comparison is read-only across report, response, evidence, and status."""
    report = _report(ReportStatus.CLOSED)
    institution = _institution()
    link = _link()
    response = _response(
        link,
        uuid4(),
        datetime(2026, 1, 2, tzinfo=UTC),
        "An existing institutional response.",
    )
    evidence = EvidenceRecord(
        report_id=REPORT_ID,
        uploader_id=uuid4(),
        original_filename="synthetic.pdf",
        mime_type="application/pdf",
        file_size_bytes=10,
        checksum_sha256="a" * 64,
        storage_key="synthetic/report.pdf",
    )
    update_status = AsyncMock()
    list_channels = AsyncMock()
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_institution_responses",
        AsyncMock(return_value=[(response, link, institution)]),
    )
    monkeypatch.setattr(reports_repository, "update_status", update_status)
    monkeypatch.setattr(reports_repository, "list_matching_channels", list_channels)

    comparison = await reports_service.get_report_comparison(AsyncMock(), REPORT_ID)

    assert report.status == ReportStatus.CLOSED.value
    assert report.description == "The citizen-submitted issue to compare."
    assert response.content == "An existing institutional response."
    assert evidence.report_id == REPORT_ID
    assert evidence.processing_state == "RAW"
    assert comparison.responses[0].response_id == response.id
    update_status.assert_not_awaited()
    list_channels.assert_not_awaited()


def test_comparison_route_is_public_read_only_and_report_scoped() -> None:
    """RESP-003 adds only a report-scoped GET route."""
    route = next(
        route
        for route in reports_routes.report_router.routes
        if route.path == "/reports/{report_id}/comparison"
    )
    assert route.methods == {"GET"}


def test_resp003_preserves_existing_resp_and_civic_models() -> None:
    """No new reply entity or competing relationship model is introduced."""
    assert ReportInstitutionLink.__tablename__ == "report_institution_links"
    assert InstitutionResponse.__tablename__ == "institution_responses"
    assert ReportingChannel.__tablename__ == "reporting_channels"
    assert EvidenceRecord.__tablename__ == "evidence_records"
    assert not hasattr(CitizenIssueReport, "comparison_id")
