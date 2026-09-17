"""Persistence tables for the deliberately narrow project-explorer slice."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKeyConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


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
