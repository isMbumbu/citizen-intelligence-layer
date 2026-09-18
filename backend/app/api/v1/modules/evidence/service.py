"""Application functions for secure citizen evidence uploads."""

import asyncio
import hashlib
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.modules.comments import repository as comments_repository
from app.api.v1.modules.evidence import repository
from app.api.v1.modules.evidence.processor import EvidenceProcessor
from app.api.v1.modules.evidence.schemas import (
    EvidenceCreateRequest,
    EvidenceDerivedArtifactResponse,
    EvidenceProcessingEventResponse,
    EvidenceProcessingResponse,
    EvidenceResponse,
)
from app.api.v1.modules.projects import repository as projects_repository
from app.core.config import settings
from app.core.logging import logger
from app.core.storage import EvidenceStorage, get_evidence_storage
from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.evidence import (
    EvidenceDerivedArtifact,
    EvidenceProcessingEvent,
    EvidenceRecord,
)
from app.models.vertical_slice import CitizenIssueReport


@dataclass(frozen=True)
class EvidenceDownload:
    """Safe file payload and display metadata for a public evidence download."""

    content: bytes
    mime_type: str
    filename: str


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


async def upload_project_evidence(
    session: AsyncSession,
    project_id: UUID,
    uploader_id: UUID,
    comment_id: UUID | None,
    upload: UploadFile,
) -> EvidenceResponse:
    """Validate, store, and persist evidence attached to a project."""
    await _require_project(session, project_id)
    if comment_id is not None:
        await _require_comment_for_project(session, comment_id, project_id)
    return await _upload(
        session,
        project_id=project_id,
        report_id=None,
        comment_id=comment_id,
        uploader_id=uploader_id,
        upload=upload,
    )


async def upload_comment_evidence(
    session: AsyncSession,
    comment_id: UUID,
    uploader_id: UUID,
    upload: UploadFile,
) -> EvidenceResponse:
    """Validate, store, and persist evidence attached to a comment."""
    comment = await comments_repository.get_comment(session, comment_id)
    if comment is None:
        logger.info("Rejected evidence upload for unknown comment id=%s", comment_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )
    return await _upload(
        session,
        project_id=comment.project_id,
        report_id=None,
        comment_id=comment_id,
        uploader_id=uploader_id,
        upload=upload,
    )


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


async def upload_report_evidence(
    session: AsyncSession,
    project_id: UUID,
    report_id: UUID,
    uploader_id: UUID,
    comment_id: UUID | None,
    upload: UploadFile,
) -> EvidenceResponse:
    """Validate, store, and persist evidence attached to a citizen report."""
    await _require_project(session, project_id)
    report = await session.get(CitizenIssueReport, report_id)
    if report is None or report.project_id != project_id:
        logger.info(
            "Rejected evidence upload for report id=%s project_id=%s",
            report_id,
            project_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen report not found for project.",
        )
    if comment_id is not None:
        await _require_comment_for_project(session, comment_id, project_id)
    return await _upload(
        session,
        project_id=project_id,
        report_id=report_id,
        comment_id=comment_id,
        uploader_id=uploader_id,
        upload=upload,
    )


async def upload_report_evidence_by_id(
    session: AsyncSession,
    report_id: UUID,
    uploader_id: UUID,
    upload: UploadFile,
) -> EvidenceResponse:
    """Validate, store, and persist evidence attached to a citizen report."""
    report = await session.get(CitizenIssueReport, report_id)
    if report is None:
        logger.info("Rejected evidence upload for unknown report id=%s", report_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citizen report not found.",
        )
    return await _upload(
        session,
        project_id=report.project_id,
        report_id=report_id,
        comment_id=None,
        uploader_id=uploader_id,
        upload=upload,
    )


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


