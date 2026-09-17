"""Create citizen comment and comment-report persistence tables.

Revision ID: 20260917_0004
Revises: 20260917_0003
Create Date: 2026-09-17 03:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260917_0004"
down_revision = "20260917_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "citizen_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_comment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("moderation_state", sa.String(length=30), nullable=False),
        sa.Column("visibility", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["citizen_comments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status = 'ACTIVE'", name="ck_citizen_comments_status"),
        sa.CheckConstraint(
            "moderation_state = 'PENDING'",
            name="ck_citizen_comments_moderation_state",
        ),
        sa.CheckConstraint(
            "visibility = 'PUBLIC'",
            name="ck_citizen_comments_visibility",
        ),
    )
    op.create_index(
        "ix_citizen_comments_project_id", "citizen_comments", ["project_id"]
    )
    op.create_index(
        "ix_citizen_comments_parent_comment_id",
        "citizen_comments",
        ["parent_comment_id"],
    )
    op.create_index("ix_citizen_comments_author_id", "citizen_comments", ["author_id"])
    op.create_index("ix_citizen_comments_status", "citizen_comments", ["status"])
    op.create_index(
        "ix_citizen_comments_moderation_state", "citizen_comments", ["moderation_state"]
    )
    op.create_index(
        "ix_citizen_comments_visibility", "citizen_comments", ["visibility"]
    )

    op.create_table(
        "comment_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["citizen_comments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "reason IN ("
            "'SPAM', 'HARASSMENT', 'PERSONAL_INFORMATION', "
            "'INAPPROPRIATE', 'OTHER')",
            name="ck_comment_reports_reason",
        ),
        sa.CheckConstraint(
            "status = 'SUBMITTED'",
            name="ck_comment_reports_status",
        ),
    )
    op.create_index("ix_comment_reports_comment_id", "comment_reports", ["comment_id"])
    op.create_index(
        "ix_comment_reports_reporter_id", "comment_reports", ["reporter_id"]
    )
    op.create_index("ix_comment_reports_reason", "comment_reports", ["reason"])
    op.create_index("ix_comment_reports_status", "comment_reports", ["status"])


def downgrade() -> None:
    op.drop_index("ix_comment_reports_status", table_name="comment_reports")
    op.drop_index("ix_comment_reports_reason", table_name="comment_reports")
    op.drop_index("ix_comment_reports_reporter_id", table_name="comment_reports")
    op.drop_index("ix_comment_reports_comment_id", table_name="comment_reports")
    op.drop_table("comment_reports")
    op.drop_index("ix_citizen_comments_visibility", table_name="citizen_comments")
    op.drop_index("ix_citizen_comments_moderation_state", table_name="citizen_comments")
    op.drop_index("ix_citizen_comments_status", table_name="citizen_comments")
    op.drop_index("ix_citizen_comments_author_id", table_name="citizen_comments")
    op.drop_index(
        "ix_citizen_comments_parent_comment_id", table_name="citizen_comments"
    )
    op.drop_index("ix_citizen_comments_project_id", table_name="citizen_comments")
    op.drop_table("citizen_comments")
