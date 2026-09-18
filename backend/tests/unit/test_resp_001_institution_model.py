"""Focused behavior tests for RESP-001 institution relationships."""

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
from app.models.vertical_slice import (
    CitizenIssueReport,
    Institution,
    ReportingChannel,
    ReportInstitutionLink,
)

REPORT_ID = uuid4()
PROJECT_ID = uuid4()
INSTITUTION_ID = uuid4()


def _report(status: ReportStatus = ReportStatus.SUBMITTED) -> CitizenIssueReport:
    """Build a report fixture containing private fields that must stay hidden."""
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category=ReportCategory.QUALITY.value,
        description="A synthetic RESP-001 report description.",
        contact_information="private@example.test",
        status=status.value,
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _institution(
    institution_id: UUID = INSTITUTION_ID,
    *,
    active: bool = True,
    code: str = "county-works",
) -> Institution:
    """Build synthetic institution reference data without production details."""
    return Institution(
        id=institution_id,
        code=code,
        name="Synthetic County Works Office",
        role=InstitutionRole.COUNTY_GOVERNMENT,
        is_active=active,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _link(
    institution: Institution,
    *,
    relationship_type: ReportInstitutionRelationship,
    created_at: datetime,
    link_id: UUID | None = None,
) -> tuple[ReportInstitutionLink, Institution]:
    """Build one synthetic relationship joined to its institution."""
    return (
        ReportInstitutionLink(
            id=link_id or uuid4(),
            report_id=REPORT_ID,
            institution_id=institution.id,
            relationship_type=relationship_type,
            created_at=created_at,
        ),
        institution,
    )


async def test_institution_normalizes_valid_data_and_rejects_invalid_role() -> None:
    """Institution codes and names normalize while roles remain controlled."""
    direct_institution = Institution(
        code="  county-works  ",
        name="  Synthetic County Works Office  ",
        role=InstitutionRole.COUNTY_GOVERNMENT,
    )
    assert direct_institution.code == "COUNTY-WORKS"
    assert direct_institution.name == "Synthetic County Works Office"

    institution = Institution.model_validate(
        {
            "code": "  county-works  ",
            "name": "  Synthetic County Works Office  ",
            "role": "COUNTY_GOVERNMENT",
        }
    )

    assert institution.code == "COUNTY-WORKS"
    assert institution.name == "Synthetic County Works Office"
    assert institution.role is InstitutionRole.COUNTY_GOVERNMENT
    assert set(InstitutionRole) == {
        InstitutionRole.COUNTY_GOVERNMENT,
        InstitutionRole.NATIONAL_GOVERNMENT,
        InstitutionRole.PUBLIC_AGENCY,
    }
    with pytest.raises(ValidationError):
        Institution.model_validate(
            {
                "code": "unknown",
                "name": "Unknown institution",
                "role": "PRIVATE_COMPANY",
            }
        )


def test_institution_and_link_constraints_are_registered() -> None:
    """Persistence metadata contains the approved uniqueness constraints."""
    institution_constraints = {
        constraint.name for constraint in Institution.__table__.constraints
    }
    link_constraints = {
        constraint.name for constraint in ReportInstitutionLink.__table__.constraints
    }

    assert "uq_institutions_code" in institution_constraints
    assert "uq_report_institution_relationship" in link_constraints
    assert ReportInstitutionLink.report_id.property.columns[0].index is True
    assert ReportInstitutionLink.institution_id.property.columns[0].index is True


@pytest.mark.parametrize(
    "relationship_type",
    [ReportInstitutionRelationship.ASSIGNED, ReportInstitutionRelationship.REFERRED],
)
async def test_valid_assignment_and_referral_persist_one_link(
    monkeypatch: pytest.MonkeyPatch,
    relationship_type: ReportInstitutionRelationship,
) -> None:
    """Both approved relationship types persist without changing report state."""
    report = _report()
    institution = _institution()
    persisted: list[ReportInstitutionLink] = []
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "get_institution",
        AsyncMock(return_value=institution),
    )
    monkeypatch.setattr(
        reports_repository,
        "get_report_institution_link",
        AsyncMock(return_value=None),
    )
    update_status = AsyncMock()
    monkeypatch.setattr(reports_repository, "update_status", update_status)

    async def persist(
        session: object,
        link: ReportInstitutionLink,
    ) -> ReportInstitutionLink:
        persisted.append(link)
        return link

    monkeypatch.setattr(
        reports_repository,
        "create_report_institution_link",
        persist,
    )

    result = await reports_service.link_report_to_institution(
        AsyncMock(), REPORT_ID, INSTITUTION_ID, relationship_type
    )

    assert result.relationship_type is relationship_type
    assert len(persisted) == 1
    assert report.status == ReportStatus.SUBMITTED.value
    update_status.assert_not_awaited()


