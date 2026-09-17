"""Add auditable evidence processing history and derived artifacts.

Revision ID: 20260918_0006
Revises: 20260917_0005
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260918_0006"
down_revision = "20260917_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create processing event and derived artifact tables."""
    op.create_table(
        "evidence_processing_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_state", sa.String(length=30), nullable=True),
        sa.Column("to_state", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evidence_processing_events_evidence_id",
        "evidence_processing_events",
        ["evidence_id"],
    )
    op.create_table(
        "evidence_derived_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("content_reference", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("processing_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_class", sa.String(length=40), nullable=False),
        sa.Column("trust_classification", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence_records.id"]),
        sa.ForeignKeyConstraint(
            ["processing_event_id"], ["evidence_processing_events.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evidence_id",
            "artifact_type",
            name="uq_evidence_derived_artifacts_stage",
        ),
        sa.CheckConstraint(
            "source_class = 'CITIZEN_SUBMITTED'",
            name="ck_evidence_derived_artifacts_source_class",
        ),
        sa.CheckConstraint(
            "trust_classification = 'DERIVED_UNVERIFIED_NON_OFFICIAL'",
            name="ck_evidence_derived_artifacts_trust",
        ),
    )
    op.create_index(
        "ix_evidence_derived_artifacts_evidence_id",
        "evidence_derived_artifacts",
        ["evidence_id"],
    )
    op.create_index(
        "ix_evidence_derived_artifacts_processing_event_id",
        "evidence_derived_artifacts",
        ["processing_event_id"],
    )


def downgrade() -> None:
    """Remove processing history and derived artifact tables."""
    op.drop_index(
        "ix_evidence_derived_artifacts_processing_event_id",
        table_name="evidence_derived_artifacts",
    )
    op.drop_index(
        "ix_evidence_derived_artifacts_evidence_id",
        table_name="evidence_derived_artifacts",
    )
    op.drop_table("evidence_derived_artifacts")
    op.drop_index(
        "ix_evidence_processing_events_evidence_id",
        table_name="evidence_processing_events",
    )
    op.drop_table("evidence_processing_events")
