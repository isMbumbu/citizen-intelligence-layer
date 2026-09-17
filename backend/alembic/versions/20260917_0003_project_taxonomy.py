"""Replace the narrow project-type enum with taxonomy reference data.

Revision ID: 20260917_0003
Revises: 20260917_0002
Create Date: 2026-09-17 02:00:00
"""

from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from app.models.taxonomy_reference import (
    PROJECT_CATEGORY_DEFINITIONS,
    PROJECT_SUBTYPE_DEFINITIONS,
    category_id,
    subtype_id,
)

# revision identifiers, used by Alembic.
revision = "20260917_0003"
down_revision = "20260917_0002"
branch_labels = None
depends_on = None

_REFERENCE_TIMESTAMP = datetime(2026, 9, 17, 2, 0, tzinfo=UTC)
_LEGACY_TYPE_MAPPING = {
    "ROAD": ("ROADS_TRANSPORT", "ROAD_REHABILITATION"),
    "HEALTH": ("HEALTH", "HEALTH_FACILITY"),
    "WATER": ("WATER_SANITATION", "WATER_SUPPLY"),
    "EDUCATION": ("EDUCATION", "CLASSROOMS"),
}


def upgrade() -> None:
    op.create_table(
        "project_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_project_categories_code"),
    )
    op.create_index("ix_project_categories_code", "project_categories", ["code"])
    op.create_index("ix_project_categories_name", "project_categories", ["name"])
    op.create_index(
        "ix_project_categories_is_active",
        "project_categories",
        ["is_active"],
    )
    op.create_table(
        "project_subtypes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["project_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_project_subtypes_code"),
        sa.UniqueConstraint(
            "category_id",
            "code",
            name="uq_project_subtypes_category_code",
        ),
        sa.UniqueConstraint(
            "category_id",
            "id",
            name="uq_project_subtypes_category_id",
        ),
    )
    op.create_index(
        "ix_project_subtypes_category_id", "project_subtypes", ["category_id"]
    )
    op.create_index("ix_project_subtypes_code", "project_subtypes", ["code"])
    op.create_index("ix_project_subtypes_name", "project_subtypes", ["name"])
    op.create_index(
        "ix_project_subtypes_is_active",
        "project_subtypes",
        ["is_active"],
    )
    _insert_reference_data()

    op.add_column(
        "projects",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("subtype_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_projects_category_id", "projects", ["category_id"])
    op.create_index("ix_projects_subtype_id", "projects", ["subtype_id"])
    op.create_foreign_key(
        "fk_projects_category",
        "projects",
        "project_categories",
        ["category_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_projects_subtype",
        "projects",
        "project_subtypes",
        ["subtype_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_projects_category_subtype",
        "projects",
        "project_subtypes",
        ["category_id", "subtype_id"],
        ["category_id", "id"],
    )
    _backfill_legacy_project_types()
    op.alter_column(
        "projects",
        "category_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.drop_constraint("ck_projects_type", "projects", type_="check")
    op.alter_column(
        "projects",
        "project_type",
        existing_type=sa.String(length=30),
        nullable=True,
    )


def downgrade() -> None:
    _ensure_legacy_projects_are_downgradeable()
    op.alter_column(
        "projects",
        "project_type",
        existing_type=sa.String(length=30),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_projects_type",
        "projects",
        "project_type IN ('ROAD', 'HEALTH', 'WATER', 'EDUCATION')",
    )
    op.drop_constraint("fk_projects_category_subtype", "projects", type_="foreignkey")
    op.drop_constraint("fk_projects_subtype", "projects", type_="foreignkey")
    op.drop_constraint("fk_projects_category", "projects", type_="foreignkey")
    op.drop_index("ix_projects_subtype_id", table_name="projects")
    op.drop_index("ix_projects_category_id", table_name="projects")
    op.drop_column("projects", "subtype_id")
    op.drop_column("projects", "category_id")
    op.drop_index("ix_project_subtypes_is_active", table_name="project_subtypes")
    op.drop_index("ix_project_subtypes_name", table_name="project_subtypes")
    op.drop_index("ix_project_subtypes_code", table_name="project_subtypes")
    op.drop_index("ix_project_subtypes_category_id", table_name="project_subtypes")
    op.drop_table("project_subtypes")
    op.drop_index("ix_project_categories_is_active", table_name="project_categories")
    op.drop_index("ix_project_categories_name", table_name="project_categories")
    op.drop_index("ix_project_categories_code", table_name="project_categories")
    op.drop_table("project_categories")


def _insert_reference_data() -> None:
    category_table = sa.table(
        "project_categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(length=80)),
        sa.column("name", sa.String(length=160)),
        sa.column("description", sa.String(length=1000)),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    subtype_table = sa.table(
        "project_subtypes",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("category_id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(length=80)),
        sa.column("name", sa.String(length=160)),
        sa.column("description", sa.String(length=1000)),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        category_table,
        [
            {
                "id": category_id(definition.code),
                "code": definition.code,
                "name": definition.name,
                "description": definition.description,
                "is_active": True,
                "created_at": _REFERENCE_TIMESTAMP,
                "updated_at": _REFERENCE_TIMESTAMP,
            }
            for definition in PROJECT_CATEGORY_DEFINITIONS
        ],
    )
    op.bulk_insert(
        subtype_table,
        [
            {
                "id": subtype_id(definition.code),
                "category_id": category_id(definition.category_code),
                "code": definition.code,
                "name": definition.name,
                "description": definition.description,
                "is_active": True,
                "created_at": _REFERENCE_TIMESTAMP,
                "updated_at": _REFERENCE_TIMESTAMP,
            }
            for definition in PROJECT_SUBTYPE_DEFINITIONS
        ],
    )


def _backfill_legacy_project_types() -> None:
    for legacy_type, (category_code, subtype_code) in _LEGACY_TYPE_MAPPING.items():
        statement = sa.text(
            "UPDATE projects "
            "SET category_id = :category_id, subtype_id = :subtype_id "
            "WHERE project_type = :legacy_type"
        ).bindparams(
            category_id=category_id(category_code),
            subtype_id=subtype_id(subtype_code),
            legacy_type=legacy_type,
        )
        op.execute(statement)


def _ensure_legacy_projects_are_downgradeable() -> None:
    unsupported_project = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM projects "
                "WHERE project_type IS NULL "
                "OR project_type NOT IN ('ROAD', 'HEALTH', 'WATER', 'EDUCATION') "
                "LIMIT 1"
            )
        )
        .scalar()
    )
    if unsupported_project is not None:
        raise RuntimeError(
            "Cannot downgrade project taxonomy while projects use taxonomy-only "
            "or non-legacy project types."
        )