async def download_evidence(
    session: AsyncSession,
    evidence_id: UUID,
    *,
    storage: EvidenceStorage | None = None,
) -> EvidenceDownload:
    """Return an explicitly public original evidence file for download."""
    evidence = await repository.get(session, evidence_id)
    if evidence is None:
        logger.info("Evidence download record was not found id=%s", evidence_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found.",
        )
    if not _is_publicly_retrievable(evidence):
        logger.info("Evidence download was denied id=%s", evidence_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Evidence is not publicly retrievable.",
        )

    try:
        content = await (storage or get_evidence_storage()).read(
            evidence.storage_key,
            settings.evidence_max_size_bytes,
        )
    except FileNotFoundError as error:
        logger.warning(
            "Evidence download object was not found id=%s error_type=%s",
            evidence_id,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found.",
        ) from error
    except Exception as error:
        logger.error(
            "Evidence download failed id=%s error_type=%s",
            evidence_id,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve evidence file.",
        ) from error

    return EvidenceDownload(
        content=content,
        mime_type=evidence.mime_type,
        filename=_sanitize_filename(evidence.original_filename),
    )


async def get_processing(
    session: AsyncSession,
    evidence_id: UUID,
) -> EvidenceProcessingResponse:
    """Return safe processing history and derived-artifact lineage."""
    evidence = await repository.get(session, evidence_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found.",
        )
    try:
        events = await repository.list_processing_events(session, evidence_id)
        artifacts = await repository.list_derived_artifacts(session, evidence_id)
    except Exception as error:
        logger.exception("Unable to retrieve evidence processing metadata")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve evidence processing metadata.",
        ) from error
    return EvidenceProcessingResponse(
        evidence_id=evidence.id,
        processing_state=EvidenceProcessingState(evidence.processing_state),
        events=[_event_response(event) for event in events],
        derived_artifacts=[_artifact_response(artifact) for artifact in artifacts],
    )


async def process_evidence(
    session: AsyncSession,
    evidence_id: UUID,
    *,
    task_id: str | None = None,
    storage: EvidenceStorage | None = None,
) -> EvidenceProcessingState:
    """Process one evidence record using service-owned lifecycle rules."""
    evidence = await repository.get(session, evidence_id)
    if evidence is None:
        raise ValueError("Evidence record not found.")
    if evidence.is_deleted:
        raise ValueError("Evidence is not eligible for processing.")
    if evidence.processing_state == EvidenceProcessingState.EXTRACTED.value:
        logger.info("Evidence already processed evidence_id=%s", evidence_id)
        return EvidenceProcessingState.EXTRACTED
    if evidence.processing_state in {
        EvidenceProcessingState.FAILED.value,
        EvidenceProcessingState.HIDDEN.value,
        EvidenceProcessingState.INDEXED.value,
    }:
        raise ValueError("Evidence is not eligible for processing.")

    try:
        if evidence.processing_state == EvidenceProcessingState.RAW.value:
            await transition_processing_state(
                session,
                evidence,
                EvidenceProcessingState.VALIDATION_PASSED,
                event_type="VALIDATION",
                task_id=task_id,
            )
        if evidence.processing_state == EvidenceProcessingState.VALIDATION_PASSED.value:
            processor = EvidenceProcessor(storage or get_evidence_storage())
            artifact_hash = await processor.process(evidence)
            event = await transition_processing_state(
                session,
                evidence,
                EvidenceProcessingState.EXTRACTED,
                event_type="EXTRACTION",
                task_id=task_id,
            )
            existing_artifact = await repository.get_derived_artifact(
                session, evidence.id, "EXTRACTED"
            )
            if existing_artifact is None:
                await repository.create_derived_artifact(
                    session,
                    EvidenceDerivedArtifact(
                        evidence_id=evidence.id,
                        artifact_type="EXTRACTED",
                        content_hash=artifact_hash,
                        processing_event_id=event.id,
                    ),
                )
        await session.commit()
    except Exception as error:
        await session.rollback()
        logger.exception("Evidence processing failed evidence_id=%s", evidence_id)
        await _record_failure(session, evidence, task_id=task_id, error=error)
        raise
    logger.info("Evidence processing completed evidence_id=%s", evidence_id)
    return EvidenceProcessingState(evidence.processing_state)


