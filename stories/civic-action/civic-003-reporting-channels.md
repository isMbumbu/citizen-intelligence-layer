# CIVIC-003: Reporting channels

## Goal

Show citizens where a report should be sent without introducing institutional
response workflow.

## User

Citizen / reviewer

## Requirements

- Store reporting channels as persisted reference data.
- Match channels by the existing report category and project geography.
- Use ward, sub-county, then county specificity.
- Return only channels at the most specific matching geographic level.
- Support multiple channels in deterministic priority order.
- Exclude inactive channels.
- Derive category and geography from the persisted report and project.
- Keep lookup read-only and informational.

## Acceptance criteria

### AC1: Matching reporting channels are returned

Given a report with a category and a project location
When reporting channels are requested
Then the active channels for the most specific matching geographic scope are
returned.

### AC2: Channel results are deterministic and safe

Given multiple matching channels
When the lookup is performed
Then channels are ordered by priority ascending and ID ascending, and only
citizen-facing channel fields are returned.

## Data requirements

`reporting_channels` contains:

- UUID identifier
- report issue category
- exactly one county, sub-county, or ward reference
- office name
- channel type
- destination
- optional display label
- priority
- active state

## API requirements

- `GET /api/v1/reports/{report_id}/channels`
- Unknown reports return the stable report not-found response.
- No matching active channel returns `200 []`.
- Category and geography are derived from the stored report and project.

## Security and privacy requirements

- Lookup never changes report status or creates referral/history records.
- Do not expose report descriptions, contact information, evidence, provenance,
  actor data, or internal persistence details.
- Do not introduce authentication or authorization.
- Do not invent real authority or contact data.

## Dependencies

- CIVIC-001
- CIVIC-002
- GEO-001
- TAX-001
- TAX-002

## Non-goals

- no institution model
- no report assignment or automatic referral
- no notifications or case management
- no moderation, authentication, or authorization
- no institutional response or right of reply
- no evidence, provenance, AI, search, frontend, or rate limiting changes
- no production channel rows without an approved dataset

## Definition of done

- Persisted channel reference data and migration exist.
- The report-scoped read endpoint applies the approved geography fallback.
- Multiple channels are ordered deterministically and inactive channels are excluded.
- Focused tests cover matching, fallback, privacy, no-match, and non-mutation behavior.
