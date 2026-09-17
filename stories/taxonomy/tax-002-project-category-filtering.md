# TAX-002: Project category filtering and county/national support

## Goal

Ensure the project taxonomy supports realistic Kenyan public-sector filtering and
can handle both county and national government projects without hard-coded enum
bloat.

## User

Citizen / reviewer / product operator

## Context

The current project type model is a narrow enum and does not support the richer
classification needed for public-project discovery. The new taxonomy must support
project browsing and filtering without creating a brittle, redeploy-every-time
enum.

## Requirements

- Project records reference category and optional subtype metadata.
- The browse API supports filtering by category and subtype.
- The system supports county and national project records.
- Category metadata is queryable from the project API.
- The design supports future analytics and additional project classes safely.

## Acceptance criteria

### AC1: Filters by category and subtype work
Given project records with taxonomy metadata exist
When a browse request includes the category and subtype filter values
Then only matching projects are returned.

### AC2: County and national projects coexist
Given both county and national project records exist
When the listing API is called
Then both can be retrieved using the same project browsing model.

### AC3: Filter defaults remain stable
Given a project listing request without category or subtype parameters
When it is processed
Then the API returns the default unfiltered list for the valid project scope.

## Data requirements

- `ProjectCategory`
- `ProjectSubtype`
- `Project` relationship to category and subtype
- optional institution or implementing-body reference if introduced later

## API requirements

- extend `GET /api/v1/projects` with category/subtype filters
- expose taxonomy lookups for UI-driven filtering

## UI requirements

- project explorer filters by category and subtype
- project detail shows category and subtype labels

## Security requirements

- taxonomy updates require administrative permissions
- category data is not directly user-editable

## Provenance requirements

- taxonomy is administrative reference data and is not a claim about project truth
- classification must remain separate from evidence and verification

## Tests

- filter by category returns expected project subset
- filter by subtype returns expected subset
- county and national records are both included under the same browse flow
- invalid taxonomy values fail with stable validation errors

## Dependencies

- TAX-001
- PROJ-001

## Non-goals

- not a full public registry service
- not geospatial dashboarding
- not department hierarchy modeling beyond project classification

## Definition of done

- category and subtype filtering works for the project explorer
- taxonomy supports realistic Kenyan public-sector project types
- county and national project use-cases are both supported without enum churn
