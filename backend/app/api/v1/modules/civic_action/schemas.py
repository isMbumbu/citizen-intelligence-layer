"""Pydantic contracts for the intentionally narrow citizen reporting flow."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ReportCategory, ReportStatus


class CitizenReportCreateRequest(BaseModel):
    category: ReportCategory
    description: str = Field(min_length=10, max_length=4000)
    contact_information: str | None = Field(default=None, max_length=255)

    @field_validator("description")
    @classmethod
    def description_must_contain_content(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("Description must contain at least 10 characters.")
        return cleaned

    @field_validator("contact_information")
    @classmethod
    def normalize_optional_contact(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CitizenReportResponse(BaseModel):
    id: UUID
    project_id: UUID
    category: ReportCategory
    status: ReportStatus
    submitted_at: datetime


class CitizenReportStatusHistoryResponse(BaseModel):
    """Public-safe representation of one report status transition."""

    from_status: ReportStatus
    to_status: ReportStatus
    created_at: datetime


class CitizenReportDetailResponse(BaseModel):
    """Public-safe report status and lifecycle history."""

    id: UUID
    project_id: UUID
    category: ReportCategory
    status: ReportStatus
    submitted_at: datetime
    status_history: list[CitizenReportStatusHistoryResponse]
