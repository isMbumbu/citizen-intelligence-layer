# GEO-001: Geography hierarchy

## Goal

Represent the public-sector geographic structure needed to browse and filter
projects by place, with clear county → sub-county → ward relationships.

## User

Citizen / developer / product operator

## Context

Public-project information is location-specific. The system needs a stable
geography model to support project discovery and location-based filtering.

## Requirements

- The application stores counties, sub-counties, and wards.
- Each ward belongs to a single sub-county.
- Each sub-county belongs to a single county.
- Geographies remain queryable through API endpoints.
- Related data is stored in a way that supports project discovery by location.

## Acceptance criteria

### AC1: Geography records are created and linked
Given a county, sub-county, and ward dataset exists
When the records are persisted
Then the hierarchy is explicit and queryable.

### AC2: Invalid relationships are not permitted
Given a project or a geographic record is created
When it references a wrong parent relationship
Then the system rejects it with a clear validation or integrity error.

### AC3: Geography can be read by API
Given geography entries exist
When the API endpoint for geographic lookup is called
Then the response contains the hierarchy without leaking database internals.

## Data requirements

- County table
- Sub-county table
- Ward table
- Foreign-key relationship chain

## API requirements

- `GET /api/v1/geography` or equivalent location listing endpoint
- project-scoped geography details on project read

## UI requirements

- Geography selection for filters and project browsing

## Provenance requirements

- Geographical hierarchy records are administrative reference data and do not
  require public-source citations unless they are attached to project metadata.

## Validation

- API returns hierarchy correctly.
- Relationship integrity holds.
- Empty or invalid requests return stable errors.

## Tests

- create geography hierarchy
- fail invalid relationship insertion
- list geography hierarchy from API

## Non-goals

- Not full geospatial analysis or maps
- Not location-based user profiles
- Not a geographic search engine beyond the required hierarchy

## Dependencies

- FND-001
- FND-002

## Definition of done

- Geographic hierarchy is modeled and queryable.
- API supports location-scoped project discovery.
- Geographical relationships are consistent and testable.
