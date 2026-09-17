"""Pydantic v2 contracts for the project-explorer API."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ClaimKind,
    FinancialKind,
    ProjectStatus,
    ProjectType,
    SourceType,
    VerificationStatus,
)


class SourceReferenceResponse(BaseModel):
    """The source and record that support a displayed project claim."""

    source_id: UUID
    source_record_id: UUID
    publisher: str
    title: str
    source_type: SourceType
    url: str
    publication_date: date | None
    retrieved_at: datetime
    record_summary: str


class ClaimReferenceResponse(BaseModel):
    """An evidence link for a specific material fact."""

    claim_id: UUID
    sources: list[SourceReferenceResponse]


class ClaimEvidenceResponse(BaseModel):
    """A material fact and all source records supporting it."""

    id: UUID
    claim_kind: ClaimKind
    field_name: str
    value_text: str
    numeric_value: Decimal | None
    currency: str | None
    financial_period: str | None
    sources: list[SourceReferenceResponse]


class LocationResponse(BaseModel):
    county_id: UUID
    county: str
    sub_county_id: UUID
    sub_county: str
    ward_id: UUID
    ward: str


class ProjectListItemResponse(BaseModel):
    id: UUID
    name: str
    description: str
    project_type: ProjectType
    status: ProjectStatus
    location: LocationResponse


class ProjectPageResponse(BaseModel):
    items: list[ProjectListItemResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class FinancialFactResponse(BaseModel):
    kind: FinancialKind
    amount: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    financial_period: str
    evidence: ClaimReferenceResponse


class FinancialSummaryResponse(BaseModel):
    allocated: FinancialFactResponse | None = None
    committed: FinancialFactResponse | None = None
    contracted: FinancialFactResponse | None = None
    spent: FinancialFactResponse | None = None
    reported: FinancialFactResponse | None = None


class ContractorResponse(BaseModel):
    id: UUID
    legal_name: str
    award_reference: str
    contract_status: str
    contract_start_date: date | None
    contract_end_date: date | None
    evidence: ClaimReferenceResponse


class ProgressResponse(BaseModel):
    percentage: Decimal = Field(ge=0, le=100)
    reported_at: date
    evidence: ClaimReferenceResponse


class TimelineResponse(BaseModel):
    planned_start_date: date
    planned_completion_date: date
    actual_start_date: date | None
    expected_completion_date: date | None


class VerificationResponse(BaseModel):
    status: VerificationStatus
    verification_date: datetime | None
    recorded_at: datetime
    notes: str
    source: SourceReferenceResponse | None


class ProjectDetailResponse(BaseModel):
    """Project-page contract composed from scoped project feature data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    project_type: ProjectType
    status: ProjectStatus
    location: LocationResponse
    financial_summary: FinancialSummaryResponse
    contractor: ContractorResponse | None
    progress: ProgressResponse | None
    timeline: TimelineResponse
    last_verified_at: datetime | None
    verification: VerificationResponse | None
    evidence: list[ClaimEvidenceResponse]


class ProjectAnomalyResponse(BaseModel):
    """A deterministic review flag, not a verification or misconduct finding."""

    type: str
    status: str
    message: str
    requires_verification: bool
    reported_progress_percentage: Decimal = Field(ge=0, le=100)
    spent_budget_percentage: Decimal = Field(ge=0, le=100)
    supporting_claims: list[ClaimReferenceResponse]
