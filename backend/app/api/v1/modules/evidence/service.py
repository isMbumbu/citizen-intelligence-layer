"""Application functions for citizen evidence metadata."""

from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.comments import repository as comments_repository
from app.api.v1.modules.evidence import repository
from app.api.v1.modules.evidence.schemas import EvidenceCreateRequest, EvidenceResponse
from app.api.v1.modules.projects import repository as projects_repository
from app.core.logging import logger
from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.evidence import EvidenceRecord
from app.models.vertical_slice import CitizenIssueReport


async def create_project_evidence(
    session: AsyncSession,
    project_id: UUID,
    payload: EvidenceCreateRequest,
) -> EvidenceResponse:
    """Create metadata for evidence attached directly to a project or comment."""
    await _require_project(session, project_id)
    if payload.comment_id is not None:
        await _require_comment_for_project(session, payload.comment_id, project_id)
    response = await _create(
        session,
        project_id=project_id,
        report_id=None,
        payload=payload,
    )
    logger.info(
        "Created project evidence metadata id=%s project_id=%s comment_id=%s",
        response.id,
        project_id,
        payload.comment_id,
    )
    return response


async def create_report_evidence(
    session: AsyncSession,
    project_id: UUID,
    report_id: UUID,
    payload: EvidenceCreateRequest,
) -> EvidenceResponse:
    """Create metadata for evidence attached to an existing citizen report."""
    await _require_project(session, project_id)
    report = await session.get(CitizenIssueReport, report_id)
    if report is None or report.project_id != project_id:
        logger.info(
            "Rejected evidence for report id=%s project_id=%s",
            report_id,
            project_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen report not found for project.",
        )
    if payload.comment_id is not None:
        await _require_comment_for_project(session, payload.comment_id, project_id)
    response = await _create(
        session,
        project_id=project_id,
        report_id=report_id,
        payload=payload,
    )
    logger.info(
        "Created report evidence metadata id=%s project_id=%s report_id=%s",
        response.id,
        project_id,
        report_id,
    )
    return response


async def get_evidence(
    session: AsyncSession,
    evidence_id: UUID,
) -> EvidenceResponse:
    """Return evidence metadata without retrieving file content."""
    evidence = await repository.get(session, evidence_id)
    if evidence is None:
        logger.info("Evidence metadata was not found id=%s", evidence_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found.",
        )
    logger.info(
        "Retrieved evidence metadata id=%s project_id=%s state=%s",
        evidence.id,
        evidence.project_id,
        evidence.processing_state,
    )
    return _response(evidence)


async def _create(
    session: AsyncSession,
    *,
    project_id: UUID,
    report_id: UUID | None,
    payload: EvidenceCreateRequest,
) -> EvidenceResponse:
    try:
        evidence = await repository.create(
            session,
            EvidenceRecord(
                project_id=project_id,
                comment_id=payload.comment_id,
                report_id=report_id,
                uploader_id=payload.uploader_id,
                original_filename=payload.original_filename,
                mime_type=payload.mime_type,
                file_size_bytes=payload.file_size_bytes,
                checksum_sha256=payload.checksum_sha256,
                storage_key=f"evidence/{uuid4()}",
            ),
        )
    except Exception as error:
        await session.rollback()
        logger.exception(
            "Unable to create evidence metadata for project id=%s", project_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create evidence metadata.",
        ) from error
    return _response(evidence)


async def _require_project(session: AsyncSession, project_id: UUID) -> None:
    if await projects_repository.get(session, project_id) is None:
        logger.info("Rejected evidence for unknown project id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )


async def _require_comment_for_project(
    session: AsyncSession,
    comment_id: UUID,
    project_id: UUID,
) -> None:
    comment = await comments_repository.get_comment(session, comment_id)
    if comment is None or comment.project_id != project_id:
        logger.info(
            "Rejected evidence for comment id=%s project_id=%s",
            comment_id,
            project_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found for project.",
        )


def _response(evidence: EvidenceRecord) -> EvidenceResponse:
    return EvidenceResponse(
        id=evidence.id,
        project_id=evidence.project_id,
        comment_id=evidence.comment_id,
        report_id=evidence.report_id,
        uploader_id=evidence.uploader_id,
        source_class=EvidenceSourceClass(evidence.source_class),
        original_filename=evidence.original_filename,
        mime_type=evidence.mime_type,
        file_size_bytes=evidence.file_size_bytes,
        checksum_sha256=evidence.checksum_sha256,
        storage_key=evidence.storage_key,
        moderation_state=EvidenceModerationState(evidence.moderation_state),
        processing_state=EvidenceProcessingState(evidence.processing_state),
        visibility=EvidenceVisibility(evidence.visibility),
        is_deleted=evidence.is_deleted,
        uploaded_at=evidence.uploaded_at,
    )
