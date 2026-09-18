"""Add auditable citizen report status transitions.

Revision ID: 20260918_0007
Revises: 20260918_0006
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260918_0007"
down_revision = "20260918_0006"
branch_labels = None
depends_on = None

_REPORT_STATES = (
    "'SUBMITTED', 'UNDER_REVIEW', 'REFERRED', 'RESPONDED', 'RESOLVED', 'CLOSED'"
)


def upgrade() -> None:
    """Expand report statuses and create transition history."""
    op.drop_constraint(
        "ck_citizen_issue_reports_status",
        "citizen_issue_reports",
        type_="check",
    )
    op.create_check_constraint(
        "ck_citizen_issue_reports_status",
        "citizen_issue_reports",
        f"status IN ({_REPORT_STATES})",
    )
    op.create_table(
        "citizen_report_status_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=False),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["citizen_issue_reports.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            f"from_status IN ({_REPORT_STATES})",
            name="ck_report_status_transitions_from_status",
        ),
        sa.CheckConstraint(
            f"to_status IN ({_REPORT_STATES})",
            name="ck_report_status_transitions_to_status",
        ),
    )
    op.create_index(
        "ix_citizen_report_status_transitions_report_id",
        "citizen_report_status_transitions",
        ["report_id"],
    )
    op.create_index(
        "ix_citizen_report_status_transitions_created_at",
        "citizen_report_status_transitions",
        ["created_at"],
    )


def downgrade() -> None:
    """Remove report transition history and restore submission-only status."""
    op.drop_index(
        "ix_citizen_report_status_transitions_created_at",
        table_name="citizen_report_status_transitions",
    )
    op.drop_index(
        "ix_citizen_report_status_transitions_report_id",
        table_name="citizen_report_status_transitions",
    )
    op.drop_table("citizen_report_status_transitions")
    op.drop_constraint(
        "ck_citizen_issue_reports_status",
        "citizen_issue_reports",
        type_="check",
    )
    op.create_check_constraint(
        "ck_citizen_issue_reports_status",
        "citizen_issue_reports",
        "status = 'SUBMITTED'",
    )
