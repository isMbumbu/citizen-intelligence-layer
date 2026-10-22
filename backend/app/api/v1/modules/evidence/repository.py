"""Asynchronous persistence functions for evidence metadata."""

from typing import Any
from uuid import UUID

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.logging import logger
from app.models.enums import EvidenceModerationState, EvidenceVisibility
from app.models.evidence import (
    EvidenceDerivedArtifact,
    EvidenceProcessingEvent,
    EvidenceRecord,
)


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


async def list_public(
    session: AsyncSession,
    *,
    project_id: UUID | None,
    report_id: UUID | None,
    comment_id: UUID | None,
) -> list[EvidenceRecord]:
    """Return public, non-moderated-away evidence for one target, newest first."""
    conditions: list[Any] = [
        col(EvidenceRecord.is_deleted).is_(False),
        EvidenceRecord.visibility == EvidenceVisibility.PUBLIC.value,
        col(EvidenceRecord.moderation_state).not_in(
            [
                EvidenceModerationState.HIDDEN.value,
                EvidenceModerationState.REMOVED.value,
            ]
        ),
    ]
    if project_id is not None:
        conditions.append(EvidenceRecord.project_id == project_id)
    if report_id is not None:
        conditions.append(EvidenceRecord.report_id == report_id)
    if comment_id is not None:
        conditions.append(EvidenceRecord.comment_id == comment_id)
    result = await session.exec(
        select(EvidenceRecord)
        .where(*conditions)
        .order_by(col(EvidenceRecord.uploaded_at).desc(), col(EvidenceRecord.id))
        .limit(100)
    )
    return list(result.all())


async def create_processing_event(
    session: AsyncSession,
    event: EvidenceProcessingEvent,
) -> EvidenceProcessingEvent:
    """Stage one processing audit event in the current transaction."""
    try:
        session.add(event)
        await session.flush()
    except Exception:
        logger.exception("Unable to stage evidence processing event")
        raise
    return event


async def create_derived_artifact(
    session: AsyncSession,
    artifact: EvidenceDerivedArtifact,
) -> EvidenceDerivedArtifact:
    """Stage one derived-artifact record in the current transaction."""
    try:
        session.add(artifact)
        await session.flush()
    except Exception:
        logger.exception(
            "Unable to stage derived artifact evidence_id=%s", artifact.evidence_id
        )
        raise
    return artifact


async def list_processing_events(
    session: AsyncSession,
    evidence_id: UUID,
) -> list[EvidenceProcessingEvent]:
    """Return the ordered audit history for one evidence record."""
    try:
        result = await session.exec(
            select(EvidenceProcessingEvent)
            .where(EvidenceProcessingEvent.evidence_id == evidence_id)
            .order_by(col(EvidenceProcessingEvent.created_at))
        )
    except Exception:
        logger.exception("Unable to list processing events evidence_id=%s", evidence_id)
        raise
    return list(result.all())


async def list_derived_artifacts(
    session: AsyncSession,
    evidence_id: UUID,
) -> list[EvidenceDerivedArtifact]:
    """Return separately addressable derived artifacts for one evidence record."""
    try:
        result = await session.exec(
            select(EvidenceDerivedArtifact)
            .where(EvidenceDerivedArtifact.evidence_id == evidence_id)
            .order_by(col(EvidenceDerivedArtifact.created_at))
        )
    except Exception:
        logger.exception("Unable to list derived artifacts evidence_id=%s", evidence_id)
        raise
    return list(result.all())


async def get_derived_artifact(
    session: AsyncSession,
    evidence_id: UUID,
    artifact_type: str,
) -> EvidenceDerivedArtifact | None:
    """Return the idempotent artifact for an evidence processing stage."""
    try:
        result = await session.exec(
            select(EvidenceDerivedArtifact).where(
                EvidenceDerivedArtifact.evidence_id == evidence_id,
                EvidenceDerivedArtifact.artifact_type == artifact_type,
            )
        )
    except Exception:
        logger.exception(
            "Unable to find derived artifact evidence_id=%s artifact_type=%s",
            evidence_id,
            artifact_type,
        )
        raise
    return result.one_or_none()
