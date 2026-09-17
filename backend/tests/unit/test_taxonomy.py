"""Focused behavior tests for TAX-001 project taxonomy reference data."""

import importlib.util
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

import app.api.v1.modules.taxonomy.service as taxonomy_service
from app.api.v1.modules.taxonomy import repository as taxonomy_repository
from app.api.v1.modules.taxonomy.schemas import ProjectCategoryResponse
from app.api.v1.modules.taxonomy.service import _category_responses
from app.main import app
from app.models.taxonomy_reference import (
    PROJECT_CATEGORY_DEFINITIONS,
    PROJECT_SUBTYPE_DEFINITIONS,
    category_id,
    subtype_id,
)
from app.models.vertical_slice import Project, ProjectCategory, ProjectSubtype


def _category(*, active: bool = True) -> ProjectCategory:
    return ProjectCategory(
        id=category_id("ROADS_TRANSPORT"),
        code="ROADS_TRANSPORT",
        name="Roads and transport",
        description="Roads and transport infrastructure.",
        is_active=active,
    )


def _subtype(
    category: ProjectCategory,
    *,
    active: bool = True,
) -> ProjectSubtype:
    return ProjectSubtype(
        id=subtype_id("ROAD_REHABILITATION"),
        category_id=category.id,
        code="ROAD_REHABILITATION",
        name="Road rehabilitation",
        description="Improvement of an existing public road.",
        is_active=active,
    )


def test_initial_taxonomy_is_deterministic_and_covers_the_required_categories() -> None:
    """The migration bootstrap vocabulary is stable, compact, and Kenya-aware."""
    category_codes = {definition.code for definition in PROJECT_CATEGORY_DEFINITIONS}
    subtype_codes = {definition.code for definition in PROJECT_SUBTYPE_DEFINITIONS}

    assert len(category_codes) == len(PROJECT_CATEGORY_DEFINITIONS)
    assert len(subtype_codes) == len(PROJECT_SUBTYPE_DEFINITIONS)
    assert category_codes >= {
        "ROADS_TRANSPORT",
        "WATER_SANITATION",
        "HEALTH",
        "EDUCATION",
        "AGRICULTURE",
        "ENERGY_ELECTRIFICATION",
        "WASTE_MANAGEMENT",
        "OTHER",
    }
    assert {
        definition.category_code for definition in PROJECT_SUBTYPE_DEFINITIONS
    } <= category_codes
    assert category_id("ROADS_TRANSPORT") == category_id("ROADS_TRANSPORT")
    assert subtype_id("ROAD_REHABILITATION") == subtype_id("ROAD_REHABILITATION")


def test_category_hierarchy_keeps_subtypes_with_their_parent() -> None:
    """A hierarchy response only attaches a subtype to its own category."""
    category = _category()
    other_category = ProjectCategory(
        id=uuid4(),
        code="WATER_SANITATION",
        name="Water and sanitation",
        description="Water infrastructure.",
    )
    response = _category_responses(
        [category, other_category],
        [_subtype(category)],
    )

    assert response[0].code == "ROADS_TRANSPORT"
    assert [subtype.code for subtype in response[0].subtypes] == ["ROAD_REHABILITATION"]
    assert response[1].subtypes == []


async def test_inactive_reference_data_is_not_returned_to_public_taxonomy_clients(
    monkeypatch,
) -> None:
    """The service receives only active reference data from its repository."""
    active_category = _category()
    active_subtype = _subtype(active_category)
    session = AsyncMock()
    monkeypatch.setattr(
        taxonomy_repository,
        "list_active_categories",
        AsyncMock(return_value=[active_category]),
    )
    monkeypatch.setattr(
        taxonomy_repository,
        "list_active_subtypes",
        AsyncMock(return_value=[active_subtype]),
    )

    response = await taxonomy_service.list_categories(session)

    assert [category.code for category in response] == ["ROADS_TRANSPORT"]
    assert [subtype.code for subtype in response[0].subtypes] == ["ROAD_REHABILITATION"]


