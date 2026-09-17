# FND-003: Demo data seeding

## Goal

Create realistic, deterministic demo data so the project can demonstrate the
citizen journey with real-looking public-sector records without depending on
production data.

## User

Developer / operator / demo viewer

## Context

The project needs a small but credible dataset that allows project browsing,
financial analysis, evidence display, and review signals. The seed must be
repeatable so the app remains stable across local setup and demos.

## Requirements

- Seed realistic Kenyan public-project data.
- Include geographical locations, project records, financial data, and source
  references.
- Produce idempotent seed behavior.
- Include at least one derived review signal based on sourced values.
- Support local demos and product walkthroughs.

## Acceptance criteria

### AC1: Deterministic seed data exists
Given a clean environment
When the seed step is run
Then structured demo records are created for multiple counties and wards.

### AC2: Seed data is idempotent
Given the seed step is run more than once
When the application data is checked
Then the records do not duplicate unexpectedly and the system remains stable.

### AC3: Financial and provenance values are present
Given project records are created
When the seeded data is inspected
Then each material value has a related source or provenance reference.

### AC4: Example intelligence signal is available
Given seeded project values exist
When the review logic is evaluated
Then at least one project demonstrates a review-required signal based on sourced
facts.

## Data requirements

- Project records with name, status, type, location, and timeline data
- At least two counties and multiple wards
- Financial allocations and expenditure values
- Contractor and contract records
- Source records and claim links
- Verification-state records

## API requirements

- No new public API is required specifically for this story.
- The seed data must be queryable through the project and location endpoints.

## UI requirements

- Demo data should be visible through the explorer and project detail screens.

## Provenance requirements

- Each material number or statement should be attributable to a source record.
- Derived numbers should be clearly separated from official records.

## Validation

- Seed command succeeds on clean setup
- Seed command is safe to re-run
- Demo data supports the initial product journey

## Tests

- seed command creates expected records
- duplicate runs do not duplicate records
- one seeded project contains a review signal based on sourced values

## Non-goals

- Not full government-data ingestion
- Not production-quality public record import
- Not AI-generated content without fact anchors

## Dependencies

- FND-001
- FND-002
- GEO-001

## Definition of done

- Seed data is deterministic and idempotent.
- The project is demo-ready for project explorer and project detail flows.
- Source-provenance is present for the seeded facts.
