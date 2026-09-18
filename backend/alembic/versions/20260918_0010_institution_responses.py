"""Create RESP-002 institution responses.

Revision ID: 20260918_0010
Revises: 20260918_0009
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260918_0010"
down_revision = "20260918_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the append-only institution response table."""
    op.create_table(
        "institution_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "report_institution_link_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("content", sa.String(length=4000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["report_institution_link_id"],
            ["report_institution_links.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "char_length(btrim(content)) > 0 AND char_length(content) <= 4000",
            name="ck_institution_responses_content",
        ),
    )
    op.create_index(
        "ix_institution_responses_link_created_at_id",
        "institution_responses",
        ["report_institution_link_id", "created_at", "id"],
    )


def downgrade() -> None:
    """Remove the institution response table."""
    op.drop_index(
        "ix_institution_responses_link_created_at_id",
        table_name="institution_responses",
    )
    op.drop_table("institution_responses")
