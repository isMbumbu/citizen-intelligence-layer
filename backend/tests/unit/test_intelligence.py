"""Focused behavior tests for INT-001 deterministic anomaly detection."""

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.projects.repository as projects_repository
import app.api.v1.modules.projects.routes as projects_routes
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
PROGRESS_CLAIM_ID = uuid4()
ALLOCATED_CLAIM_ID = uuid4()
SPENT_CLAIM_ID = uuid4()


def _project() -> Project:
    """Build a synthetic project for anomaly lookup tests."""
    return Project(
        id=PROJECT_ID,
        demo_key="int-001-project",
        name="INT-001 project",
        description="A project used by INT-001 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2026, 1, 1),
        planned_completion_date=date(2026, 12, 31),
    )


def _progress(percentage: str = "75") -> ProjectProgress:
    """Build a sourced progress record."""
    return ProjectProgress(
        id=uuid4(),
        project_id=PROJECT_ID,
        percentage=Decimal(percentage),
        reported_at=date(2026, 6, 1),
        claim_id=PROGRESS_CLAIM_ID,
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )


def _financial(
    kind: FinancialKind,
    amount: str,
    claim_id: UUID,
) -> FinancialRecord:
    """Build one synthetic financial record."""
    return FinancialRecord(
        id=uuid4(),
        project_id=PROJECT_ID,
        kind=kind.value,
        amount=Decimal(amount),
        currency="KES",
        financial_period="2026",
        claim_id=claim_id,
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )


def _source_chain(claim_id: UUID) -> tuple[SourceRecord, Source]:
    """Build one synthetic claim provenance chain."""
    source = Source(
        id=uuid4(),
        demo_key=f"source-{claim_id}",
        publisher="Synthetic publisher",
        title="Synthetic source",
        source_type=SourceType.DEMONSTRATION_RECORD.value,
        url="https://example.invalid/source",
        retrieved_at=datetime(2026, 6, 3, tzinfo=UTC),
    )
    return (
        SourceRecord(
            id=uuid4(),
            source_id=source.id,
            record_key=f"record-{claim_id}",
            content_summary="Synthetic sourced value.",
        ),
        source,
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
    *,
    progress: ProjectProgress | None,
    records: list[FinancialRecord],
    sourced_claim_ids: set[UUID],
) -> list[object]:
    """Run the existing public anomaly service with synthetic dependencies."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        projects_repository,
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
    evidence = {claim_id: [_source_chain(claim_id)] for claim_id in sourced_claim_ids}
    monkeypatch.setattr(
        projects_service.sources_repository,
        "evidence_for_claims",
        AsyncMock(return_value=evidence),
    )
    return await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)


async def test_qualifying_gap_returns_existing_review_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sourced 75%-40% gap returns the established signal contract."""
    records = [
        _financial(FinancialKind.ALLOCATED, "100", ALLOCATED_CLAIM_ID),
        _financial(FinancialKind.SPENT, "40", SPENT_CLAIM_ID),
    ]

    result = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=records,
        sourced_claim_ids={PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )

    assert len(result) == 1
    signal = result[0]
    assert signal.type == "PROGRESS_SPEND_GAP"
    assert signal.status == "REVIEW_REQUIRED"
    assert signal.requires_verification is True
    assert signal.reported_progress_percentage == Decimal("75")
    assert signal.spent_budget_percentage == Decimal("40.00")
    assert "may warrant verification" in signal.message
    assert [item.claim_id for item in signal.supporting_claims] == sorted(
        [PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID], key=str
    )
    assert all(item.sources for item in signal.supporting_claims)


