"""Persistence models for citizen-submitted project comments."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel

from app.models.enums import (
    CommentModerationState,
    CommentReportStatus,
    CommentStatus,
    CommentVisibility,
)
from app.models.vertical_slice import utc_now


class CitizenComment(SQLModel, table=True):
    """A threaded, citizen-submitted comment attached to a public project."""

    __tablename__: ClassVar[str] = "citizen_comments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    parent_comment_id: UUID | None = Field(
        default=None,
        foreign_key="citizen_comments.id",
        index=True,
    )
    author_id: UUID = Field(index=True)
    content: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(
        default=CommentStatus.ACTIVE.value,
        max_length=30,
        index=True,
    )
    moderation_state: str = Field(
        default=CommentModerationState.PENDING.value,
        max_length=30,
        index=True,
    )
    visibility: str = Field(
        default=CommentVisibility.PUBLIC.value,
        max_length=30,
        index=True,
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class CommentReport(SQLModel, table=True):
    """A citizen-submitted abuse or policy report for one comment."""

    __tablename__: ClassVar[str] = "comment_reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    comment_id: UUID = Field(foreign_key="citizen_comments.id", index=True)
    reporter_id: UUID = Field(index=True)
    reason: str = Field(max_length=40, index=True)
    status: str = Field(
        default=CommentReportStatus.SUBMITTED.value,
        max_length=30,
        index=True,
    )
    submitted_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
