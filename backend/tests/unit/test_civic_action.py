"""Focused behavior and privacy tests for CIVIC-001 report submission."""

import logging
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import app.api.v1.modules.civic_action.repository as reports_repository
import app.api.v1.modules.civic_action.routes as reports_routes
import app.api.v1.modules.civic_action.service as reports_service
from app.api.v1.modules.civic_action.schemas import (
    CitizenReportCreateRequest,
)
from app.api.v1.modules.projects import repository as projects_repository
from app.models.enums import ReportCategory, ReportStatus
from app.models.vertical_slice import Claim, ClaimSource, Project, Source, SourceRecord

PROJECT_ID = uuid4()


def _project() -> Project:
    """Build a project fixture for report submission tests."""
    return Project(
        id=PROJECT_ID,
        demo_key="report-project",
        name="Report project",
        description="A project used by CIVIC-001 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=datetime(2026, 1, 1).date(),
        planned_completion_date=datetime(2026, 12, 31).date(),
    )


def _payload(*, contact_information: str | None = None) -> CitizenReportCreateRequest:
    """Build a valid report request with optional contact information."""
    return CitizenReportCreateRequest(
        category=ReportCategory.QUALITY,
        description="The project site needs a safety inspection.",
        contact_information=contact_information,
    )


async def test_valid_report_submission_returns_created_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid report is associated with its project and starts submitted."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    created = Mock()

    async def persist(session: object, report: object) -> object:
        created(report)
        return report

    monkeypatch.setattr(reports_repository, "create", persist)
    response = await reports_service.submit_report(AsyncMock(), PROJECT_ID, _payload())

    stored = created.call_args.args[0]
    assert response.project_id == PROJECT_ID
    assert response.category is ReportCategory.QUALITY
    assert response.status is ReportStatus.SUBMITTED
    assert response.submitted_at.tzinfo is not None
    assert response.submitted_at.utcoffset() is not None
    assert not hasattr(response, "contact_information")
    assert stored.project_id == PROJECT_ID
    assert stored.status == ReportStatus.SUBMITTED.value
    assert stored.contact_information is None


def test_report_route_returns_created() -> None:
    """The report endpoint advertises the required 201 response."""
    route = next(
        route
        for route in reports_routes.router.routes
        if route.path == "/projects/{project_id}/reports"
    )
    assert route.status_code == 201


async def test_contact_information_is_persisted_only_on_report_and_not_logged(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Contact information is stored on the report but absent from logs and output."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    stored: list[object] = []

    async def persist(session: object, report: object) -> object:
        stored.append(report)
        return report

    monkeypatch.setattr(reports_repository, "create", persist)
    secret_contact = "citizen@example.test"
    with caplog.at_level(logging.INFO, logger="citizen_intelligence"):
        response = await reports_service.submit_report(
            AsyncMock(), PROJECT_ID, _payload(contact_information=secret_contact)
        )

    assert stored[0].contact_information == secret_contact  # type: ignore[attr-defined]
    assert not hasattr(response, "contact_information")
    assert secret_contact not in caplog.text
    assert response.project_id == PROJECT_ID


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"category": "NOT_A_CATEGORY", "description": "A valid description."},
        {"category": "QUALITY"},
        {"category": "QUALITY", "description": "   "},
        {"category": "QUALITY", "description": "Too short"},
    ],
)
def test_invalid_report_requests_have_stable_validation_errors(
    payload: dict[str, object],
) -> None:
    """Invalid category and description inputs fail through the schema contract."""
    with pytest.raises(ValidationError) as error:
        CitizenReportCreateRequest.model_validate(payload)

    assert error.value.errors()
    assert "contact_information" not in str(error.value)


def test_optional_contact_information_is_normalized_and_bounded() -> None:
    """Optional contact input is trimmed and the existing length limit is enforced."""
    payload = _payload(contact_information="  citizen@example.test  ")
    assert payload.contact_information == "citizen@example.test"

    with pytest.raises(ValidationError):
        _payload(contact_information="x" * 256)


async def test_unknown_project_returns_stable_not_found_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown projects do not expose database details."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await reports_service.submit_report(AsyncMock(), PROJECT_ID, _payload())

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found."


async def test_database_failure_returns_safe_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistence failures are rolled back and translated to a safe response."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        reports_repository,
        "create",
        AsyncMock(side_effect=RuntimeError("database password and host")),
    )
    session = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await reports_service.submit_report(session, PROJECT_ID, _payload())

    assert error.value.status_code == 500
    assert error.value.detail == "Unable to submit issue report."
    assert "database password" not in error.value.detail
    session.rollback.assert_awaited_once()


def test_report_does_not_introduce_evidence_or_official_provenance_models() -> None:
    """The report remains separate from evidence and official provenance records."""
    assert Claim.__tablename__ == "claims"
    assert ClaimSource.__tablename__ == "claim_sources"
    assert Source.__tablename__ == "sources"
    assert SourceRecord.__tablename__ == "source_records"
