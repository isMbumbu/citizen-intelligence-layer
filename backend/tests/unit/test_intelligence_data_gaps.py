"""Focused behavior tests for INT-004 data-gap signals."""

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

import app.api.v1.modules.projects.repository as projects_repository
import app.api.v1.modules.projects.service as projects_service
from app.models.enums import FinancialKind, SourceType, VerificationStatus
from app.models.vertical_slice import (
    Claim,
    FinancialRecord,
    Project,
    ProjectProgress,
    ProjectVerification,
    Source,
    SourceRecord,
)

PROJECT_ID = uuid4()


def _project() -> Project:
    return Project(
        id=PROJECT_ID,
        demo_key="int-004-project",
        name="INT-004 project",
        description="A project used by INT-004 tests.",
        category_id=uuid4(),
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2026, 1, 1),
        planned_completion_date=date(2026, 12, 31),
    )


def _claim(claim_id: UUID | None = None) -> Claim:
    return Claim(
        id=claim_id or uuid4(),
        project_id=PROJECT_ID,
        claim_kind="FINANCIAL",
        field_name=f"amount-{claim_id or uuid4()}",
        value_text="100",
        numeric_value=Decimal("100"),
        currency="KES",
        financial_period="2026",
    )


def _verification(status: str) -> ProjectVerification:
    return ProjectVerification(
        id=uuid4(),
        project_id=PROJECT_ID,
        status=status,
        notes="Synthetic verification.",
        recorded_at=datetime(2026, 6, 4, tzinfo=UTC),
    )


def _financial(
    kind: FinancialKind,
    claim_id: UUID,
    *,
    amount: str | None = None,
) -> FinancialRecord:
    return FinancialRecord(
        id=uuid4(),
        project_id=PROJECT_ID,
        kind=kind.value,
        amount=Decimal(amount or ("120" if kind is FinancialKind.SPENT else "100")),
        currency="KES",
        financial_period="2026",
        claim_id=claim_id,
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )


def _source_chain(claim_id: UUID) -> tuple[SourceRecord, Source]:
    source = Source(
        id=uuid4(),
        demo_key=f"int-004-source-{claim_id}",
        publisher="Synthetic publisher",
        title="Synthetic source",
        source_type=SourceType.DEMONSTRATION_RECORD.value,
        url="https://example.invalid/int-004-source",
        retrieved_at=datetime(2026, 6, 3, tzinfo=UTC),
    )
    return (
        SourceRecord(
            id=uuid4(),
            source_id=source.id,
            record_key=f"int-004-record-{claim_id}",
            content_summary="Synthetic sourced value.",
        ),
        source,
    )


async def _lookup(
    monkeypatch: pytest.MonkeyPatch,
    *,
    claims: list[Claim] | None = None,
    evidence: dict[UUID, list[object]] | None = None,
    verification: ProjectVerification | None = None,
    project: Project | None = None,
    records: list[FinancialRecord] | None = None,
    progress: ProjectProgress | None = None,
) -> list[object]:
    monkeypatch.setattr(
        projects_repository,
        "get",
        AsyncMock(return_value=project or _project()),
    )
    monkeypatch.setattr(
        projects_service.finance_repository,
        "list_for_project",
        AsyncMock(return_value=records or []),
    )
    monkeypatch.setattr(
        projects_service.repository,
        "get_latest_progress",
        AsyncMock(return_value=progress),
    )
    monkeypatch.setattr(
        projects_service.sources_repository,
        "list_claims_for_project",
        AsyncMock(return_value=claims or []),
    )
    monkeypatch.setattr(
        projects_service.sources_repository,
        "evidence_for_claims",
        AsyncMock(return_value=evidence or {}),
    )
    monkeypatch.setattr(
        projects_service.verification_repository,
        "get_latest_for_project",
        AsyncMock(return_value=verification),
    )
    session = AsyncMock()
    result = await projects_service.get_project_anomalies(session, PROJECT_ID)
    session.rollback.assert_not_awaited()
    session.add.assert_not_called()
    return result


