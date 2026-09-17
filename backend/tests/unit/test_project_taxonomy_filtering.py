"""Focused behavior tests for TAX-002 project taxonomy filtering."""

from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

import app.api.v1.modules.projects.repository as projects_repository
import app.api.v1.modules.projects.service as projects_service
import app.api.v1.modules.taxonomy.repository as taxonomy_repository
from app.models.vertical_slice import (
    County,
    Project,
    ProjectCategory,
    ProjectSubtype,
    SubCounty,
    Ward,
)

CATEGORY_ID = uuid4()
SUBTYPE_ID = uuid4()
OTHER_CATEGORY_ID = uuid4()


def _category(category_id: object = CATEGORY_ID) -> ProjectCategory:
    return ProjectCategory(
        id=category_id,
        code="ROADS_TRANSPORT",
        name="Roads and transport",
        description="Road infrastructure.",
    )


def _subtype(
    category_id: object = CATEGORY_ID,
    subtype_id: object = SUBTYPE_ID,
) -> ProjectSubtype:
    return ProjectSubtype(
        id=subtype_id,
        category_id=category_id,
        code="ROAD_REHABILITATION",
        name="Road rehabilitation",
        description="Road improvement.",
    )


def _project() -> Project:
    return Project(
        demo_key="taxonomy-filter-project",
        name="Taxonomy filter project",
        description="A project used by TAX-002 tests.",
        category_id=CATEGORY_ID,
        subtype_id=SUBTYPE_ID,
        project_type="ROAD",
        status="PLANNED",
        ward_id=uuid4(),
        planned_start_date=date(2026, 1, 1),
        planned_completion_date=date(2026, 12, 31),
    )


async def _stub_active_taxonomy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_category",
        AsyncMock(return_value=_category()),
    )
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_subtype",
        AsyncMock(return_value=_subtype()),
    )


async def test_category_and_subtype_filters_are_forwarded_together(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _stub_active_taxonomy(monkeypatch)
    list_projects = AsyncMock(return_value=([], 0))
    monkeypatch.setattr(projects_repository, "list_projects", list_projects)

    await projects_service.list_projects(
        AsyncMock(),
        county=None,
        ward=None,
        project_type=None,
        category_id=CATEGORY_ID,
        subtype_id=SUBTYPE_ID,
        project_status=None,
        search=None,
        page=1,
        page_size=20,
    )

    assert list_projects.await_args.kwargs["category_id"] == CATEGORY_ID
    assert list_projects.await_args.kwargs["subtype_id"] == SUBTYPE_ID


async def test_subtype_filter_works_without_category_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _stub_active_taxonomy(monkeypatch)
    list_projects = AsyncMock(return_value=([], 0))
    monkeypatch.setattr(projects_repository, "list_projects", list_projects)

    await projects_service.list_projects(
        AsyncMock(),
        county=None,
        ward=None,
        project_type=None,
        category_id=None,
        subtype_id=SUBTYPE_ID,
        project_status=None,
        search=None,
        page=1,
        page_size=20,
    )

    assert list_projects.await_args.kwargs["category_id"] is None
    assert list_projects.await_args.kwargs["subtype_id"] == SUBTYPE_ID


async def test_taxonomy_filters_preserve_legacy_project_type_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _stub_active_taxonomy(monkeypatch)
    list_projects = AsyncMock(return_value=([], 0))
    monkeypatch.setattr(projects_repository, "list_projects", list_projects)

    await projects_service.list_projects(
        AsyncMock(),
        county=None,
        ward=None,
        project_type="ROAD",
        category_id=CATEGORY_ID,
        subtype_id=None,
        project_status=None,
        search="road",
        page=2,
        page_size=10,
    )

    assert list_projects.await_args.kwargs["project_type"] == "ROAD"
    assert list_projects.await_args.kwargs["search"] == "road"
    assert list_projects.await_args.kwargs["offset"] == 10
    assert list_projects.await_args.kwargs["limit"] == 10


async def test_unknown_or_inactive_category_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_category",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as error:
        await projects_service.list_projects(
            AsyncMock(),
            county=None,
            ward=None,
            project_type=None,
            category_id=CATEGORY_ID,
            subtype_id=None,
            project_status=None,
            search=None,
            page=1,
            page_size=20,
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Project category not found."


async def test_unknown_or_inactive_subtype_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_category",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_subtype",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as error:
        await projects_service.list_projects(
            AsyncMock(),
            county=None,
            ward=None,
            project_type=None,
            category_id=None,
            subtype_id=SUBTYPE_ID,
            project_status=None,
            search=None,
            page=1,
            page_size=20,
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Project subtype not found."


async def test_subtype_must_belong_to_selected_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_category",
        AsyncMock(return_value=_category()),
    )
    monkeypatch.setattr(
        taxonomy_repository,
        "get_active_subtype",
        AsyncMock(return_value=_subtype(OTHER_CATEGORY_ID)),
    )

    with pytest.raises(HTTPException) as error:
        await projects_service.list_projects(
            AsyncMock(),
            county=None,
            ward=None,
            project_type=None,
            category_id=CATEGORY_ID,
            subtype_id=SUBTYPE_ID,
            project_status=None,
            search=None,
            page=1,
            page_size=20,
        )

    assert error.value.status_code == 422
    assert error.value.detail == "Project subtype does not belong to project category."


async def test_repository_adds_category_and_subtype_predicates() -> None:
    class EmptyResult:
        def all(self) -> list[Project]:
            return []

        def one(self) -> int:
            return 0

    class CapturingSession:
        def __init__(self) -> None:
            self.statements: list[object] = []

        async def exec(self, statement: object) -> EmptyResult:
            self.statements.append(statement)
            return EmptyResult()

    session = CapturingSession()
    await projects_repository.list_projects(
        session,  # type: ignore[arg-type]
        county=None,
        ward=None,
        project_type=None,
        category_id=CATEGORY_ID,
        subtype_id=SUBTYPE_ID,
        status=None,
        search=None,
        offset=0,
        limit=20,
    )

    browse_query = str(session.statements[1].compile(dialect=postgresql.dialect()))
    assert "projects.category_id" in browse_query
    assert "projects.subtype_id" in browse_query


def test_project_response_labels_preserve_taxonomy_and_legacy_type() -> None:
    project = _project()
    category = _category()
    subtype = _subtype()
    location = (
        County(id=uuid4(), name="County", code="C"),
        SubCounty(id=uuid4(), county_id=uuid4(), name="Subcounty"),
        Ward(id=uuid4(), sub_county_id=uuid4(), name="Ward"),
    )
    response = projects_service._location_response(location)
    assert response.county == "County"
    assert project.project_type == "ROAD"
    assert projects_service._category_label(category).code == "ROADS_TRANSPORT"
    assert projects_service._subtype_label(subtype).code == "ROAD_REHABILITATION"
    assert project.category_id == category.id
    assert project.subtype_id == subtype.id
