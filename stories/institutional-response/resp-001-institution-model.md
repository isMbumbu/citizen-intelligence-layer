# RESP-001: Institution model

## Goal

Represent public institutions that may be explicitly assigned or referred a citizen issue report.

## User

Reviewer / internal civic-action service

## Context

CIVIC-001 stores citizen issue reports, CIVIC-002 tracks report status and transition history, and CIVIC-003 exposes informational reporting channels. RESP-001 adds institution reference data and explicit report relationships without changing the report table or deriving links from reporting channels.

## Requirements

- Store institutions as reference data with stable UUIDs.
- Give each institution a normalized, stable, unique internal code.
- Store a trimmed public institution name.
- Classify each institution with exactly one controlled role:
  - `COUNTY_GOVERNMENT`
  - `NATIONAL_GOVERNMENT`
  - `PUBLIC_AGENCY`
- Allow multiple institution relationships for one report.
- Represent each relationship as `ASSIGNED` or `REFERRED`.
- Preserve relationship creation time as a timezone-aware UTC timestamp.
- Keep institution linking as an internal service capability.
- Do not add `institution_id` to `CitizenIssueReport`.
- Do not derive links from `ReportingChannel`.
- Do not change report status or create status-transition history when a relationship is created.
- Inactive institutions cannot receive new relationships, but existing relationships remain readable.

## Data requirements

### Institution

- `id`: UUID primary key.
- `code`: required internal-only string, normalized and stable, unique, maximum 80 characters.
- `name`: required public string, trimmed and non-empty, maximum 255 characters.
- `role`: required controlled role value.
- `is_active`: required boolean, default `true`.
- `created_at`: required timezone-aware UTC timestamp.

No organizational hierarchy, contact directory, address, credentials, actor metadata, or unnecessary operational fields are stored.

### ReportInstitutionLink

- `id`: UUID primary key.
- `report_id`: required foreign key to `citizen_issue_reports.id`.
- `institution_id`: required foreign key to `institutions.id`.
- `relationship_type`: required controlled value, `ASSIGNED` or `REFERRED`.
- `created_at`: required timezone-aware UTC timestamp.
- Unique constraint on `(report_id, institution_id, relationship_type)`.
- Indexes support report and institution lookups.

## API requirements

- `GET /api/v1/reports/{report_id}/institutions` returns deterministic public institution relationships.
- Each response item contains only institution ID, institution name, institution role, and relationship type.
- Unknown reports return the existing `404 Report not found.` response.
- A valid report with no relationships returns `200 []`.
- Institution linking is an internal service operation and has no public mutation endpoint.

## Service requirements

Implement `link_report_to_institution(session, report_id, institution_id, relationship_type)`.

- Unknown report returns the existing stable not-found behavior.
- Unknown institution returns a stable not-found behavior.
- Inactive institutions cannot receive new links.
- Duplicate relationships return a deterministic conflict or validation error.
- A valid request persists exactly one link.
- Linking does not change report status, create a status-transition record, or create reporting-channel records.

## Privacy and security

Public report-institution responses must not expose institution code, citizen contact information, report descriptions, evidence or provenance internals, actor/request metadata, or internal operational fields. No credentials, authentication, authorization, or actor attribution is introduced by this story.

## Migration

Create a migration after `20260918_0008` with reversible creation and removal of `institutions` and `report_institution_links`, including approved primary keys, foreign keys, indexes, and uniqueness constraints.

Do not modify prior migrations, `citizen_issue_reports`, `citizen_report_status_transitions`, `reporting_channels`, or project/geography tables.

## Seed data

Do not add production institution rows. Use synthetic fixtures only in tests.

## Tests

Cover valid institution data, exact role validation, code uniqueness, assignment, referral, multiple institutions, duplicate relationships, inactive institutions, unknown reports and institutions, empty lookups, deterministic ordering, public field restrictions, code/contact/description privacy, unchanged report status, absent transition history, no channel-to-institution derivation, and regressions for CIVIC-001, CIVIC-002, and CIVIC-003 behavior.

## Dependencies

- CIVIC-001: issue report submission
- CIVIC-002: report status tracking
- CIVIC-003: reporting channels
- GEO-001: geography hierarchy

## Non-goals

- RESP-002 institutional response flow
- RESP-003 right of reply
- institutional response content
- notifications
- case management
- moderation
- authentication or authorization
- actor attribution
- institution administration endpoints
- frontend
- AI
- external government data integration
- automatic referral
- automatic status transitions
- channel-to-institution resolution
- institution contacts or directories

## Definition of done

- Institution and report-link models are registered for persistence metadata.
- Internal linking service enforces report, institution, active-state, and duplicate rules.
- The public read endpoint returns only the approved institution relationship fields.
- Migration upgrade, downgrade, and re-upgrade are reversible and verified.
- Focused and adjacent civic-action tests pass without changing prior story behavior.
