# Backend Docker delivery

## Scope

Provide a repeatable, backend-only Docker workflow for the Citizen Intelligence
Layer. This story is governed by `principles/architecture.md`,
`principles/async.md`, `principles/security.md`, and the platform infrastructure
described in `specs/domain-model.md` and `specs/api.md`.

## Acceptance criteria

1. The backend Dockerfile has distinct builder, development, and minimal
   runtime stages, with the runtime process running as an unprivileged user.
2. API, migrations, and the Celery worker use the same backend image definition
   so their Python dependencies cannot drift.
3. Local Compose uses the development target for the API and does not send
   virtual environments, test caches, or environment files to Docker builds.
4. The local PostgreSQL image continues to provide PostGIS and pgvector because
   the initial Alembic migration creates both extensions.
5. `docker compose build` and the migration service complete successfully.
