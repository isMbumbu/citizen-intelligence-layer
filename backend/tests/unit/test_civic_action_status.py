"""Focused behavior tests for CIVIC-002 report status tracking."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.civic_action.repository as reports_repository
import app.api.v1.modules.civic_action.service as reports_service
from app.models.enums import ReportCategory, ReportStatus
from app.models.vertical_slice import (
    CitizenIssueReport,
    CitizenReportStatusTransition,
    Claim,
    ClaimSource,
    Source,
    SourceRecord,
)

REPORT_ID = uuid4()
PROJECT_ID = uuid4()


def _report(status: ReportStatus = ReportStatus.SUBMITTED) -> CitizenIssueReport:
    """Build a report fixture at the requested lifecycle state."""
    return CitizenIssueReport(
        id=REPORT_ID,
        project_id=PROJECT_ID,
        category=ReportCategory.QUALITY.value,
        description="A report used by CIVIC-002 tests.",
        status=status.value,
        submitted_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("current", "next_status"),
    [
        (ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW),
        (ReportStatus.UNDER_REVIEW, ReportStatus.REFERRED),
        (ReportStatus.REFERRED, ReportStatus.RESPONDED),
        (ReportStatus.RESPONDED, ReportStatus.RESOLVED),
        (ReportStatus.RESOLVED, ReportStatus.CLOSED),
    ],
)
async def test_each_sequential_transition_updates_and_audits_once(
    monkeypatch: pytest.MonkeyPatch,
    current: ReportStatus,
    next_status: ReportStatus,
) -> None:
    """Each valid next-state transition updates one report and one history row."""
    report = _report(current)
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    transitions: list[CitizenReportStatusTransition] = []

    async def persist(
        session: object,
        updated_report: CitizenIssueReport,
        transition: CitizenReportStatusTransition,
    ) -> CitizenIssueReport:
        transitions.append(transition)
        return updated_report

    monkeypatch.setattr(reports_repository, "update_status", persist)

    response = await reports_service.transition_report_status(
        AsyncMock(), REPORT_ID, next_status
    )

    assert response.status is next_status
    assert report.status == next_status.value
    assert len(transitions) == 1
    assert transitions[0].report_id == REPORT_ID
    assert transitions[0].from_status == current.value
    assert transitions[0].to_status == next_status.value
    assert transitions[0].created_at.tzinfo is not None


@pytest.mark.parametrize(
    ("current", "requested"),
    [
        (ReportStatus.SUBMITTED, ReportStatus.REFERRED),
        (ReportStatus.UNDER_REVIEW, ReportStatus.SUBMITTED),
        (ReportStatus.UNDER_REVIEW, ReportStatus.UNDER_REVIEW),
        (ReportStatus.CLOSED, ReportStatus.CLOSED),
        (ReportStatus.CLOSED, ReportStatus.SUBMITTED),
    ],
)
async def test_invalid_transition_is_rejected_without_history(
    monkeypatch: pytest.MonkeyPatch,
    current: ReportStatus,
    requested: ReportStatus,
) -> None:
    """Skipped, backward, repeated, and closed transitions create no history."""
    report = _report(current)
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    update_status = AsyncMock()
    monkeypatch.setattr(reports_repository, "update_status", update_status)

    with pytest.raises(HTTPException) as error:
        await reports_service.transition_report_status(
            AsyncMock(), REPORT_ID, requested
        )

    assert error.value.status_code == 422
    assert error.value.detail == "Invalid report status transition."
    update_status.assert_not_awaited()


async def test_unknown_report_returns_stable_not_found_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown reports use the stable report not-found response."""
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await reports_service.transition_report_status(
            AsyncMock(), REPORT_ID, ReportStatus.UNDER_REVIEW
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Report not found."


async def test_report_detail_returns_status_history_without_private_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report detail exposes only citizen-safe status and history metadata."""
    report = _report(ReportStatus.UNDER_REVIEW)
    history = [
        CitizenReportStatusTransition(
            report_id=REPORT_ID,
            from_status=ReportStatus.SUBMITTED.value,
            to_status=ReportStatus.UNDER_REVIEW.value,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    ]
    monkeypatch.setattr(reports_repository, "get", AsyncMock(return_value=report))
    monkeypatch.setattr(
        reports_repository,
        "list_status_history",
        AsyncMock(return_value=history),
    )

    response = await reports_service.get_report(AsyncMock(), REPORT_ID)

    assert response.id == REPORT_ID
    assert response.project_id == PROJECT_ID
    assert response.status is ReportStatus.UNDER_REVIEW
    assert response.status_history[0].from_status is ReportStatus.SUBMITTED
    assert response.status_history[0].to_status is ReportStatus.UNDER_REVIEW
    assert response.status_history[0].created_at.tzinfo is not None
    assert not hasattr(response, "description")
    assert not hasattr(response, "contact_information")


def test_report_status_history_is_separate_from_evidence_and_official_sources() -> None:
    """Status tracking does not reuse evidence or official provenance records."""
    assert CitizenReportStatusTransition.__tablename__ == (
        "citizen_report_status_transitions"
    )
    assert Claim.__tablename__ == "claims"
    assert ClaimSource.__tablename__ == "claim_sources"
    assert Source.__tablename__ == "sources"
    assert SourceRecord.__tablename__ == "source_records"