async def test_taxonomy_repository_queries_only_active_records() -> None:
    """Inactive reference data is deliberately excluded at the data boundary."""

    class EmptyResult:
        def all(self) -> list[object]:
            return []

    class CapturingSession:
        def __init__(self) -> None:
            self.statements: list[object] = []

        async def exec(self, statement: object) -> EmptyResult:
            self.statements.append(statement)
            return EmptyResult()

    session = CapturingSession()
    await taxonomy_repository.list_active_categories(session)  # type: ignore[arg-type]
    await taxonomy_repository.list_active_subtypes(  # type: ignore[arg-type]
        session,
        {uuid4()},
    )
    compiled_queries = [
        str(statement.compile(dialect=postgresql.dialect()))
        for statement in session.statements
    ]

    assert all("is_active IS true" in query for query in compiled_queries)


def test_taxonomy_reference_tables_define_duplicate_prevention_constraints() -> None:
    """Reference codes cannot silently duplicate in persisted taxonomy data."""
    category_constraint_names = {
        constraint.name for constraint in ProjectCategory.__table__.constraints
    }
    subtype_constraint_names = {
        constraint.name for constraint in ProjectSubtype.__table__.constraints
    }

    assert "uq_project_categories_code" in category_constraint_names
    assert "uq_project_subtypes_code" in subtype_constraint_names
    assert "uq_project_subtypes_category_code" in subtype_constraint_names


def test_project_model_accepts_taxonomy_references_without_a_legacy_type() -> None:
    """New projects can use category reference data instead of a fixed enum value."""
    category = _category()
    subtype = _subtype(category)

    project = Project(
        demo_key="taxonomy-compatible-project",
        name="Example public project",
        description="A project classified through database reference data.",
        category_id=category.id,
        subtype_id=subtype.id,
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2027, 1, 1),
        planned_completion_date=date(2027, 6, 30),
    )

    assert project.category_id == category.id
    assert project.subtype_id == subtype.id
    assert project.project_type is None


def test_taxonomy_migration_backfills_every_legacy_project_type() -> None:
    """The migration preserves all values accepted by the previous type constraint."""
    migration_path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "20260917_0003_project_taxonomy.py"
    )
    spec = importlib.util.spec_from_file_location(
        "project_taxonomy_migration", migration_path
    )
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    assert migration._LEGACY_TYPE_MAPPING == {
        "ROAD": ("ROADS_TRANSPORT", "ROAD_REHABILITATION"),
        "HEALTH": ("HEALTH", "HEALTH_FACILITY"),
        "WATER": ("WATER_SANITATION", "WATER_SUPPLY"),
        "EDUCATION": ("EDUCATION", "CLASSROOMS"),
    }


def test_project_category_endpoints_expose_only_scoped_reference_contracts(
    monkeypatch,
) -> None:
    """The public category route returns schemas rather than SQLModel instances."""
    category = _category()
    subtype = _subtype(category)
    response_model = ProjectCategoryResponse(
        id=category.id,
        code=category.code,
        name=category.name,
        description=category.description,
        subtypes=[
            {
                "id": subtype.id,
                "code": subtype.code,
                "name": subtype.name,
                "description": subtype.description,
            }
        ],
    )
    monkeypatch.setattr(
        taxonomy_service,
        "list_categories",
        AsyncMock(return_value=[response_model]),
    )
    monkeypatch.setattr(
        taxonomy_service,
        "list_subtypes",
        AsyncMock(
            side_effect=HTTPException(
                status_code=404,
                detail="Project category not found.",
            )
        ),
    )

    with TestClient(app) as client:
        categories_response = client.get("/api/v1/project-categories")
        missing_response = client.get(f"/api/v1/project-categories/{uuid4()}/subtypes")

    assert categories_response.status_code == 200
    assert categories_response.json() == [
        {
            "id": str(category.id),
            "code": "ROADS_TRANSPORT",
            "name": "Roads and transport",
            "description": "Roads and transport infrastructure.",
            "subtypes": [
                {
                    "id": str(subtype.id),
                    "code": "ROAD_REHABILITATION",
                    "name": "Road rehabilitation",
                    "description": "Improvement of an existing public road.",
                }
            ],
        }
    ]
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Project category not found."}
