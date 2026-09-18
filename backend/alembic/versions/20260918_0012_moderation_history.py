"""Create moderation history and widen comment moderation states.

Revision ID: 20260918_0012
Revises: 20260918_0011
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260918_0012"
down_revision = "20260918_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_citizen_comments_moderation_state",
        "citizen_comments",
        type_="check",
    )
    op.create_check_constraint(
        "ck_citizen_comments_moderation_state",
        "citizen_comments",
        "moderation_state IN ('PENDING', 'FLAGGED', 'HIDDEN', 'REMOVED')",
    )
    op.create_table(
        "moderation_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("previous_state", sa.String(length=30), nullable=False),
        sa.Column("resulting_state", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "target_type IN ('COMMENT', 'EVIDENCE')",
            name="ck_moderation_history_target_type",
        ),
        sa.CheckConstraint(
            "action IN ('FLAG', 'HIDE', 'REMOVE', 'RESTORE')",
            name="ck_moderation_history_action",
        ),
        sa.CheckConstraint(
            "reason IN ('SPAM', 'HARASSMENT', 'PERSONAL_INFORMATION', "
            "'MALICIOUS_CONTENT', 'INAPPROPRIATE_CONTENT', 'ABUSE')",
            name="ck_moderation_history_reason",
        ),
        sa.CheckConstraint(
            "previous_state IN ('PENDING', 'FLAGGED', 'HIDDEN', 'REMOVED')",
            name="ck_moderation_history_previous_state",
        ),
        sa.CheckConstraint(
            "resulting_state IN ('PENDING', 'FLAGGED', 'HIDDEN', 'REMOVED')",
            name="ck_moderation_history_resulting_state",
        ),
    )
    op.create_index(
        "ix_moderation_history_target_created_at_id",
        "moderation_history",
        ["target_type", "target_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_moderation_history_target_created_at_id",
        table_name="moderation_history",
    )
    op.drop_table("moderation_history")
    op.drop_constraint(
        "ck_citizen_comments_moderation_state",
        "citizen_comments",
        type_="check",
    )
    op.create_check_constraint(
        "ck_citizen_comments_moderation_state",
        "citizen_comments",
        "moderation_state = 'PENDING'",
    )