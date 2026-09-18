"""Create RESP-001 institution and report relationship tables.

Revision ID: 20260918_0009
Revises: 20260918_0008
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260918_0009"
down_revision = "20260918_0008"
branch_labels = None
depends_on = None

_INSTITUTION_ROLES = "'COUNTY_GOVERNMENT', 'NATIONAL_GOVERNMENT', 'PUBLIC_AGENCY'"
_RELATIONSHIP_TYPES = "'ASSIGNED', 'REFERRED'"


def upgrade() -> None:
    """Create empty institution reference and report-link tables."""
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_institutions_code"),
        sa.CheckConstraint(
            f"role IN ({_INSTITUTION_ROLES})",
            name="ck_institutions_role",
        ),
    )
    op.create_index("ix_institutions_code", "institutions", ["code"])
    op.create_index("ix_institutions_role", "institutions", ["role"])
    op.create_index("ix_institutions_is_active", "institutions", ["is_active"])

    op.create_table(
        "report_institution_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["citizen_issue_reports.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "report_id",
            "institution_id",
            "relationship_type",
            name="uq_report_institution_relationship",
        ),
        sa.CheckConstraint(
            f"relationship_type IN ({_RELATIONSHIP_TYPES})",
            name="ck_report_institution_relationship_type",
        ),
    )
    op.create_index(
        "ix_report_institution_links_report_id",
        "report_institution_links",
        ["report_id"],
    )
    op.create_index(
        "ix_report_institution_links_institution_id",
        "report_institution_links",
        ["institution_id"],
    )
    op.create_index(
        "ix_report_institution_links_relationship_type",
        "report_institution_links",
        ["relationship_type"],
    )


def downgrade() -> None:
    """Remove report links and institution reference data."""
    op.drop_index(
        "ix_report_institution_links_relationship_type",
        table_name="report_institution_links",
    )
    op.drop_index(
        "ix_report_institution_links_institution_id",
        table_name="report_institution_links",
    )
    op.drop_index(
        "ix_report_institution_links_report_id",
        table_name="report_institution_links",
    )
    op.drop_table("report_institution_links")
    op.drop_index("ix_institutions_is_active", table_name="institutions")
    op.drop_index("ix_institutions_role", table_name="institutions")
    op.drop_index("ix_institutions_code", table_name="institutions")
    op.drop_table("institutions")
