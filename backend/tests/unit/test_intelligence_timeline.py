"""Focused behavior tests for INT-003 timeline anomalies."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.projects.repository as projects_repository
import app.api.v1.modules.projects.service as projects_service
from app.models.enums import FinancialKind, SourceType
from app.models.vertical_slice import (
    FinancialRecord,
    Project,
    ProjectProgress,
    ProjectVerification,
    Source,
    SourceRecord,
)

PROJECT_ID = uuid4()


def _project(
    *,
    status: str = "IN_PROGRESS",
    planned_completion_date: date | None = None,
    planned_start_date: date | None = None,
    actual_start_date: date | None = None,
) -> Project:
    """Build a synthetic project timeline fixture."""
    today = datetime.now(UTC).date()
    return Project(
        id=PROJECT_ID,
        demo_key="int-003-project",
        name="INT-003 project",
        description="A project used by INT-003 tests.",
        category_id=uuid4(),
        status=status,
        ward_id=uuid4(),
        planned_start_date=planned_start_date or today - timedelta(days=60),
        planned_completion_date=planned_completion_date or today - timedelta(days=1),
        actual_start_date=actual_start_date,
    )


def _verification() -> ProjectVerification:
    return ProjectVerification(
        id=uuid4(),
        project_id=PROJECT_ID,
        status="VERIFIED",
        notes="Synthetic verification.",
        recorded_at=datetime(2026, 6, 4, tzinfo=UTC),
    )


async def _lookup(
    monkeypatch: pytest.MonkeyPatch,
    project: Project,
) -> list[object]:
    """Run the existing anomaly service without financial or progress inputs."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=project))
    monkeypatch.setattr(
        projects_service.finance_repository,
        "list_for_project",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        projects_service.repository,
        "get_latest_progress",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        projects_service.sources_repository,
        "list_claims_for_project",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        projects_service.verification_repository,
        "get_latest_for_project",
        AsyncMock(return_value=_verification()),
    )
    monkeypatch.setattr(
        projects_service.sources_repository,
        "evidence_for_claims",
        AsyncMock(return_value={}),
    )
    return await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)


def _financial(kind: FinancialKind, amount: str, claim_id: UUID) -> FinancialRecord:
    return FinancialRecord(
        id=uuid4(),
        project_id=PROJECT_ID,
        kind=kind.value,
        amount=Decimal(amount),
        currency="KES",
        financial_period="2026",
        claim_id=claim_id,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


async def test_in_progress_past_due_project_returns_exact_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An eligible project past its planned date emits TIMELINE_PAST_DUE."""
    project = _project()

    result = await _lookup(monkeypatch, project)

    assert len(result) == 1
    signal = result[0]
    assert signal.type == "TIMELINE_PAST_DUE"
    assert signal.status == "REVIEW_REQUIRED"
    assert signal.requires_verification is True
    assert signal.message == (
        "The project is past its planned completion date without a recorded "
        "completion date. This may warrant verification."
    )
    assert signal.planned_completion_date == project.planned_completion_date
    assert signal.supporting_claims == []


@pytest.mark.parametrize(
    "planned_completion_date",
    [
        datetime.now(UTC).date(),
        datetime.now(UTC).date() + timedelta(days=1),
    ],
)
async def test_equality_or_future_completion_date_does_not_qualify(
    monkeypatch: pytest.MonkeyPatch,
    planned_completion_date: date,
) -> None:
    """Only a date strictly before today is past due."""
    result = await _lookup(
        monkeypatch,
        _project(planned_completion_date=planned_completion_date),
    )

    assert result == []


@pytest.mark.parametrize(
    "status",
    ["COMPLETED", "ON_HOLD", "PLANNED", "CANCELLED"],
)
async def test_ineligible_status_suppresses_timeline_signal(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    """Completed, on-hold, and unsupported statuses do not qualify."""
    result = await _lookup(monkeypatch, _project(status=status))

    assert result == []


async def test_missing_completion_date_suppresses_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing planned completion data produces no signal."""
    project = _project()
    project.planned_completion_date = None  # type: ignore[assignment]

    assert await _lookup(monkeypatch, project) == []


@pytest.mark.parametrize(
    "actual_start_date",
    [
        datetime.now(UTC).date() - timedelta(days=1),
        datetime.now(UTC).date() + timedelta(days=1),
    ],
)
async def test_timeline_contradiction_suppresses_signal(
    monkeypatch: pytest.MonkeyPatch,
    actual_start_date: date,
) -> None:
    """Contradictory start/completion dates do not produce a signal."""
    project = _project(
        planned_completion_date=datetime.now(UTC).date() - timedelta(days=1),
        actual_start_date=actual_start_date,
    )
    if actual_start_date <= project.planned_completion_date:
        project.planned_start_date = project.planned_completion_date + timedelta(days=1)

    assert await _lookup(monkeypatch, project) == []


async def test_timeline_signal_follows_existing_financial_signal_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Timeline output follows INT-001 and INT-002 signals."""
    project = _project()
    progress_claim_id = uuid4()
    spent_claim_id = uuid4()
    allocated_claim_id = uuid4()
    contracted_claim_id = uuid4()
    progress = ProjectProgress(
        id=uuid4(),
        project_id=PROJECT_ID,
        percentage=Decimal("75"),
        reported_at=date(2026, 6, 1),
        claim_id=progress_claim_id,
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )
    records = [
        _financial(FinancialKind.SPENT, "120", spent_claim_id),
        _financial(FinancialKind.ALLOCATED, "100", allocated_claim_id),
        _financial(FinancialKind.CONTRACTED, "100", contracted_claim_id),
    ]
    claim_ids = {
        progress_claim_id,
        spent_claim_id,
        allocated_claim_id,
        contracted_claim_id,
    }
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=project))
    monkeypatch.setattr(
        projects_service.repository,
        "get_latest_progress",
        AsyncMock(return_value=progress),
    )
    monkeypatch.setattr(
        projects_service.finance_repository,
        "list_for_project",
        AsyncMock(return_value=records),
    )
    monkeypatch.setattr(
        projects_service.sources_repository,
        "list_claims_for_project",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        projects_service.verification_repository,
        "get_latest_for_project",
        AsyncMock(return_value=_verification()),
    )
    monkeypatch.setattr(
        projects_service.sources_repository,
        "evidence_for_claims",
        AsyncMock(
            return_value={
                claim_id: [
                    (
                        SourceRecord(
                            id=uuid4(),
                            source_id=uuid4(),
                            record_key=f"record-{claim_id}",
                            content_summary="Synthetic source.",
                        ),
                        Source(
                            id=uuid4(),
                            demo_key=f"source-{claim_id}",
                            publisher="Synthetic publisher",
                            title="Synthetic source",
                            source_type=SourceType.DEMONSTRATION_RECORD.value,
                            url="https://example.invalid/source",
                            retrieved_at=datetime(2026, 6, 3, tzinfo=UTC),
                        ),
                    )
                ]
                for claim_id in claim_ids
            }
        ),
    )

    result = await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)

    assert [signal.type for signal in result] == [
        "SPEND_OVER_ALLOCATION",
        "SPEND_OVER_CONTRACT",
        "TIMELINE_PAST_DUE",
    ]


async def test_unknown_project_preserves_existing_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown projects retain the existing stable 404 behavior."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found."


def test_timeline_signal_has_no_stalled_variant() -> None:
    """INT-003 does not introduce deferred TIMELINE_STALLED output."""
    assert "TIMELINE_STALLED" not in vars(projects_service)
