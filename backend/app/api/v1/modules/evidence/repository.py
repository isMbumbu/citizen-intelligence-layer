"""Asynchronous persistence functions for evidence metadata."""

from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.evidence import EvidenceRecord


async def create(
    session: AsyncSession,
    evidence: EvidenceRecord,
) -> EvidenceRecord:
    """Persist one evidence metadata record."""
    try:
        session.add(evidence)
        await session.commit()
        await session.refresh(evidence)
    except Exception:
        await session.rollback()
        logger.exception("Unable to store evidence metadata")
        raise
    logger.info(
        "Stored evidence metadata id=%s project_id=%s",
        evidence.id,
        evidence.project_id,
    )
    return evidence


async def get(
    session: AsyncSession,
    evidence_id: UUID,
) -> EvidenceRecord | None:
    """Return evidence metadata by identifier."""
    return await session.get(EvidenceRecord, evidence_id)


async def list_for_project(
    session: AsyncSession,
    project_id: UUID,
) -> list[EvidenceRecord]:
    """Return evidence metadata attached to one project."""
    result = await session.exec(
        select(EvidenceRecord)
        .where(
            EvidenceRecord.project_id == project_id,
            col(EvidenceRecord.is_deleted).is_(False),
        )
        .order_by(col(EvidenceRecord.uploaded_at))
    )
    return list(result.all())
