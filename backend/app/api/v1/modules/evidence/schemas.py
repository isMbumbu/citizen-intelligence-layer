"""API contracts for citizen evidence metadata."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)


class EvidenceCreateRequest(BaseModel):
    """Metadata submitted when an evidence record is reserved."""

    uploader_id: UUID
    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=120)
    file_size_bytes: int = Field(ge=0)
    checksum_sha256: str = Field(min_length=1, max_length=128)
    comment_id: UUID | None = None


class EvidenceResponse(BaseModel):
    """Unverified citizen evidence metadata, never an official source record."""

    id: UUID
    project_id: UUID | None
    comment_id: UUID | None
    report_id: UUID | None
    uploader_id: UUID
    source_class: EvidenceSourceClass
    original_filename: str
    mime_type: str
    file_size_bytes: int
    checksum_sha256: str
    moderation_state: EvidenceModerationState
    processing_state: EvidenceProcessingState
    visibility: EvidenceVisibility
    is_deleted: bool
    uploaded_at: datetime
    is_official_source: bool = False
    trust_label: str = "CITIZEN_SUBMITTED_EVIDENCE"


class EvidenceProcessingEventResponse(BaseModel):
    """Safe public representation of one processing transition."""

    id: UUID
    from_state: EvidenceProcessingState | None
    to_state: EvidenceProcessingState
    event_type: str
    error_code: str | None
    error_message: str | None
    created_at: datetime


class EvidenceDerivedArtifactResponse(BaseModel):
    """Safe lineage metadata for one unverified derived artifact."""

    id: UUID
    evidence_id: UUID
    artifact_type: str
    content_hash: str | None
    source_class: EvidenceSourceClass
    trust_classification: str
    created_at: datetime


class EvidenceProcessingResponse(BaseModel):
    """Processing state, audit history, and derived-artifact lineage."""

    evidence_id: UUID
    processing_state: EvidenceProcessingState
    events: list[EvidenceProcessingEventResponse]
    derived_artifacts: list[EvidenceDerivedArtifactResponse]
