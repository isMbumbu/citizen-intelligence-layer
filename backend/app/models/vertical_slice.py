"""Persistence tables for the deliberately narrow project-explorer slice."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel

from app.models.enums import (
    ClaimReviewRequestType,
    InstitutionRole,
    ReportInstitutionRelationship,
)


def utc_now() -> datetime:
    """Return an aware UTC timestamp for persistence defaults."""
    return datetime.now(UTC)


class County(SQLModel, table=True):
    __tablename__: ClassVar[str] = "counties"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120, index=True)
    code: str = Field(max_length=32, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SubCounty(SQLModel, table=True):
    __tablename__: ClassVar[str] = "sub_counties"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    county_id: UUID = Field(foreign_key="counties.id", index=True)
    name: str = Field(max_length=120, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Ward(SQLModel, table=True):
    __tablename__: ClassVar[str] = "wards"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sub_county_id: UUID = Field(foreign_key="sub_counties.id", index=True)
    name: str = Field(max_length=120, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProjectCategory(SQLModel, table=True):
    """Database-managed, top-level reference data for public-project grouping."""

    __tablename__: ClassVar[str] = "project_categories"
    __table_args__ = (UniqueConstraint("code", name="uq_project_categories_code"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(max_length=80, index=True)
    name: str = Field(max_length=160, index=True)
    description: str = Field(max_length=1000)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProjectSubtype(SQLModel, table=True):
    """Database-managed, category-scoped detail for project classification."""

    __tablename__: ClassVar[str] = "project_subtypes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_project_subtypes_code"),
        UniqueConstraint(
            "category_id", "code", name="uq_project_subtypes_category_code"
        ),
        UniqueConstraint("category_id", "id", name="uq_project_subtypes_category_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    category_id: UUID = Field(foreign_key="project_categories.id", index=True)
    code: str = Field(max_length=80, index=True)
    name: str = Field(max_length=160, index=True)
    description: str = Field(max_length=1000)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Project(SQLModel, table=True):
    __tablename__: ClassVar[str] = "projects"
    __table_args__ = (
        ForeignKeyConstraint(
            ["category_id", "subtype_id"],
            ["project_subtypes.category_id", "project_subtypes.id"],
            name="fk_projects_category_subtype",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    demo_key: str = Field(max_length=80, index=True)
    name: str = Field(max_length=255, index=True)
    description: str = Field(max_length=4000)
    project_type: str | None = Field(default=None, max_length=30, index=True)
    category_id: UUID = Field(foreign_key="project_categories.id", index=True)
    subtype_id: UUID | None = Field(
        default=None,
        foreign_key="project_subtypes.id",
        index=True,
    )
    status: str = Field(max_length=30, index=True)
    ward_id: UUID = Field(foreign_key="wards.id", index=True)
    planned_start_date: date
    planned_completion_date: date
    actual_start_date: date | None = None
    expected_completion_date: date | None = None
    last_verified_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Contractor(SQLModel, table=True):
    __tablename__: ClassVar[str] = "contractors"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    demo_key: str = Field(max_length=80, index=True)
    legal_name: str = Field(max_length=255, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProjectContract(SQLModel, table=True):
    __tablename__: ClassVar[str] = "project_contracts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    contractor_id: UUID = Field(foreign_key="contractors.id", index=True)
    award_reference: str = Field(max_length=120)
    contract_status: str = Field(max_length=30)
    contract_start_date: date | None = None
    contract_end_date: date | None = None
    claim_id: UUID = Field(foreign_key="claims.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Source(SQLModel, table=True):
    __tablename__: ClassVar[str] = "sources"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    demo_key: str = Field(max_length=100, index=True)
    publisher: str = Field(max_length=255)
    title: str = Field(max_length=500)
    source_type: str = Field(max_length=40)
    url: str = Field(max_length=2048)
    publication_date: date | None = None
    retrieved_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    document_hash: str | None = Field(default=None, max_length=128)
    storage_reference: str | None = Field(default=None, max_length=1024)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class SourceRecord(SQLModel, table=True):
    __tablename__: ClassVar[str] = "source_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_id: UUID = Field(foreign_key="sources.id", index=True)
    record_key: str = Field(max_length=160, index=True)
    content_summary: str = Field(max_length=4000)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Claim(SQLModel, table=True):
    __tablename__: ClassVar[str] = "claims"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    claim_kind: str = Field(max_length=30, index=True)
    field_name: str = Field(max_length=80, index=True)
    value_text: str = Field(max_length=500)
    numeric_value: Decimal | None = Field(
        default=None,
        max_digits=16,
        decimal_places=2,
    )
    currency: str | None = Field(default=None, max_length=3)
    financial_period: str | None = Field(default=None, max_length=20)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ClaimSource(SQLModel, table=True):
    __tablename__: ClassVar[str] = "claim_sources"

    claim_id: UUID = Field(foreign_key="claims.id", primary_key=True)
    source_record_id: UUID = Field(foreign_key="source_records.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ClaimReviewRequest(SQLModel, table=True):
    """Append-only internal request to correct or review one material claim."""

    __tablename__: ClassVar[str] = "claim_review_requests"
    __table_args__ = (
        CheckConstraint(
            "request_type IN ('CORRECTION', 'REVIEW_APPEAL')",
            name="ck_claim_review_requests_request_type",
        ),
        CheckConstraint(
            "char_length(btrim(content)) > 0 AND char_length(content) <= 4000",
            name="ck_claim_review_requests_content",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    claim_id: UUID = Field(foreign_key="claims.id")
    request_type: ClaimReviewRequestType
    content: str = Field(max_length=4000)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    def __init__(self, **data: Any) -> None:
        if isinstance(data.get("content"), str):
            data["content"] = self.normalize_content(data["content"])
        super().__init__(**data)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 4000:
            raise ValueError("Claim review request content is invalid.")
        return normalized

    @validates("content")
    def validate_content_assignment(self, key: str, value: str) -> str:
        return self.normalize_content(value)


class FinancialRecord(SQLModel, table=True):
    __tablename__: ClassVar[str] = "financial_records"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    kind: str = Field(max_length=30, index=True)
    amount: Decimal = Field(max_digits=16, decimal_places=2)
    currency: str = Field(default="KES", max_length=3)
    financial_period: str = Field(max_length=20)
    claim_id: UUID = Field(foreign_key="claims.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProjectProgress(SQLModel, table=True):
    __tablename__: ClassVar[str] = "project_progress_updates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    percentage: Decimal = Field(max_digits=5, decimal_places=2)
    reported_at: date
    claim_id: UUID = Field(foreign_key="claims.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProjectVerification(SQLModel, table=True):
    __tablename__: ClassVar[str] = "project_verifications"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    status: str = Field(max_length=30, index=True)
    verification_date: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    recorded_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    notes: str = Field(max_length=4000)
    source_record_id: UUID | None = Field(
        default=None,
        foreign_key="source_records.id",
        index=True,
    )


class CitizenIssueReport(SQLModel, table=True):
    __tablename__: ClassVar[str] = "citizen_issue_reports"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    category: str = Field(max_length=30, index=True)
    description: str = Field(max_length=4000)
    contact_information: str | None = Field(default=None, max_length=255)
    status: str = Field(default="SUBMITTED", max_length=30, index=True)
    submitted_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class CitizenReportStatusTransition(SQLModel, table=True):
    """Auditable status change for one citizen issue report."""

    __tablename__: ClassVar[str] = "citizen_report_status_transitions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    report_id: UUID = Field(
        foreign_key="citizen_issue_reports.id",
        index=True,
    )
    from_status: str = Field(max_length=30)
    to_status: str = Field(max_length=30)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ReportingChannel(SQLModel, table=True):
    """Public reporting-channel reference data scoped to one geography level."""

    __tablename__: ClassVar[str] = "reporting_channels"
    __table_args__ = (
        CheckConstraint(
            "issue_category IN ('QUALITY', 'DELAY', 'ACCESS', 'SAFETY', 'OTHER')",
            name="ck_reporting_channels_issue_category",
        ),
        CheckConstraint(
            "num_nonnulls(county_id, sub_county_id, ward_id) = 1",
            name="ck_reporting_channels_one_geography",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_reporting_channels_priority",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    issue_category: str = Field(max_length=30, index=True)
    county_id: UUID | None = Field(default=None, foreign_key="counties.id", index=True)
    sub_county_id: UUID | None = Field(
        default=None,
        foreign_key="sub_counties.id",
        index=True,
    )
    ward_id: UUID | None = Field(default=None, foreign_key="wards.id", index=True)
    office_name: str = Field(max_length=160)
    channel_type: str = Field(max_length=40)
    destination: str = Field(max_length=512)
    display_label: str | None = Field(default=None, max_length=160)
    priority: int = Field(default=100, ge=0, index=True)
    is_active: bool = Field(default=True, index=True)


class Institution(SQLModel, table=True):
    """Reference data for a public institution receiving report links."""

    __tablename__: ClassVar[str] = "institutions"
    __table_args__ = (UniqueConstraint("code", name="uq_institutions_code"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(max_length=80, index=True)
    name: str = Field(max_length=255)
    role: InstitutionRole = Field(index=True)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    def __init__(self, **data: Any) -> None:
        if isinstance(data.get("code"), str):
            data["code"] = self.normalize_code(data["code"])
        if isinstance(data.get("name"), str):
            data["name"] = self.normalize_name(data["name"])
        super().__init__(**data)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Institution code must not be empty.")
        return normalized

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Institution name must not be empty.")
        return normalized

    @validates("code")
    def validate_code_assignment(self, key: str, value: str) -> str:
        return self.normalize_code(value)

    @validates("name")
    def validate_name_assignment(self, key: str, value: str) -> str:
        return self.normalize_name(value)


class ReportInstitutionLink(SQLModel, table=True):
    """Append-only relationship history between reports and institutions."""

    __tablename__: ClassVar[str] = "report_institution_links"
    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "institution_id",
            "relationship_type",
            name="uq_report_institution_relationship",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    report_id: UUID = Field(
        foreign_key="citizen_issue_reports.id",
        index=True,
    )
    institution_id: UUID = Field(foreign_key="institutions.id", index=True)
    relationship_type: ReportInstitutionRelationship = Field(index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class InstitutionResponse(SQLModel, table=True):
    """Append-only public response from an institution linked to a report."""

    __tablename__: ClassVar[str] = "institution_responses"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(content)) > 0 AND char_length(content) <= 4000",
            name="ck_institution_responses_content",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    report_institution_link_id: UUID = Field(
        foreign_key="report_institution_links.id",
    )
    content: str = Field(max_length=4000)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    def __init__(self, **data: Any) -> None:
        if isinstance(data.get("content"), str):
            data["content"] = self.normalize_content(data["content"])
        super().__init__(**data)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 4000:
            raise ValueError("Institution response content is invalid.")
        return normalized

    @validates("content")
    def validate_content_assignment(self, key: str, value: str) -> str:
        return self.normalize_content(value)