async def test_multiple_institutions_are_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A report can receive separate relationships to multiple institutions."""
    report = _report()
    first = _institution()
    second = _institution(uuid4(), code="national-works")
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "get_institution",
        AsyncMock(side_effect=[first, second]),
    )
    monkeypatch.setattr(
        reports_repository,
        "get_report_institution_link",
        AsyncMock(return_value=None),
    )
    persisted: list[ReportInstitutionLink] = []
    monkeypatch.setattr(
        reports_repository,
        "create_report_institution_link",
        AsyncMock(side_effect=lambda session, link: persisted.append(link) or link),
    )

    await reports_service.link_report_to_institution(
        AsyncMock(), REPORT_ID, first.id, ReportInstitutionRelationship.ASSIGNED
    )
    await reports_service.link_report_to_institution(
        AsyncMock(), REPORT_ID, second.id, ReportInstitutionRelationship.REFERRED
    )

    assert [link.institution_id for link in persisted] == [first.id, second.id]


async def test_duplicate_relationship_is_rejected_without_persisting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate report/institution/type relationships return a stable conflict."""
    existing = ReportInstitutionLink(
        report_id=REPORT_ID,
        institution_id=INSTITUTION_ID,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
    )
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=_report()))
    monkeypatch.setattr(
        reports_repository,
        "get_institution",
        AsyncMock(return_value=_institution()),
    )
    monkeypatch.setattr(
        reports_repository,
        "get_report_institution_link",
        AsyncMock(return_value=existing),
    )
    create = AsyncMock()
    monkeypatch.setattr(reports_repository, "create_report_institution_link", create)

    with pytest.raises(HTTPException) as error:
        await reports_service.link_report_to_institution(
            AsyncMock(),
            REPORT_ID,
            INSTITUTION_ID,
            ReportInstitutionRelationship.ASSIGNED,
        )

    assert error.value.status_code == 409
    assert error.value.detail == "Report is already linked to this institution."
    create.assert_not_awaited()


@pytest.mark.parametrize(
    ("report", "institution", "expected_status", "expected_detail"),
    [
        (None, _institution(), 404, "Report not found."),
        (_report(), None, 404, "Institution not found."),
        (_report(), _institution(active=False), 422, "Institution is inactive."),
    ],
)
async def test_unknown_or_inactive_relationship_targets_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    report: CitizenIssueReport | None,
    institution: Institution | None,
    expected_status: int,
    expected_detail: str,
) -> None:
    """Report and institution references use stable safe errors."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "get_institution",
        AsyncMock(return_value=institution),
    )

    with pytest.raises(HTTPException) as error:
        await reports_service.link_report_to_institution(
            AsyncMock(),
            REPORT_ID,
            INSTITUTION_ID,
            ReportInstitutionRelationship.ASSIGNED,
        )

    assert error.value.status_code == expected_status
    assert error.value.detail == expected_detail


async def test_empty_and_ordered_public_relationship_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Relationship reads are deterministic and empty reports return an empty list."""
    report = _report()
    first = _institution(code="first")
    second = _institution(uuid4(), code="second")
    first_link = _link(
        first,
        relationship_type=ReportInstitutionRelationship.REFERRED,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    second_link = _link(
        second,
        relationship_type=ReportInstitutionRelationship.ASSIGNED,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_report_institution_links",
        AsyncMock(return_value=[first_link, second_link]),
    )

    result = await reports_service.get_report_institutions(AsyncMock(), REPORT_ID)

    assert [item.institution_id for item in result] == [second.id, first.id]
    assert result[0].institution_name == second.name
    assert result[0].institution_role is InstitutionRole.COUNTY_GOVERNMENT
    assert result[0].relationship_type is ReportInstitutionRelationship.ASSIGNED
    assert not hasattr(result[0], "code")
    assert not hasattr(result[0], "description")
    assert not hasattr(result[0], "contact_information")

    monkeypatch.setattr(
        reports_repository,
        "list_report_institution_links",
        AsyncMock(return_value=[]),
    )
    assert await reports_service.get_report_institutions(AsyncMock(), REPORT_ID) == []


async def test_unknown_report_lookup_uses_existing_not_found_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Public relationship lookup preserves the CIVIC-002 not-found contract."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await reports_service.get_report_institutions(AsyncMock(), REPORT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Report not found."


def test_institution_endpoint_is_read_only_and_report_scoped() -> None:
    """RESP-001 exposes only a GET endpoint under the existing report router."""
    route = next(
        route
        for route in reports_routes.report_router.routes
        if route.path == "/reports/{report_id}/institutions"
    )
    assert "GET" in route.methods
    assert "POST" not in route.methods


def test_resp001_does_not_reuse_channels_or_add_report_institution_id() -> None:
    """Institution links remain separate from reports and reporting channels."""
    assert ReportingChannel.__tablename__ == "reporting_channels"
    assert not hasattr(CitizenIssueReport, "institution_id")
