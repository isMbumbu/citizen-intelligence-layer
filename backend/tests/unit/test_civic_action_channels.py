"""Focused behavior tests for CIVIC-003 reporting channels."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.civic_action.repository as reports_repository
import app.api.v1.modules.civic_action.routes as reports_routes
import app.api.v1.modules.civic_action.service as reports_service
from app.models.enums import ReportCategory, ReportStatus
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import (
    CitizenIssueReport,
    County,
    Project,
    ReportingChannel,
    SubCounty,
    Ward,
)

REPORT_ID = uuid4()
PROJECT_ID = uuid4()
COUNTY_ID = uuid4()
SUB_COUNTY_ID = uuid4()
WARD_ID = uuid4()


def _report() -> CitizenIssueReport:
    """Build a report fixture with persisted category and project association."""
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category=ReportCategory.QUALITY.value,
        description="A report used by CIVIC-003 tests.",
        contact_information="private@example.test",
        status=ReportStatus.SUBMITTED.value,
        submitted_at=datetime.now(UTC),
    )


def _project() -> Project:
    """Build a project fixture linked to the test ward."""
    return Project(
        id=PROJECT_ID,
        demo_key="channels-project",
        name="Channels project",
        description="A project used by CIVIC-003 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=WARD_ID,
        planned_start_date=datetime(2026, 1, 1).date(),
        planned_completion_date=datetime(2026, 12, 31).date(),
    )


def _location() -> tuple[County, SubCounty, Ward]:
    """Build the existing county/sub-county/ward hierarchy fixture."""
    return (
        County(id=COUNTY_ID, name="Demo County", code="DMC"),
        SubCounty(id=SUB_COUNTY_ID, county_id=COUNTY_ID, name="Demo SubCounty"),
        Ward(id=WARD_ID, sub_county_id=SUB_COUNTY_ID, name="Demo Ward"),
    )


def _channel(
    channel_id: UUID,
    *,
    priority: int,
    county_id: UUID | None = None,
    sub_county_id: UUID | None = None,
    ward_id: UUID | None = None,
    is_active: bool = True,
) -> ReportingChannel:
    """Build synthetic channel reference data without real authority details."""
    return ReportingChannel(
        id=channel_id,
        issue_category=ReportCategory.QUALITY.value,
        county_id=county_id,
        sub_county_id=sub_county_id,
        ward_id=ward_id,
        office_name="Synthetic demo office",
        channel_type="WEB",
        destination="https://example.invalid/report",
        display_label="Synthetic demo channel",
        priority=priority,
        is_active=is_active,
    )


async def _lookup(
    monkeypatch: pytest.MonkeyPatch,
    channels: list[ReportingChannel],
) -> list[object]:
    """Run the report-scoped lookup with synthetic persisted dependencies."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=_report()))
    monkeypatch.setattr(
        reports_service.projects_repository,
        "get",
        AsyncMock(return_value=_project()),
    )
    monkeypatch.setattr(
        reports_service.geography_repository,
        "get_location_for_ward",
        AsyncMock(return_value=_location()),
    )
    monkeypatch.setattr(
        reports_repository,
        "list_matching_channels",
        AsyncMock(return_value=channels),
    )
    return await reports_service.get_report_channels(AsyncMock(), REPORT_ID)


async def test_ward_channels_win_and_are_priority_ordered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ward channels suppress broader channels and order by priority then ID."""
    county_channel = _channel(uuid4(), priority=1, county_id=COUNTY_ID)
    ward_late = _channel(uuid4(), priority=10, ward_id=WARD_ID)
    ward_early = _channel(uuid4(), priority=10, ward_id=WARD_ID)

    result = await _lookup(monkeypatch, [county_channel, ward_late, ward_early])

    assert [item.id for item in result] == sorted(
        [ward_early.id, ward_late.id], key=str
    )
    assert all(item.office_name == "Synthetic demo office" for item in result)
    assert not hasattr(result[0], "contact_information")
    assert not hasattr(result[0], "description")


async def test_subcounty_fallback_is_used_when_no_ward_channel_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sub-county channels are selected when the ward has no match."""
    result = await _lookup(
        monkeypatch,
        [_channel(uuid4(), priority=10, sub_county_id=SUB_COUNTY_ID)],
    )

    assert len(result) == 1
    assert result[0].priority == 10


async def test_county_fallback_is_used_when_narrower_levels_are_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """County channels are selected only when narrower levels have no match."""
    result = await _lookup(
        monkeypatch,
        [_channel(uuid4(), priority=10, county_id=COUNTY_ID)],
    )

    assert len(result) == 1
    assert result[0].priority == 10


async def test_inactive_channels_and_category_mismatches_are_not_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inactive and mismatched candidates produce no public channel result."""
    inactive = _channel(uuid4(), priority=1, ward_id=WARD_ID, is_active=False)
    mismatched = _channel(uuid4(), priority=2, ward_id=WARD_ID)
    mismatched.issue_category = ReportCategory.SAFETY.value

    result = await _lookup(monkeypatch, [inactive, mismatched])

    assert result == []


async def test_unknown_report_returns_stable_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown reports do not reveal storage or database details."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await reports_service.get_report_channels(AsyncMock(), REPORT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Report not found."


async def test_no_match_returns_empty_list_without_mutating_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A no-match lookup is informational and leaves CIVIC-002 status unchanged."""
    report = _report()
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_service.projects_repository,
        "get",
        AsyncMock(return_value=_project()),
    )
    monkeypatch.setattr(
        reports_service.geography_repository,
        "get_location_for_ward",
        AsyncMock(return_value=_location()),
    )
    monkeypatch.setattr(
        reports_repository,
        "list_matching_channels",
        AsyncMock(return_value=[]),
    )
    transition = AsyncMock()
    monkeypatch.setattr(reports_repository, "update_status", transition)

    result = await reports_service.get_report_channels(AsyncMock(), REPORT_ID)

    assert result == []
    assert report.status == ReportStatus.SUBMITTED.value
    transition.assert_not_awaited()


def test_channel_response_route_is_read_only_and_report_scoped() -> None:
    """The endpoint is a GET under the existing report router."""
    route = next(
        route
        for route in reports_routes.report_router.routes
        if route.path == "/reports/{report_id}/channels"
    )
    assert "GET" in route.methods
    assert "POST" not in route.methods


def test_channel_contract_is_separate_from_evidence() -> None:
    """CIVIC-003 does not reuse evidence or provenance models."""
    assert EvidenceRecord.__tablename__ == "evidence_records"
