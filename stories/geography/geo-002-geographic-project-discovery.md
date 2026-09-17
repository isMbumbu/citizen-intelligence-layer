# GEO-002: Geographic project discovery

## Goal

Allow a resident to select a county, sub-county, or ward and discover the
projects relevant to that place.

## User

Citizen / resident / project explorer user

## Context

The geography model is in place, but residents still need a way to browse and
filter projects based on place. This is the entry point for the public-interest
journey.

## Requirements

- A citizen can browse projects by county and ward.
- The API returns only projects that belong to the selected geography.
- The result can be paginated and filtered.
- Empty results produce a clear empty-state response.

## Acceptance criteria

### AC1: Geographic filters work
Given a valid county, sub-county, or ward selection
When the project listing endpoint runs
Then only records in that geography are returned.

### AC2: Empty states are clear
Given no projects exist for a selected geography
When the list is requested
Then the API returns an empty response and the front-end can show a friendly
empty state.

### AC3: Filters are composable
Given a user selects a county and a ward together
When the project browse endpoint is called
Then the resulting list respects both filters simultaneously.

## Data requirements

- Project records with geographic references
- Geography records from GEO-001

## API requirements

- Extend `GET /api/v1/projects` with geographic filter parameters
- Optionally expose a geography-specific project listing endpoint

## UI requirements

- Location filter control in the project explorer
- Empty-state messaging for no projects in an area

## Provenance requirements

- Geographic filtering is administrative metadata and does not require public
  source data by itself.

## Validation

- Query by county returns matching results.
- Query by ward returns matching results.
- Combined filters reduce the result set correctly.

## Tests

- geography filter returns expected project subset
- combined filters perform correctly
- empty set is handled gracefully

## Non-goals

- Not map rendering or GIS visualisation
- Not geospatial clustering or route analysis
- Not project editing or administrative workflows

## Dependencies

- GEO-001
- PROJ-001

## Definition of done

- Residents can discover relevant projects by location.
- Geographic filters are deterministic and easily testable.
- The product has a usable entry point for the project explorer flow.