@pytest.mark.parametrize(
    "failure",
    ["missing_claim_source", "missing_record", "missing_source"],
)
async def test_incomplete_claim_provenance_emits_claim_gap(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    claim = _claim()
    result = await _lookup(
        monkeypatch,
        claims=[claim],
        evidence={claim.id: []},
        verification=_verification(VerificationStatus.VERIFIED.value),
    )

    assert len(result) == 1
    signal = result[0]
    assert signal.type == "DATA_GAP_CLAIM_PROVENANCE"
    assert signal.status == "REVIEW_REQUIRED"
    assert signal.requires_verification is True
    assert signal.message == (
        "The claim does not have complete official source provenance. "
        "This missing information may warrant verification."
    )
    assert set(signal.model_dump()) == {
        "type",
        "status",
        "message",
        "requires_verification",
        "claim_id",
        "supporting_claims",
    }
    assert signal.claim_id == claim.id
    assert [item.model_dump() for item in signal.supporting_claims] == [
        {"claim_id": claim.id, "sources": []}
    ]
    assert failure in {"missing_claim_source", "missing_record", "missing_source"}


async def test_complete_claim_provenance_does_not_qualify(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim = _claim()
    result = await _lookup(
        monkeypatch,
        claims=[claim],
        evidence={claim.id: [_source_chain(claim.id)]},
        verification=_verification(VerificationStatus.VERIFIED.value),
    )

    assert result == []


async def test_multiple_claim_gaps_are_unique_and_claim_id_sorted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim_ids = sorted([uuid4(), uuid4(), uuid4()], key=str)
    claims = [_claim(claim_id) for claim_id in reversed(claim_ids)]
    result = await _lookup(
        monkeypatch,
        claims=claims,
        evidence={claim.id: [] for claim in claims},
        verification=_verification(VerificationStatus.VERIFIED.value),
    )

    assert [signal.type for signal in result] == [
        "DATA_GAP_CLAIM_PROVENANCE",
        "DATA_GAP_CLAIM_PROVENANCE",
        "DATA_GAP_CLAIM_PROVENANCE",
    ]
    assert [signal.claim_id for signal in result] == claim_ids
    assert all(signal.supporting_claims[0].sources == [] for signal in result)


async def test_no_claims_produces_no_claim_gap_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = await _lookup(
        monkeypatch,
        claims=[],
        verification=_verification(VerificationStatus.VERIFIED.value),
    )

    assert result == []


async def test_missing_verification_emits_exact_project_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = await _lookup(monkeypatch, verification=None)

    assert len(result) == 1
    signal = result[0]
    assert signal.type == "DATA_GAP_VERIFICATION"
    assert signal.status == "REVIEW_REQUIRED"
    assert signal.requires_verification is True
    assert signal.message == (
        "The project does not have a recorded verification. "
        "This missing information may warrant verification."
    )
    assert set(signal.model_dump()) == {
        "type",
        "status",
        "message",
        "requires_verification",
        "supporting_claims",
    }
    assert signal.supporting_claims == []


@pytest.mark.parametrize("verification_status", list(VerificationStatus))
async def test_existing_verification_states_do_not_qualify(
    monkeypatch: pytest.MonkeyPatch,
    verification_status: VerificationStatus,
) -> None:
    result = await _lookup(
        monkeypatch,
        verification=_verification(verification_status.value),
    )

    assert result == []


async def test_existing_signals_precede_data_gaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim = _claim()
    project = _project()
    project.status = "IN_PROGRESS"
    project.planned_start_date = date(2026, 1, 1)
    project.planned_completion_date = date(2026, 1, 2)
    progress_claim_id = uuid4()
    progress = ProjectProgress(
        id=uuid4(),
        project_id=PROJECT_ID,
        percentage=Decimal("75"),
        reported_at=date(2026, 6, 1),
        claim_id=progress_claim_id,
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )
    allocated_claim_id = uuid4()
    spent_claim_id = uuid4()
    records = [
        _financial(FinancialKind.ALLOCATED, allocated_claim_id),
        _financial(FinancialKind.SPENT, spent_claim_id, amount="40"),
    ]
    evidence_claim_ids = {
        claim.id,
        progress_claim_id,
        allocated_claim_id,
        spent_claim_id,
    }
    result = await _lookup(
        monkeypatch,
        project=project,
        claims=[claim],
        evidence={
            claim_id: [_source_chain(claim_id)] for claim_id in evidence_claim_ids
        },
        verification=None,
        records=records,
        progress=progress,
    )

    assert [signal.type for signal in result] == [
        "PROGRESS_SPEND_GAP",
        "TIMELINE_PAST_DUE",
        "DATA_GAP_VERIFICATION",
    ]


async def test_unknown_project_preserves_existing_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(projects_repository, "get", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        await projects_service.get_project_anomalies(AsyncMock(), PROJECT_ID)

    assert error.value.status_code == 404
    assert error.value.detail == "Project not found."


def test_no_timeline_stalled_implementation() -> None:
    assert "TIMELINE_STALLED" not in vars(projects_service)