async def test_gap_below_threshold_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A gap below 25 percentage points emits no signal."""
    result = await _lookup(
        monkeypatch,
        progress=_progress("64"),
        records=[
            _financial(FinancialKind.ALLOCATED, "100", ALLOCATED_CLAIM_ID),
            _financial(FinancialKind.SPENT, "40", SPENT_CLAIM_ID),
        ],
        sourced_claim_ids={PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )

    assert result == []


async def test_exact_threshold_and_two_decimal_rounding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact 25-point threshold emits a signal with two-decimal rounding."""
    result = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=[
            _financial(FinancialKind.ALLOCATED, "300", ALLOCATED_CLAIM_ID),
            _financial(FinancialKind.SPENT, "150", SPENT_CLAIM_ID),
        ],
        sourced_claim_ids={PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )

    assert len(result) == 1
    assert result[0].spent_budget_percentage == Decimal("50.00")

    rounded = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=[
            _financial(FinancialKind.ALLOCATED, "300", ALLOCATED_CLAIM_ID),
            _financial(FinancialKind.SPENT, "149", SPENT_CLAIM_ID),
        ],
        sourced_claim_ids={PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )
    assert rounded[0].spent_budget_percentage == Decimal("49.67")


@pytest.mark.parametrize(
    "progress",
    [None],
)
async def test_missing_progress_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
    progress: ProjectProgress | None,
) -> None:
    """Missing progress does not fabricate a review signal."""
    result = await _lookup(
        monkeypatch,
        progress=progress,
        records=[_financial(FinancialKind.ALLOCATED, "100", ALLOCATED_CLAIM_ID)],
        sourced_claim_ids={ALLOCATED_CLAIM_ID},
    )
    assert result == []


@pytest.mark.parametrize(
    "records",
    [
        [_financial(FinancialKind.SPENT, "40", SPENT_CLAIM_ID)],
        [_financial(FinancialKind.ALLOCATED, "100", ALLOCATED_CLAIM_ID)],
    ],
)
async def test_missing_allocation_or_spend_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
    records: list[FinancialRecord],
) -> None:
    """Missing allocation or spend does not fabricate a review signal."""
    result = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=records,
        sourced_claim_ids={PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )
    assert result == []


@pytest.mark.parametrize("amount", ["0", "-1"])
async def test_non_positive_allocation_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
    amount: str,
) -> None:
    """Zero and negative allocation values are invalid for the rule."""
    result = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=[
            _financial(FinancialKind.ALLOCATED, amount, ALLOCATED_CLAIM_ID),
            _financial(FinancialKind.SPENT, "40", SPENT_CLAIM_ID),
        ],
        sourced_claim_ids={PROGRESS_CLAIM_ID, ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )
    assert result == []


async def test_incomplete_provenance_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every required claim must have source provenance."""
    result = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=[
            _financial(FinancialKind.ALLOCATED, "100", ALLOCATED_CLAIM_ID),
            _financial(FinancialKind.SPENT, "40", SPENT_CLAIM_ID),
        ],
        sourced_claim_ids={ALLOCATED_CLAIM_ID, SPENT_CLAIM_ID},
    )
    assert result == []


async def test_duplicate_same_kind_records_use_existing_baseline_without_new_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate same-kind records remain outside INT-001 selection semantics."""
    duplicate_allocated = _financial(FinancialKind.ALLOCATED, "200", uuid4())
    records = [
        _financial(FinancialKind.ALLOCATED, "100", ALLOCATED_CLAIM_ID),
        duplicate_allocated,
        _financial(FinancialKind.SPENT, "40", SPENT_CLAIM_ID),
    ]
    sourced_ids = {
        PROGRESS_CLAIM_ID,
        ALLOCATED_CLAIM_ID,
        duplicate_allocated.claim_id,
        SPENT_CLAIM_ID,
    }

    result = await _lookup(
        monkeypatch,
        progress=_progress("75"),
        records=records,
        sourced_claim_ids=sourced_ids,
    )

    assert len(result) == 1
    assert {item.claim_id for item in result[0].supporting_claims} == {
        PROGRESS_CLAIM_ID,
        duplicate_allocated.claim_id,
        SPENT_CLAIM_ID,
    }


async def test_unknown_project_returns_stable_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown projects preserve the existing public 404 behavior."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found."


def test_anomaly_route_is_read_only_and_project_scoped() -> None:
    """INT-001 retains the existing GET-only project anomaly endpoint."""
    route = next(
        route
        for route in projects_routes.router.routes
        if route.path == "/projects/{project_id}/anomalies"
    )
    assert route.methods == {"GET"}
    assert route.status_code is None
