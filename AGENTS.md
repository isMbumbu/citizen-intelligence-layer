# Citizen Intelligence Layer working agreement

## Scope and workflow

This repository is a monorepo. Product-wide principles, specifications, and
stories belong at the root; backend-only instructions belong in `backend/`.

Before changing a feature:

1. Read the relevant file in `principles/`.
2. Read the matching file in `specs/`.
3. Read or create an implementation story under `stories/` with acceptance
   criteria.
4. Implement the smallest change that satisfies that story.
5. Add focused tests and run the backend checks.

## Engineering rules

- Keep FastAPI routes thin: route → service → repository → database.
- Use SQLModel for persistence models and Pydantic schemas for API contracts.
- Keep database and HTTP work asynchronous; move expensive work to Celery.
- Keep source provenance attached to material facts. AI output is never an
  authoritative source or verification result.
- Use timezone-aware datetimes, UUID primary keys where appropriate, typed
  interfaces, and structured logs without secrets or personal data.
- Do not introduce business features without a corresponding specification and
  story.

## Verification

From `backend/`, run:

```bash
ruff format --check .
ruff check .
mypy app
pytest
```

Use `docker compose up --build` at the root to verify the integrated local
environment. Never commit `.env` files or real credentials.
