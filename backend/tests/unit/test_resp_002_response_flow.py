"""Focused behavior tests for RESP-002 institution responses."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

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


def _report(status: ReportStatus = ReportStatus.SUBMITTED) -> CitizenIssueReport:
    """Build a report fixture containing fields that must remain private."""
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category=ReportCategory.QUALITY.value,
        description="A synthetic RESP-002 report description.",
        contact_information="private@example.test",
        status=status.value,
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _institution(
    institution_id: UUID = INSTITUTION_ID,
    *,
    active: bool = True,
) -> Institution:
    """Build synthetic institution reference data."""
    return Institution(
        id=institution_id,
        code="synthetic-office",
        name="Synthetic Public Office",
        role=InstitutionRole.PUBLIC_AGENCY,
        is_active=active,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _link(
    relationship_type: ReportInstitutionRelationship,
    *,
    link_id: UUID = LINK_ID,
) -> ReportInstitutionLink:
    """Build one synthetic RESP-001 report relationship."""
    return ReportInstitutionLink(
        id=link_id,
        report_id=REPORT_ID,
        institution_id=INSTITUTION_ID,
        relationship_type=relationship_type,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _response(
    link: ReportInstitutionLink,
    *,
    response_id: UUID | None = None,
    content: str = "The institution has reviewed this issue.",
    created_at: datetime = datetime(2026, 1, 2, tzinfo=UTC),
) -> InstitutionResponse:
    """Build one synthetic append-only response."""
    return InstitutionResponse(
        id=response_id or uuid4(),
        report_institution_link_id=link.id,
        content=content,
        created_at=created_at,
    )


async def _prepare_creation(
    monkeypatch: pytest.MonkeyPatch,
    *,
    relationship_type: ReportInstitutionRelationship,
    active: bool = True,
    status: ReportStatus = ReportStatus.SUBMITTED,
) -> tuple[CitizenIssueReport, Institution, ReportInstitutionLink, AsyncMock]:
    """Patch the existing report and RESP-001 repositories for creation tests."""
    report = _report(status)
    institution = _institution(active=active)
    link = _link(relationship_type)
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "get_institution",
        AsyncMock(return_value=institution),
    )
    monkeypatch.setattr(
        reports_repository,
        "get_report_institution_link_for_response",
        AsyncMock(return_value=link),
    )
    create = AsyncMock(side_effect=lambda session, response: response)
    monkeypatch.setattr(reports_repository, "create_institution_response", create)
    return report, institution, link, create


@pytest.mark.parametrize(
    "relationship_type",
    [ReportInstitutionRelationship.ASSIGNED, ReportInstitutionRelationship.REFERRED],
)
async def test_valid_response_creation_uses_existing_link(
    monkeypatch: pytest.MonkeyPatch,
    relationship_type: ReportInstitutionRelationship,
) -> None:
    """Both RESP-001 relationship types can create one response."""
    report, institution, link, create = await _prepare_creation(
        monkeypatch,
        relationship_type=relationship_type,
    )

    response = await reports_service.create_institution_response(
        AsyncMock(), REPORT_ID, institution.id, "  A reviewed response.  "
    )

    assert response.report_institution_link_id == link.id
    assert response.content == "A reviewed response."
    assert response.created_at.tzinfo is not None
    assert report.status == ReportStatus.SUBMITTED.value
    create.assert_awaited_once()


@pytest.mark.parametrize("content", ["", "   ", "x" * 4001])
async def test_invalid_response_content_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    """Empty, whitespace-only, and over-limit content use stable validation."""
    _, institution, _, create = await _prepare_creation(
        monkeypatch,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
    )

    with pytest.raises(HTTPException) as error:
        await reports_service.create_institution_response(
            AsyncMock(), REPORT_ID, institution.id, content
        )

    assert error.value.status_code == 422
    assert error.value.detail == "The institution response is invalid."
    create.assert_not_awaited()


async def test_response_content_accepts_exactly_4000_characters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The approved maximum response length is accepted."""
    _, institution, _, create = await _prepare_creation(
        monkeypatch,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
    )

    response = await reports_service.create_institution_response(
        AsyncMock(), REPORT_ID, institution.id, "x" * 4000
    )

    assert len(response.content) == 4000
    create.assert_awaited_once()


@pytest.mark.parametrize(
    ("report", "institution", "link", "expected_status", "expected_detail"),
    [
        (
            None,
            _institution(),
            _link(ReportInstitutionRelationship.ASSIGNED),
            404,
            "Report not found.",
        ),
        (
            _report(),
            None,
            _link(ReportInstitutionRelationship.ASSIGNED),
            404,
            "Institution not found.",
        ),
        (
            _report(),
            _institution(),
            None,
            409,
            "Institution is not linked to this report.",
        ),
    ],
)
async def test_unknown_report_institution_or_link_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    report: CitizenIssueReport | None,
    institution: Institution | None,
    link: ReportInstitutionLink | None,
    expected_status: int,
    expected_detail: str,
) -> None:
    """Creation validates every ownership reference with safe errors."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "get_institution",
        AsyncMock(return_value=institution),
    )
    monkeypatch.setattr(
        reports_repository,
        "get_report_institution_link_for_response",
        AsyncMock(return_value=link),
    )

    with pytest.raises(HTTPException) as error:
        await reports_service.create_institution_response(
            AsyncMock(), REPORT_ID, INSTITUTION_ID, "A valid response."
        )

    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail


async def test_inactive_institution_cannot_create_new_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inactive institutions cannot create new responses."""
    _, institution, _, create = await _prepare_creation(
        monkeypatch,
        relationship_type=ReportInstitutionRelationship.REFERRED,
        active=False,
    )

    with pytest.raises(HTTPException) as error:
        await reports_service.create_institution_response(
            AsyncMock(), REPORT_ID, institution.id, "A valid response."
        )

    assert error.value.status_code == 422
    assert error.value.detail == "Institution is inactive."
    create.assert_not_awaited()


