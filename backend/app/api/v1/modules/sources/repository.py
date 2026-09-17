"""Asynchronous SQLModel provenance queries for claims and source records."""

from collections import defaultdict
from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vertical_slice import Claim, ClaimSource, Source, SourceRecord


async def list_claims_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> list[Claim]:
    """Return all material claims for one project in a stable order."""
    result = await session.exec(
        select(Claim)
        .where(Claim.project_id == project_id)
        .order_by(col(Claim.field_name), col(Claim.created_at))
    )
    return list(result.all())


async def evidence_for_claims(
    session: AsyncSession,
    claim_ids: set[UUID],
) -> dict[UUID, list[tuple[SourceRecord, Source]]]:
    """Return supporting source records grouped by claim ID."""
    if not claim_ids:
        return {}

    links_result = await session.exec(
        select(ClaimSource).where(col(ClaimSource.claim_id).in_(claim_ids))
    )
    links = list(links_result.all())
    record_ids = {link.source_record_id for link in links}
    if not record_ids:
        return {claim_id: [] for claim_id in claim_ids}

    records_result = await session.exec(
        select(SourceRecord).where(col(SourceRecord.id).in_(record_ids))
    )
    records = {record.id: record for record in records_result.all()}
    source_ids = {record.source_id for record in records.values()}
    sources_result = await session.exec(
        select(Source).where(col(Source.id).in_(source_ids))
    )
    sources = {source.id: source for source in sources_result.all()}

    grouped: defaultdict[UUID, list[tuple[SourceRecord, Source]]] = defaultdict(list)
    for link in links:
        record = records.get(link.source_record_id)
        if record is None:
            continue
        source = sources.get(record.source_id)
        if source is not None:
            grouped[link.claim_id].append((record, source))
    return {claim_id: grouped[claim_id] for claim_id in claim_ids}


async def evidence_for_source_record(
    session: AsyncSession,
    source_record_id: UUID,
) -> tuple[SourceRecord, Source] | None:
    """Return one verification source record and its publisher metadata."""
    record = await session.get(SourceRecord, source_record_id)
    if record is None:
        return None
    source = await session.get(Source, record.source_id)
    if source is None:
        return None
    return record, source
