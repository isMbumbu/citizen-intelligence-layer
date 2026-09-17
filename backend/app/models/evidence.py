"""Persistence model for citizen-submitted evidence metadata."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.enums import (
    EvidenceModerationState,
    EvidenceProcessingState,
    EvidenceSourceClass,
    EvidenceVisibility,
)
from app.models.vertical_slice import utc_now


class EvidenceRecord(SQLModel, table=True):
    """Unverified citizen evidence metadata kept separate from official sources."""

    __tablename__: ClassVar[str] = "evidence_records"
    __table_args__ = (
        UniqueConstraint("storage_key", name="uq_evidence_records_storage_key"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID | None = Field(
        default=None,
        foreign_key="projects.id",
        index=True,
    )
    comment_id: UUID | None = Field(
        default=None,
        foreign_key="citizen_comments.id",
        index=True,
    )
    report_id: UUID | None = Field(
        default=None,
        foreign_key="citizen_issue_reports.id",
        index=True,
    )
    uploader_id: UUID = Field(index=True)
    source_class: str = Field(
        default=EvidenceSourceClass.CITIZEN_SUBMITTED.value,
        sa_column=Column(String(length=40), nullable=False),
    )
    original_filename: str = Field(max_length=255)
    mime_type: str = Field(max_length=120)
    file_size_bytes: int = Field(ge=0)
    checksum_sha256: str = Field(max_length=128)
    storage_key: str = Field(max_length=255, index=True)
    moderation_state: str = Field(
        default=EvidenceModerationState.PENDING.value,
        max_length=30,
        index=True,
    )
    processing_state: str = Field(
        default=EvidenceProcessingState.RAW.value,
        max_length=30,
        index=True,
    )
    visibility: str = Field(
        default=EvidenceVisibility.PRIVATE.value,
        max_length=30,
        index=True,
    )
    is_deleted: bool = Field(default=False, index=True)
    uploaded_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class EvidenceProcessingEvent(SQLModel, table=True):
    """Bounded audit metadata for one evidence processing transition."""

    __tablename__: ClassVar[str] = "evidence_processing_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    evidence_id: UUID = Field(foreign_key="evidence_records.id", index=True)
    from_state: str | None = Field(default=None, max_length=30)
    to_state: str = Field(max_length=30)
    event_type: str = Field(max_length=50)
    error_code: str | None = Field(default=None, max_length=50)
    error_message: str | None = Field(default=None, max_length=500)
    task_id: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class EvidenceDerivedArtifact(SQLModel, table=True):
    """Unverified, separately addressable output derived from evidence."""

    __tablename__: ClassVar[str] = "evidence_derived_artifacts"
    __table_args__ = (
        UniqueConstraint(
            "evidence_id",
            "artifact_type",
            name="uq_evidence_derived_artifacts_stage",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    evidence_id: UUID = Field(foreign_key="evidence_records.id", index=True)
    artifact_type: str = Field(max_length=50)
    content_reference: str | None = Field(default=None, max_length=255)
    content_hash: str | None = Field(default=None, max_length=128)
    processing_event_id: UUID = Field(
        foreign_key="evidence_processing_events.id",
        index=True,
    )
    source_class: str = Field(
        default=EvidenceSourceClass.CITIZEN_SUBMITTED.value,
        sa_column=Column(String(length=40), nullable=False),
    )
    trust_classification: str = Field(
        default="DERIVED_UNVERIFIED_NON_OFFICIAL",
        max_length=60,
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
