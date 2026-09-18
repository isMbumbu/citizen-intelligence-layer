"""Focused behavior tests for INT-002 financial anomalies."""

from datetime import UTC, date, datetime
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
    ProjectVerification,
    Source,
    SourceRecord,
)

PROJECT_ID = uuid4()
SPENT_CLAIM_ID = uuid4()
ALLOCATED_CLAIM_ID = uuid4()
CONTRACTED_CLAIM_ID = uuid4()


def _project() -> Project:
    """Build a synthetic project for INT-002 tests."""
    return Project(
        id=PROJECT_ID,
        demo_key="int-002-project",
        name="INT-002 project",
        description="A project used by INT-002 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2026, 1, 1),
        planned_completion_date=date(2026, 12, 31),
    )


def _financial(
    kind: FinancialKind,
    amount: str,
    claim_id: UUID,
    *,
    currency: str = "KES",
    financial_period: str = "2026",
) -> FinancialRecord:
    """Build a synthetic financial record."""
    return FinancialRecord(
        id=uuid4(),
        project_id=PROJECT_ID,
        kind=kind.value,
        amount=Decimal(amount),
        currency=currency,
        financial_period=financial_period,
        claim_id=claim_id,
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )


def _source_chain(claim_id: UUID) -> tuple[SourceRecord, Source]:
    """Build one synthetic provenance chain."""
    source = Source(
        id=uuid4(),
        demo_key=f"int-002-source-{claim_id}",
        publisher="Synthetic publisher",
        title="Synthetic financial source",
        source_type=SourceType.DEMONSTRATION_RECORD.value,
        url="https://example.invalid/int-002-source",
        retrieved_at=datetime(2026, 6, 3, tzinfo=UTC),
    )
    return (
        SourceRecord(
            id=uuid4(),
            source_id=source.id,
            record_key=f"int-002-record-{claim_id}",
            content_summary="Synthetic sourced financial value.",
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
    records: list[FinancialRecord],
    sourced_claim_ids: set[UUID],
) -> list[object]:
    """Run the existing anomaly service with synthetic financial records."""
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=_project()))
    monkeypatch.setattr(
        projects_service.finance_repository,
        "list_for_project",
        AsyncMock(return_value=records),
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
        AsyncMock(
            return_value={
                claim_id: [_source_chain(claim_id)] for claim_id in sourced_claim_ids
            }
        ),
    )
    return await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)


def _complete_claim_ids() -> set[UUID]:
    return {SPENT_CLAIM_ID, ALLOCATED_CLAIM_ID, CONTRACTED_CLAIM_ID}


def _records(
    *,
    spent: str = "120",
    allocated: str = "100",
    contracted: str = "100",
    currency: str = "KES",
    financial_period: str = "2026",
) -> list[FinancialRecord]:
    return [
        _financial(
            FinancialKind.SPENT,
            spent,
            SPENT_CLAIM_ID,
            currency=currency,
            financial_period=financial_period,
        ),
        _financial(
            FinancialKind.ALLOCATED,
            allocated,
            ALLOCATED_CLAIM_ID,
            currency=currency,
            financial_period=financial_period,
        ),
        _financial(
            FinancialKind.CONTRACTED,
            contracted,
            CONTRACTED_CLAIM_ID,
            currency=currency,
            financial_period=financial_period,
        ),
    ]


async def test_spend_over_allocation_signal_has_exact_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spending over allocation emits the approved financial signal."""
    result = await _lookup(
        monkeypatch,
        _records(spent="120", allocated="100", contracted="120"),
        _complete_claim_ids(),
    )

    allocation_signal = next(
        item for item in result if item.type == "SPEND_OVER_ALLOCATION"
    )
    assert allocation_signal.status == "REVIEW_REQUIRED"
    assert allocation_signal.requires_verification is True
    assert allocation_signal.message == (
        "Recorded spending exceeds the allocated amount. This may warrant verification."
    )
    assert allocation_signal.spent_amount == Decimal("120")
    assert allocation_signal.comparison_amount == Decimal("100")
    assert allocation_signal.comparison_kind == "ALLOCATED"
    assert allocation_signal.currency == "KES"
    assert allocation_signal.financial_period == "2026"


async def test_spend_over_contract_signal_has_exact_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spending over contract emits the approved financial signal."""
    result = await _lookup(
        monkeypatch,
        _records(spent="120", allocated="120", contracted="100"),
        _complete_claim_ids(),
    )

    contract_signal = next(
        item for item in result if item.type == "SPEND_OVER_CONTRACT"
    )
    assert contract_signal.status == "REVIEW_REQUIRED"
    assert contract_signal.requires_verification is True
    assert contract_signal.message == (
        "Recorded spending exceeds the contracted amount. "
        "This may warrant verification."
    )
    assert contract_signal.spent_amount == Decimal("120")
    assert contract_signal.comparison_amount == Decimal("100")
    assert contract_signal.comparison_kind == "CONTRACTED"