async def transition_processing_state(
    session: AsyncSession,
    evidence: EvidenceRecord,
    to_state: EvidenceProcessingState,
    *,
    event_type: str,
    task_id: str | None = None,
) -> EvidenceProcessingEvent:
    """Apply one valid transition and append its audit event."""
    current = EvidenceProcessingState(evidence.processing_state)
    allowed = {
        EvidenceProcessingState.RAW: {EvidenceProcessingState.VALIDATION_PASSED},
        EvidenceProcessingState.VALIDATION_PASSED: {EvidenceProcessingState.EXTRACTED},
        EvidenceProcessingState.EXTRACTED: {EvidenceProcessingState.INDEXED},
    }
    if to_state not in allowed.get(current, set()):
        raise ValueError(
            f"Invalid evidence processing transition: {current} -> {to_state}"
        )
    event = EvidenceProcessingEvent(
        evidence_id=evidence.id,
        from_state=current.value,
        to_state=to_state.value,
        event_type=event_type,
        task_id=task_id,
    )
    evidence.processing_state = to_state.value
    await repository.create_processing_event(session, event)
    logger.info(
        "Evidence processing state changed evidence_id=%s state=%s",
        evidence.id,
        to_state,
    )
    return event


async def _record_failure(
    session: AsyncSession,
    evidence: EvidenceRecord,
    *,
    task_id: str | None,
    error: Exception,
) -> None:
    """Persist a bounded failure event without exposing exception details."""
    from_state = evidence.processing_state
    evidence.processing_state = EvidenceProcessingState.FAILED.value
    await repository.create_processing_event(
        session,
        EvidenceProcessingEvent(
            evidence_id=evidence.id,
            from_state=from_state,
            to_state=EvidenceProcessingState.FAILED.value,
            event_type="PROCESSING_FAILED",
            error_code="PROCESSING_FAILED",
            error_message="Evidence processing could not be completed.",
            task_id=task_id,
        ),
    )
    await session.commit()
    logger.warning(
        "Evidence marked failed evidence_id=%s error_type=%s",
        evidence.id,
        type(error).__name__,
    )


def _event_response(event: EvidenceProcessingEvent) -> EvidenceProcessingEventResponse:
    """Convert an internal processing event to its safe API contract."""
    return EvidenceProcessingEventResponse(
        id=event.id,
        from_state=(
            EvidenceProcessingState(event.from_state) if event.from_state else None
        ),
        to_state=EvidenceProcessingState(event.to_state),
        event_type=event.event_type,
        error_code=event.error_code,
        error_message=event.error_message,
        created_at=event.created_at,
    )


def _artifact_response(
    artifact: EvidenceDerivedArtifact,
) -> EvidenceDerivedArtifactResponse:
    """Convert internal artifact lineage to its safe API contract."""
    return EvidenceDerivedArtifactResponse(
        id=artifact.id,
        evidence_id=artifact.evidence_id,
        artifact_type=artifact.artifact_type,
        content_hash=artifact.content_hash,
        source_class=EvidenceSourceClass(artifact.source_class),
        trust_classification=artifact.trust_classification,
        created_at=artifact.created_at,
    )


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


async def _upload(
    session: AsyncSession,
    *,
    project_id: UUID,
    report_id: UUID | None,
    comment_id: UUID | None,
    uploader_id: UUID,
    upload: UploadFile,
    storage: EvidenceStorage | None = None,
) -> EvidenceResponse:
    temporary_path: Path | None = None
    storage_key: str | None = None
    try:
        (
            temporary_path,
            original_filename,
            mime_type,
            file_size,
            checksum,
        ) = await _validate_upload(upload)
        extension = _extension_for_mime(mime_type)
        storage_key = f"evidence/{uuid4()}.{extension}"
        selected_storage = storage or get_evidence_storage()
        await selected_storage.store(temporary_path, storage_key)
        evidence = await repository.create(
            session,
            EvidenceRecord(
                project_id=project_id,
                comment_id=comment_id,
                report_id=report_id,
                uploader_id=uploader_id,
                original_filename=original_filename,
                mime_type=mime_type,
                file_size_bytes=file_size,
                checksum_sha256=checksum,
                storage_key=storage_key,
            ),
        )
    except HTTPException:
        raise
    except Exception as error:
        await session.rollback()
        if storage_key is not None:
            try:
                await (storage or get_evidence_storage()).delete(storage_key)
            except Exception:
                logger.exception("Unable to clean up evidence storage key")
        logger.exception("Unable to persist evidence upload project_id=%s", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store evidence upload.",
        ) from error
    finally:
        if temporary_path is not None:
            try:
                await asyncio.to_thread(temporary_path.unlink)
            except FileNotFoundError:
                pass
    logger.info("Stored evidence upload id=%s project_id=%s", evidence.id, project_id)
    return _response(evidence)


