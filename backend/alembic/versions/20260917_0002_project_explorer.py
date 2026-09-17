"""Create project-explorer vertical-slice tables.

Revision ID: 20260917_0002
Revises: 20260917_0001
Create Date: 2026-09-17 00:20:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260917_0002"
down_revision = "20260917_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "counties",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_counties_code"),
    )
    op.create_index("ix_counties_name", "counties", ["name"])
    op.create_index("ix_counties_code", "counties", ["code"])
    op.create_table(
        "sub_counties",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("county_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["county_id"], ["counties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("county_id", "name", name="uq_sub_counties_county_name"),
    )
    op.create_index("ix_sub_counties_county_id", "sub_counties", ["county_id"])
    op.create_index("ix_sub_counties_name", "sub_counties", ["name"])
    op.create_table(
        "wards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sub_county_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["sub_county_id"], ["sub_counties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sub_county_id", "name", name="uq_wards_sub_county_name"),
    )
    op.create_index("ix_wards_sub_county_id", "wards", ["sub_county_id"])
    op.create_index("ix_wards_name", "wards", ["name"])
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("demo_key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("project_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ward_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("planned_start_date", sa.Date(), nullable=False),
        sa.Column("planned_completion_date", sa.Date(), nullable=False),
        sa.Column("actual_start_date", sa.Date(), nullable=True),
        sa.Column("expected_completion_date", sa.Date(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "project_type IN ('ROAD', 'HEALTH', 'WATER', 'EDUCATION')",
            name="ck_projects_type",
        ),
        sa.CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD')",
            name="ck_projects_status",
        ),
        sa.ForeignKeyConstraint(["ward_id"], ["wards.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("demo_key", name="uq_projects_demo_key"),
    )
    op.create_index("ix_projects_demo_key", "projects", ["demo_key"])
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_project_type", "projects", ["project_type"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_ward_id", "projects", ["ward_id"])
    op.create_table(
        "contractors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("demo_key", sa.String(length=80), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("demo_key", name="uq_contractors_demo_key"),
    )
    op.create_index("ix_contractors_demo_key", "contractors", ["demo_key"])
    op.create_index("ix_contractors_legal_name", "contractors", ["legal_name"])
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("demo_key", sa.String(length=100), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_hash", sa.String(length=128), nullable=True),
        sa.Column("storage_reference", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_type IN ('DEMONSTRATION_RECORD', 'OFFICIAL_DOCUMENT', "
            "'OFFICIAL_DATASET', 'CIVIL_SOCIETY_RECORD')",
            name="ck_sources_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("demo_key", name="uq_sources_demo_key"),
    )
    op.create_index("ix_sources_demo_key", "sources", ["demo_key"])
    op.create_table(
        "source_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_key", sa.String(length=160), nullable=False),
        sa.Column("content_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id", "record_key", name="uq_source_records_source_key"
        ),
    )
    op.create_index("ix_source_records_source_id", "source_records", ["source_id"])
    op.create_index("ix_source_records_record_key", "source_records", ["record_key"])
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_kind", sa.String(length=30), nullable=False),
        sa.Column("field_name", sa.String(length=80), nullable=False),
        sa.Column("value_text", sa.String(length=500), nullable=False),
        sa.Column("numeric_value", sa.Numeric(precision=16, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("financial_period", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "claim_kind IN ('FINANCIAL', 'CONTRACTOR', 'PROGRESS', 'VERIFICATION')",
            name="ck_claims_kind",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_claims_project_id", "claims", ["project_id"])
    op.create_index("ix_claims_claim_kind", "claims", ["claim_kind"])
    op.create_index("ix_claims_field_name", "claims", ["field_name"])
    op.create_table(
        "claim_sources",
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_record_id"], ["source_records.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("claim_id", "source_record_id"),
    )
    op.create_table(
        "financial_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=16, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("financial_period", sa.String(length=20), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_financial_records_nonnegative"),
        sa.CheckConstraint(
            "kind IN ('ALLOCATED', 'COMMITTED', 'CONTRACTED', 'SPENT', 'REPORTED')",
            name="ck_financial_records_kind",
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "kind",
            "financial_period",
            name="uq_financial_records_project_kind_period",
        ),
    )
    op.create_index(
        "ix_financial_records_project_id", "financial_records", ["project_id"]
    )
    op.create_index("ix_financial_records_kind", "financial_records", ["kind"])
    op.create_index("ix_financial_records_claim_id", "financial_records", ["claim_id"])
    op.create_table(
        "project_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contractor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("award_reference", sa.String(length=120), nullable=False),
        sa.Column("contract_status", sa.String(length=30), nullable=False),
        sa.Column("contract_start_date", sa.Date(), nullable=True),
        sa.Column("contract_end_date", sa.Date(), nullable=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.ForeignKeyConstraint(["contractor_id"], ["contractors.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_contracts_project_id", "project_contracts", ["project_id"]
    )
    op.create_index(
        "ix_project_contracts_contractor_id", "project_contracts", ["contractor_id"]
    )
    op.create_index("ix_project_contracts_claim_id", "project_contracts", ["claim_id"])
    op.create_table(
        "project_progress_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("reported_at", sa.Date(), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_progress_percentage"
        ),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_progress_updates_project_id",
        "project_progress_updates",
        ["project_id"],
    )
    op.create_index(
        "ix_project_progress_updates_claim_id", "project_progress_updates", ["claim_id"]
    )
    op.create_table(
        "project_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("verification_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('UNVERIFIED', 'PARTIALLY_VERIFIED', 'VERIFIED', 'STALE', 'DISPUTED')",
            name="ck_project_verifications_status",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_project_verifications_project_id", "project_verifications", ["project_id"]
    )
    op.create_index(
        "ix_project_verifications_status", "project_verifications", ["status"]
    )
    op.create_index(
        "ix_project_verifications_source_record_id",
        "project_verifications",
        ["source_record_id"],
    )
    op.create_table(
        "citizen_issue_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact_information", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('QUALITY', 'DELAY', 'ACCESS', 'SAFETY', 'OTHER')",
            name="ck_citizen_issue_reports_category",
        ),
        sa.CheckConstraint(
            "status = 'SUBMITTED'", name="ck_citizen_issue_reports_status"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_citizen_issue_reports_project_id", "citizen_issue_reports", ["project_id"]
    )
    op.create_index(
        "ix_citizen_issue_reports_category", "citizen_issue_reports", ["category"]
    )
    op.create_index(
        "ix_citizen_issue_reports_status", "citizen_issue_reports", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_citizen_issue_reports_status", table_name="citizen_issue_reports")
    op.drop_index(
        "ix_citizen_issue_reports_category", table_name="citizen_issue_reports"
    )
    op.drop_index(
        "ix_citizen_issue_reports_project_id", table_name="citizen_issue_reports"
    )
    op.drop_table("citizen_issue_reports")
    op.drop_index(
        "ix_project_verifications_source_record_id", table_name="project_verifications"
    )
    op.drop_index("ix_project_verifications_status", table_name="project_verifications")
    op.drop_index(
        "ix_project_verifications_project_id", table_name="project_verifications"
    )
    op.drop_table("project_verifications")
    op.drop_index(
        "ix_project_progress_updates_claim_id", table_name="project_progress_updates"
    )
    op.drop_index(
        "ix_project_progress_updates_project_id", table_name="project_progress_updates"
    )
    op.drop_table("project_progress_updates")
    op.drop_index("ix_project_contracts_claim_id", table_name="project_contracts")
    op.drop_index("ix_project_contracts_contractor_id", table_name="project_contracts")
    op.drop_index("ix_project_contracts_project_id", table_name="project_contracts")
    op.drop_table("project_contracts")
    op.drop_index("ix_financial_records_claim_id", table_name="financial_records")
    op.drop_index("ix_financial_records_kind", table_name="financial_records")
    op.drop_index("ix_financial_records_project_id", table_name="financial_records")
    op.drop_table("financial_records")
    op.drop_table("claim_sources")
    op.drop_index("ix_claims_field_name", table_name="claims")
    op.drop_index("ix_claims_claim_kind", table_name="claims")
    op.drop_index("ix_claims_project_id", table_name="claims")
    op.drop_table("claims")
    op.drop_index("ix_source_records_record_key", table_name="source_records")
    op.drop_index("ix_source_records_source_id", table_name="source_records")
    op.drop_table("source_records")
    op.drop_index("ix_sources_demo_key", table_name="sources")
    op.drop_table("sources")
    op.drop_index("ix_contractors_legal_name", table_name="contractors")
    op.drop_index("ix_contractors_demo_key", table_name="contractors")
    op.drop_table("contractors")
    op.drop_index("ix_projects_ward_id", table_name="projects")
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_project_type", table_name="projects")
    op.drop_index("ix_projects_name", table_name="projects")
    op.drop_index("ix_projects_demo_key", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_wards_name", table_name="wards")
    op.drop_index("ix_wards_sub_county_id", table_name="wards")
    op.drop_table("wards")
    op.drop_index("ix_sub_counties_name", table_name="sub_counties")
    op.drop_index("ix_sub_counties_county_id", table_name="sub_counties")
    op.drop_table("sub_counties")
    op.drop_index("ix_counties_code", table_name="counties")
    op.drop_index("ix_counties_name", table_name="counties")
    op.drop_table("counties")
