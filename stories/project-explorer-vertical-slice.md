# Project explorer vertical slice

## Story

As a resident, I want to browse a small set of clearly labelled demonstration
projects, inspect their sourced facts and review flags, and submit an issue so
I can understand and act on public-project information without mistaking demo
or derived data for verified evidence.

## Governing specifications

- `specs/geography.md`
- `specs/projects.md`
- `specs/finance.md`
- `specs/contracts.md`
- `specs/sources.md`
- `specs/provenance.md`
- `specs/verification.md`
- `specs/intelligence.md`
- `specs/civic-action.md`
- `specs/api.md`

## Acceptance criteria

- A deterministic, idempotent seed command creates four fictional Kenyan demo
  projects, their locations, financial records, contractor details, claims,
  sources, and unverified verification records.
- `GET /api/v1/projects` paginates and filters by county, ward, project type,
  status, and text search.
- A project detail presents location, financial records, contractor, progress,
  timeline, verification, and evidence references without exposing SQLModel
  tables as the API contract.
- Each material seeded financial value, contractor, and progress value has a
  traceable claim and source record.
- A progress-versus-spend flag is derived only from sourced structured values,
  uses `REVIEW_REQUIRED` language, and is never a verification result.
- A valid report for a project is stored as `SUBMITTED`; invalid input and an
  unknown project return stable client errors and contact information is not
  logged.
