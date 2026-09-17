# Citizen Intelligence Layer backend

The backend is an async FastAPI application structured like the existing
`sfnotifications` service: shared infrastructure in `app/core`, feature modules
under `app/api/v1/modules`, SQLModel persistence models in `app/models`, Celery
tasks in `app/tasks`, and Alembic migrations in `alembic`.

## Local commands

Install Python 3.12+ dependencies, then run:

```bash
python -m pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

Run quality checks with:

```bash
ruff format --check .
ruff check .
mypy app
pytest
```

For the complete local stack, run `docker compose up --build` from the
repository root. API documentation is available at `/docs`; `/health` checks
process liveness and `/health/ready` checks asynchronous PostgreSQL and Redis
access.

## Docker layout

`Dockerfile` is the single multistage image definition for the API, migrations,
and Celery worker:

- `builder` creates the production virtual environment.
- `development` adds the backend development tools and is used by Compose for
  the API. Its source bind mount enables Uvicorn reloads as files change.
- `runtime` contains only the application, Alembic migrations, and production
  dependencies. It is the default target and runs as `appuser`.

The root Compose file uses `runtime` for migrations and the worker, so they use
the same package set as a deployable API image. It keeps PostgreSQL in
`backend/postgres` because the first migration enables the PostGIS and pgvector
extensions; a plain `postgres` image would fail that migration.

## Boundaries

Each future feature module owns its routes, schemas, repository, and service.
Routes validate transport concerns, services hold use cases, and repositories
perform persistence work. SQLModel models are persistence-only; public API
contracts use Pydantic schemas. Expensive ingestion, document, embedding, and
AI operations belong in Celery tasks, never request handlers.
