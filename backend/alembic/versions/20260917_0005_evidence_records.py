"""Create citizen evidence metadata persistence.

Revision ID: 20260917_0005
Revises: 20260917_0004
Create Date: 2026-09-17 04:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260917_0005"
down_revision = "20260917_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_class", sa.String(length=40), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("moderation_state", sa.String(length=30), nullable=False),
        sa.Column("processing_state", sa.String(length=30), nullable=False),
        sa.Column("visibility", sa.String(length=30), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["comment_id"], ["citizen_comments.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["citizen_issue_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_evidence_records_storage_key"),
        sa.CheckConstraint(
            "source_class = 'CITIZEN_SUBMITTED'",
            name="ck_evidence_records_source_class",
        ),
        sa.CheckConstraint(
            "file_size_bytes >= 0",
            name="ck_evidence_records_file_size",
        ),
        sa.CheckConstraint(
            "moderation_state IN ('PENDING', 'FLAGGED', 'HIDDEN', 'REMOVED')",
            name="ck_evidence_records_moderation_state",
        ),
        sa.CheckConstraint(
            "processing_state IN ('RAW', 'VALIDATION_PASSED', 'EXTRACTED', 'INDEXED', 'FAILED', 'HIDDEN')",
            name="ck_evidence_records_processing_state",
        ),
        sa.CheckConstraint(
            "visibility IN ('PRIVATE', 'PENDING', 'PUBLIC')",
            name="ck_evidence_records_visibility",
        ),
    )
    op.create_index("ix_evidence_records_project_id", "evidence_records", ["project_id"])
    op.create_index("ix_evidence_records_comment_id", "evidence_records", ["comment_id"])
    op.create_index("ix_evidence_records_report_id", "evidence_records", ["report_id"])
    op.create_index("ix_evidence_records_uploader_id", "evidence_records", ["uploader_id"])
    op.create_index("ix_evidence_records_storage_key", "evidence_records", ["storage_key"])
    op.create_index("ix_evidence_records_moderation_state", "evidence_records", ["moderation_state"])
    op.create_index("ix_evidence_records_processing_state", "evidence_records", ["processing_state"])
    op.create_index("ix_evidence_records_visibility", "evidence_records", ["visibility"])
    op.create_index("ix_evidence_records_is_deleted", "evidence_records", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_evidence_records_is_deleted", table_name="evidence_records")
    op.drop_index("ix_evidence_records_visibility", table_name="evidence_records")
    op.drop_index("ix_evidence_records_processing_state", table_name="evidence_records")
    op.drop_index("ix_evidence_records_moderation_state", table_name="evidence_records")
    op.drop_index("ix_evidence_records_storage_key", table_name="evidence_records")
    op.drop_index("ix_evidence_records_uploader_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_report_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_comment_id", table_name="evidence_records")
    op.drop_index("ix_evidence_records_project_id", table_name="evidence_records")
    op.drop_table("evidence_records")