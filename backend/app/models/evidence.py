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