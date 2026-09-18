"""Create CIVIC-003 reporting-channel reference data.

Revision ID: 20260918_0008
Revises: 20260918_0007
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260918_0008"
down_revision = "20260918_0007"
branch_labels = None
depends_on = None

_REPORT_CATEGORIES = "'QUALITY', 'DELAY', 'ACCESS', 'SAFETY', 'OTHER'"


def upgrade() -> None:
    """Create the empty reporting-channel reference table."""
    op.create_table(
        "reporting_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("issue_category", sa.String(length=30), nullable=False),
        sa.Column("county_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sub_county_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ward_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("office_name", sa.String(length=160), nullable=False),
        sa.Column("channel_type", sa.String(length=40), nullable=False),
        sa.Column("destination", sa.String(length=512), nullable=False),
        sa.Column("display_label", sa.String(length=160), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["county_id"], ["counties.id"]),
        sa.ForeignKeyConstraint(["sub_county_id"], ["sub_counties.id"]),
        sa.ForeignKeyConstraint(["ward_id"], ["wards.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            f"issue_category IN ({_REPORT_CATEGORIES})",
            name="ck_reporting_channels_issue_category",
        ),
        sa.CheckConstraint(
            "num_nonnulls(county_id, sub_county_id, ward_id) = 1",
            name="ck_reporting_channels_one_geography",
        ),
        sa.CheckConstraint(
            "priority >= 0",
            name="ck_reporting_channels_priority",
        ),
    )
    op.create_index(
        "ix_reporting_channels_issue_category",
        "reporting_channels",
        ["issue_category"],
    )
    op.create_index(
        "ix_reporting_channels_county_id",
        "reporting_channels",
        ["county_id"],
    )
    op.create_index(
        "ix_reporting_channels_sub_county_id",
        "reporting_channels",
        ["sub_county_id"],
    )
    op.create_index(
        "ix_reporting_channels_ward_id",
        "reporting_channels",
        ["ward_id"],
    )
    op.create_index(
        "ix_reporting_channels_priority",
        "reporting_channels",
        ["priority"],
    )
    op.create_index(
        "ix_reporting_channels_is_active",
        "reporting_channels",
        ["is_active"],
    )


def downgrade() -> None:
    """Remove reporting-channel reference data."""
    op.drop_index("ix_reporting_channels_is_active", table_name="reporting_channels")
    op.drop_index("ix_reporting_channels_priority", table_name="reporting_channels")
    op.drop_index("ix_reporting_channels_ward_id", table_name="reporting_channels")
    op.drop_index(
        "ix_reporting_channels_sub_county_id", table_name="reporting_channels"
    )
    op.drop_index("ix_reporting_channels_county_id", table_name="reporting_channels")
    op.drop_index(
        "ix_reporting_channels_issue_category", table_name="reporting_channels"
    )
    op.drop_table("reporting_channels")