async def test_multiple_duplicate_responses_are_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same report-institution link can receive multiple responses."""
    report, institution, link, create = await _prepare_creation(
        monkeypatch,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
    )

    first = await reports_service.create_institution_response(
        AsyncMock(), REPORT_ID, institution.id, "The first response."
    )
    second = await reports_service.create_institution_response(
        AsyncMock(), REPORT_ID, institution.id, "The first response."
    )

    assert first.report_institution_link_id == link.id
    assert second.report_institution_link_id == link.id
    assert first.content == second.content
    assert report.status == ReportStatus.SUBMITTED.value
    assert create.await_count == 2


async def test_response_creation_does_not_change_status_history_or_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Creation preserves report status, status history behavior, and evidence."""
    report, institution, _, _ = await _prepare_creation(
        monkeypatch,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
        status=ReportStatus.CLOSED,
    )
    evidence = EvidenceRecord(
        report_id=REPORT_ID,
        uploader_id=uuid4(),
        original_filename="synthetic.pdf",
        mime_type="application/pdf",
        file_size_bytes=10,
        checksum_sha256="a" * 64,
        storage_key="synthetic/report-evidence.pdf",
    )
    update_status = AsyncMock()
    monkeypatch.setattr(reports_repository, "update_status", update_status)

    await reports_service.create_institution_response(
        AsyncMock(), REPORT_ID, institution.id, "A response after closure."
    )

    assert report.status == ReportStatus.CLOSED.value
    assert evidence.report_id == REPORT_ID
    assert evidence.processing_state == "RAW"
    update_status.assert_not_awaited()


async def test_public_response_lookup_is_ordered_and_private_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public reads expose only approved fields in deterministic order."""
    report = _report()
    institution = _institution()
    link = _link(ReportInstitutionRelationship.REFERRED)
    late = _response(
        link,
        response_id=UUID("00000000-0000-0000-0000-000000000002"),
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    early = _response(
        link,
        response_id=UUID("00000000-0000-0000-0000-000000000001"),
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_institution_responses",
        AsyncMock(return_value=[(late, link, institution), (early, link, institution)]),
    )

    result = await reports_service.get_report_responses(AsyncMock(), REPORT_ID)

    assert [item.response_id for item in result] == [early.id, late.id]
    assert result[0].institution_id == institution.id
    assert result[0].institution_name == institution.name
    assert result[0].institution_role is institution.role
    assert result[0].relationship_type is link.relationship_type
    assert result[0].content == early.content
    assert set(result[0].model_dump()) == {
        "response_id",
        "institution_id",
        "institution_name",
        "institution_role",
        "relationship_type",
        "content",
        "created_at",
    }
    assert institution.code not in result[0].model_dump_json()
    assert "private@example.test" not in result[0].model_dump_json()
    assert "synthetic RESP-002 report description" not in result[0].model_dump_json()


async def test_empty_and_unknown_public_response_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Known reports return an empty list and unknown reports use stable 404."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=_report()))
    monkeypatch.setattr(
        reports_repository,
        "list_institution_responses",
        AsyncMock(return_value=[]),
    )
    assert await reports_service.get_report_responses(AsyncMock(), REPORT_ID) == []

    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=None))
    with pytest.raises(HTTPException) as error:
        await reports_service.get_report_responses(AsyncMock(), REPORT_ID)
    assert error.value.status_code == 404
    assert error.value.detail == "Report not found."


def test_response_model_contract_and_public_route() -> None:
    """The model has only approved fields and the API exposes GET only."""
    assert set(InstitutionResponse.__table__.columns.keys()) == {
        "id",
        "report_institution_link_id",
        "content",
        "created_at",
    }
    assert "status" not in InstitutionResponse.__table__.columns
    assert "visibility" not in InstitutionResponse.__table__.columns
    constraint_names = {
        constraint.name for constraint in InstitutionResponse.__table__.constraints
    }
    assert "ck_institution_responses_content" in constraint_names
    route = next(
        route
        for route in reports_routes.report_router.routes
        if route.path == "/reports/{report_id}/responses"
    )
    assert route.methods == {"GET"}


def test_resp002_keeps_resp001_civic_and_evidence_boundaries() -> None:
    """RESP-002 remains separate from links, channels, and citizen evidence."""
    assert ReportInstitutionLink.__tablename__ == "report_institution_links"
    assert ReportingChannel.__tablename__ == "reporting_channels"
    assert EvidenceRecord.__tablename__ == "evidence_records"
    assert not hasattr(CitizenIssueReport, "institution_response_id")


def test_invalid_response_model_content_is_rejected() -> None:
    """The persistence model rejects invalid content through validation APIs."""
    with pytest.raises(ValidationError):
        InstitutionResponse.model_validate(
            {
                "report_institution_link_id": LINK_ID,
                "content": "   ",
            }
        )
    with pytest.raises(ValidationError):
        InstitutionResponse.model_validate(
            {
                "report_institution_link_id": LINK_ID,
                "content": "x" * 4001,
            }
        )
