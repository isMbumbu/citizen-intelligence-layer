"""API contracts for citizen-submitted project comments."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    CommentModerationState,
    CommentReportReason,
    CommentReportStatus,
    CommentStatus,
    CommentVisibility,
)


class CitizenCommentCreateRequest(BaseModel):
    author_id: UUID
    content: str = Field(min_length=10, max_length=4000)
    parent_comment_id: UUID | None = None

    @field_validator("content")
    @classmethod
    def content_must_contain_text(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("Comment content must contain at least 10 characters.")
        return cleaned


class CitizenCommentResponse(BaseModel):
    id: UUID
    project_id: UUID
    parent_comment_id: UUID | None
    author_id: UUID
    content: str
    status: CommentStatus
    moderation_state: CommentModerationState
    visibility: CommentVisibility
    is_citizen_submitted: bool = True
    trust_label: str = "CITIZEN_SUBMITTED_INFORMATION"
    created_at: datetime
    updated_at: datetime


class CommentReportCreateRequest(BaseModel):
    reporter_id: UUID
    reason: CommentReportReason


class CommentReportResponse(BaseModel):
    id: UUID
    comment_id: UUID
    reporter_id: UUID
    reason: CommentReportReason
    status: CommentReportStatus
    submitted_at: datetime
