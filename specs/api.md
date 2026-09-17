# API specification

The API is versioned under `/api/v1`. It exposes an unauthenticated liveness
endpoint at `/health` and a PostgreSQL/Redis-readiness endpoint at
`/health/ready`.
Feature endpoints must define Pydantic request and response schemas before
implementation and must not expose persistence models directly.