async def _validate_upload(
    upload: UploadFile,
) -> tuple[Path, str, str, int, str]:
    """Stream an upload to a temporary file and validate its untrusted content."""
    original_filename = _sanitize_filename(upload.filename)
    extension = Path(original_filename).suffix.lower()
    if extension not in {".gif", ".jpeg", ".jpg", ".pdf", ".png", ".webp"}:
        raise _upload_error("Unsupported evidence file extension.")

    temporary_file = tempfile.NamedTemporaryFile(
        prefix="citizen-evidence-",
        suffix=".upload",
        delete=False,
    )
    temporary_path = Path(temporary_file.name)
    digest = hashlib.sha256()
    file_size = 0
    try:
        with temporary_file:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > settings.evidence_max_size_bytes:
                    raise _upload_error("Evidence file exceeds the maximum size.")
                digest.update(chunk)
                await asyncio.to_thread(temporary_file.write, chunk)
        detected_mime = await asyncio.to_thread(
            _detect_and_validate_content, temporary_path
        )
        if detected_mime not in settings.evidence_allowed_mime_types:
            raise _upload_error("Evidence file type is not allowed.")
        if upload.content_type != detected_mime:
            raise _upload_error("Evidence MIME type does not match its content.")
        if f".{_extension_for_mime(detected_mime)}" != extension:
            raise _upload_error("Evidence filename does not match its content.")
        return (
            temporary_path,
            original_filename,
            detected_mime,
            file_size,
            digest.hexdigest(),
        )
    except HTTPException:
        try:
            await asyncio.to_thread(temporary_path.unlink)
        except FileNotFoundError:
            pass
        raise
    except Exception as error:
        try:
            await asyncio.to_thread(temporary_path.unlink)
        except FileNotFoundError:
            pass
        logger.info(
            "Rejected malformed evidence upload error_type=%s", type(error).__name__
        )
        raise _upload_error("Evidence file is malformed or unsafe.") from error


def _detect_and_validate_content(path: Path) -> str:
    """Return a trusted MIME type after checking the file signature/content."""
    content = path.read_bytes()
    if content.startswith(b"%PDF-") and b"%%EOF" in content[-1024:]:
        if any(
            marker in content
            for marker in (b"/JavaScript", b"/JS", b"/Launch", b"/EmbeddedFile")
        ):
            raise ValueError("PDF contains active or embedded content.")
        return "application/pdf"
    try:
        with Image.open(path) as image:
            image.verify()
            detected_format = (image.format or "").upper()
    except (OSError, UnidentifiedImageError) as error:
        raise ValueError("Unsupported or malformed evidence content.") from error
    mime_by_format = {
        "GIF": "image/gif",
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }
    try:
        return mime_by_format[detected_format]
    except KeyError as error:
        raise ValueError("Unsupported image format.") from error


def _sanitize_filename(filename: str | None) -> str:
    """Keep a safe display filename while never using it as a storage path."""
    raw_filename = (filename or "evidence").replace("\\", "/")
    basename = Path(raw_filename).name
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", basename).strip(".")
    if not sanitized or sanitized in {".", ".."}:
        return "evidence"
    return sanitized[:255]


def _extension_for_mime(mime_type: str) -> str:
    extensions = {
        "application/pdf": "pdf",
        "image/gif": "gif",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    try:
        return extensions[mime_type]
    except KeyError as error:
        raise _upload_error("Evidence file type is not allowed.") from error


def _upload_error(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail
    )


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
        moderation_state=EvidenceModerationState(evidence.moderation_state),
        processing_state=EvidenceProcessingState(evidence.processing_state),
        visibility=EvidenceVisibility(evidence.visibility),
        is_deleted=evidence.is_deleted,
        uploaded_at=evidence.uploaded_at,
    )


def _is_publicly_retrievable(evidence: EvidenceRecord) -> bool:
    """Return whether an evidence record is safe for unauthenticated retrieval."""
    return (
        not evidence.is_deleted
        and evidence.visibility == EvidenceVisibility.PUBLIC.value
        and evidence.moderation_state
        not in {
            EvidenceModerationState.HIDDEN.value,
            EvidenceModerationState.REMOVED.value,
        }
    )
