"""Focused behavior tests for CIVIC-004 public report browsing."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

import app.api.v1.modules.civic_action.repository as reports_repository
import app.api.v1.modules.civic_action.routes as reports_routes
import app.api.v1.modules.civic_action.service as reports_service
from app.api.v1.modules.civic_action.schemas import PublicReportListItem
from app.models.enums import ReportCategory, ReportStatus
from app.models.vertical_slice import CitizenIssueReport

PROJECT_ID = uuid4()


def _report() -> CitizenIssueReport:
    """Build a report fixture containing fields that must remain private."""
    return CitizenIssueReport(
        id=uuid4(),
        project_id=PROJECT_ID,
        category=ReportCategory.DELAY.value,
        description="A synthetic CIVIC-004 report description.",
        contact_information="private@example.test",
        status=ReportStatus.UNDER_REVIEW.value,
        submitted_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def test_list_reports_returns_summaries_without_private_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _report()
    list_reports = AsyncMock(return_value=([(report, "Synthetic Project")], 41))
    monkeypatch.setattr(reports_repository, "list_public_reports", list_reports)

    page = await reports_service.list_reports(
        AsyncMock(),
        project_id=PROJECT_ID,
        report_status=ReportStatus.UNDER_REVIEW,
        category=ReportCategory.DELAY,
        page=3,
        page_size=20,
    )

    assert page.total == 41
    assert page.page == 3
    item = page.items[0]
    assert item.project_name == "Synthetic Project"
    assert item.status is ReportStatus.UNDER_REVIEW
    dumped = page.model_dump_json()
    assert "synthetic CIVIC-004 report description" not in dumped
    assert "private@example.test" not in dumped
    list_reports.assert_awaited_once()
    assert list_reports.await_args is not None
    assert list_reports.await_args.kwargs == {
        "project_id": PROJECT_ID,
        "status": "UNDER_REVIEW",
        "category": "DELAY",
        "offset": 40,
        "limit": 20,
    }


def test_list_item_contract_has_no_content_fields() -> None:
    assert set(PublicReportListItem.model_fields) == {
        "id",
        "project_id",
        "project_name",
        "category",
        "status",
        "submitted_at",
    }


async def test_list_public_reports_query_joins_projects_and_filters() -> None:
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

    rows, total = await reports_repository.list_public_reports(
        FakeSession(),  # type: ignore[arg-type]
        project_id=PROJECT_ID,
        status="SUBMITTED",
        category="QUALITY",
        offset=0,
        limit=10,
    )

    assert (rows, total) == ([], 0)
    page_sql, count_sql = (
        str(statement.compile(dialect=postgresql.dialect())) for statement in statements
    )
    assert "JOIN projects ON citizen_issue_reports.project_id = projects.id" in (
        page_sql
    )
    assert "ORDER BY citizen_issue_reports.submitted_at DESC" in page_sql
    assert "citizen_issue_reports.status" in count_sql
    assert "citizen_issue_reports.category" in count_sql


def test_public_report_list_route_is_get_only() -> None:
    route = next(
        route
        for route in reports_routes.report_router.routes
        if getattr(route, "path", None) == "/reports"
    )
    assert getattr(route, "methods", None) == {"GET"}
