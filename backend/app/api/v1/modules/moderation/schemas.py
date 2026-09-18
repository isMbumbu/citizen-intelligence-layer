"""API contracts for protected moderation operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ModerationAction, ModerationReason, ModerationTargetType


class ModerationRequest(BaseModel):
    action: ModerationAction
    reason: ModerationReason
    notes: str | None = Field(default=None, max_length=4000)


class ModerationHistoryResponse(BaseModel):
    id: UUID
    target_type: ModerationTargetType
    target_id: UUID
    actor_id: UUID
    action: ModerationAction
    reason: ModerationReason
    previous_state: str
    resulting_state: str
    notes: str | None
    created_at: datetime
