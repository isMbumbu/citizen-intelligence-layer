"""Create VER-003 claim review requests.

Revision ID: 20260918_0011
Revises: 20260918_0010
Create Date: 2026-09-18 00:00:00
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260918_0011"
down_revision = "20260918_0010"
branch_labels = None
depends_on = None

_REQUEST_TYPES = "'CORRECTION', 'REVIEW_APPEAL'"


def upgrade() -> None:
    """Create the append-only claim review request table."""
    op.create_table(
        "claim_review_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_type", sa.String(length=30), nullable=False),
        sa.Column("content", sa.String(length=4000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            f"request_type IN ({_REQUEST_TYPES})",
            name="ck_claim_review_requests_request_type",
        ),
        sa.CheckConstraint(
            "char_length(btrim(content)) > 0 AND char_length(content) <= 4000",
            name="ck_claim_review_requests_content",
        ),
    )
    op.create_index(
        "ix_claim_review_requests_claim_created_at_id",
        "claim_review_requests",
        ["claim_id", "created_at", "id"],
    )


def downgrade() -> None:
    """Remove the claim review request table."""
    op.drop_index(
        "ix_claim_review_requests_claim_created_at_id",
        table_name="claim_review_requests",
    )
    op.drop_table("claim_review_requests")
