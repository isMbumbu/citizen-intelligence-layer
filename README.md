# Citizen Intelligence Layer

Citizen-first intelligence for public spending, projects, evidence, and civic action.

The Citizen Intelligence Layer turns fragmented public budgets, projects,
contracts, expenditure, timelines, and government records into information that
people can understand, verify, and act on.

## Repository layout

```text
.
├── backend/       FastAPI, SQLModel, Celery, and database migrations
├── frontend/      Next.js 16 (React 19, TypeScript, Tailwind CSS) web app
├── principles/    Product and engineering guardrails
├── specs/         Domain and API specifications
└── stories/       Implementation stories and acceptance criteria
```

The backend follows an async, module-oriented structure:

```text
API routes → service → repository → database
```

Routes are deliberately thin. All material facts must retain provenance; AI
output is explanatory rather than authoritative.

## Local development

1. Copy the root environment template: `cp .env.example .env`.
2. Start the stack: `docker compose up --build`.
3. Open FastAPI documentation at <http://localhost:8000/docs>.
4. Check the service at <http://localhost:8000/health>.

Docker Compose runs PostgreSQL with PostGIS and pgvector, Redis, RabbitMQ, the
API, migrations, and a Celery worker. The database extensions are created by
the first Alembic migration; `/health/ready` checks PostgreSQL and Redis. The
backend API uses a development image with source reloads, while migrations and
the worker use the minimal runtime image. See [backend/README.md](backend/README.md)
for the image stages and database-extension rationale.

For backend-only development, follow [backend/README.md](backend/README.md).
For frontend-only development, follow [frontend/README.md](frontend/README.md).

## Development workflow

Before implementing a capability, read its governing principle, specification,
and story. Define acceptance criteria, implement the smallest scoped change,
then run formatting, linting, type checking, and tests. See [AGENTS.md](AGENTS.md)
for the working agreement.

The frontend is a Next.js application that talks to the API through a same-origin
rewrite; see [frontend/README.md](frontend/README.md) for the request flow and
environment configuration.