async def test_both_signals_are_ordered_after_existing_int001_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Financial signals use the approved allocation-then-contract order."""
    result = await _lookup(monkeypatch, _records(), _complete_claim_ids())

    assert [item.type for item in result] == [
        "SPEND_OVER_ALLOCATION",
        "SPEND_OVER_CONTRACT",
    ]


@pytest.mark.parametrize(
    ("spent", "allocated", "contracted"),
    [("100", "100", "100"), ("90", "100", "100")],
)
async def test_equality_and_lower_spend_are_not_anomalies(
    monkeypatch: pytest.MonkeyPatch,
    spent: str,
    allocated: str,
    contracted: str,
) -> None:
    """Strict comparisons do not flag equality or lower spending."""
    result = await _lookup(
        monkeypatch,
        _records(spent=spent, allocated=allocated, contracted=contracted),
        _complete_claim_ids(),
    )
    assert result == []


@pytest.mark.parametrize(
    "missing_kind",
    [FinancialKind.SPENT, FinancialKind.ALLOCATED, FinancialKind.CONTRACTED],
)
async def test_missing_required_financial_record_suppresses_affected_signal(
    monkeypatch: pytest.MonkeyPatch,
    missing_kind: FinancialKind,
) -> None:
    """Missing financial inputs suppress their dependent signal."""
    records = [record for record in _records() if record.kind != missing_kind.value]
    result = await _lookup(monkeypatch, records, _complete_claim_ids())

    expected = {
        FinancialKind.SPENT: [],
        FinancialKind.ALLOCATED: ["SPEND_OVER_CONTRACT"],
        FinancialKind.CONTRACTED: ["SPEND_OVER_ALLOCATION"],
    }[missing_kind]
    assert [item.type for item in result] == expected


@pytest.mark.parametrize("amount", ["0", "-1"])
async def test_non_positive_comparison_value_suppresses_signal(
    monkeypatch: pytest.MonkeyPatch,
    amount: str,
) -> None:
    """Zero and negative comparison amounts do not produce financial signals."""
    result = await _lookup(
        monkeypatch,
        _records(allocated=amount, contracted=amount),
        _complete_claim_ids(),
    )
    assert result == []


@pytest.mark.parametrize(
    ("currency", "financial_period"),
    [("USD", "2026"), ("KES", "2025")],
)
async def test_incompatible_currency_or_period_suppresses_signals(
    monkeypatch: pytest.MonkeyPatch,
    currency: str,
    financial_period: str,
) -> None:
    """No conversion or period selection is performed for incompatible records."""
    records = [
        _financial(FinancialKind.SPENT, "120", SPENT_CLAIM_ID),
        _financial(
            FinancialKind.ALLOCATED,
            "100",
            ALLOCATED_CLAIM_ID,
            currency=currency,
            financial_period=financial_period,
        ),
        _financial(
            FinancialKind.CONTRACTED,
            "100",
            CONTRACTED_CLAIM_ID,
            currency=currency,
            financial_period=financial_period,
        ),
    ]
    result = await _lookup(monkeypatch, records, _complete_claim_ids())
    assert result == []


async def test_incomplete_provenance_suppresses_only_affected_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each emitted signal requires provenance for both compared claims."""
    result = await _lookup(
        monkeypatch,
        _records(),
        {SPENT_CLAIM_ID, ALLOCATED_CLAIM_ID},
    )
    assert [item.type for item in result] == ["SPEND_OVER_ALLOCATION"]


async def test_duplicate_same_kind_records_use_existing_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate records are not given a new INT-002 resolution rule."""
    duplicate = _financial(FinancialKind.ALLOCATED, "200", uuid4())
    records = _records() + [duplicate]
    claim_ids = _complete_claim_ids() | {duplicate.claim_id}

    result = await _lookup(monkeypatch, records, claim_ids)

    assert [item.type for item in result] == ["SPEND_OVER_CONTRACT"]


async def test_financial_signals_are_read_only_and_unknown_project_is_stable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The endpoint remains read-only and preserves the existing 404 behavior."""
    update = AsyncMock()
    monkeypatch.setattr(projects_service, "repository", projects_repository)
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found."
    update.assert_not_awaited()
