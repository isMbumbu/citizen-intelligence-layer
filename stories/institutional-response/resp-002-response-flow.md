# RESP-002: Response flow

## Status

Approved contract. No implementation is included in this story draft.

## Goal

Store and publicly show institution responses alongside citizen issue reports while preserving the original citizen report and its existing evidence unchanged.

## Roadmap authority

The roadmap defines two RESP-002 requirements:

- Institution responses are stored and shown alongside issues.
- The original citizen report and evidence are preserved.

This story makes the smallest explicit contract consistent with those requirements, RESP-001, CIVIC-001, CIVIC-002, and the existing evidence/provenance boundaries.

## Approved decisions

- Responses are separate records and are not columns on `CitizenIssueReport`.
- A response must reference an existing `ReportInstitutionLink`.
- Both `ASSIGNED` and `REFERRED` relationships may produce responses.
- Multiple responses are allowed for one report and one institution relationship, including duplicate response content.
- Responses are append-only. They cannot be edited or deleted in RESP-002.
- A stored response is public-readable; no separate response visibility or moderation workflow is introduced.
- Response creation is an internal service capability. There is no public mutation endpoint.
- Reading responses is public and report-scoped.
- Creating a response does not change `CitizenIssueReport.status` and does not create a `CitizenReportStatusTransition`.
- Response creation does not create or modify `ReportingChannel` or `EvidenceRecord` rows.
- RESP-002 does not attach evidence to responses. Existing citizen evidence remains linked to the original report and retains its existing classification and lifecycle.

These decisions are final for RESP-002 and must not be expanded during implementation.

## Data model

### InstitutionResponse

Create one table named `institution_responses` with only these fields:

- `id`: UUID primary key.
- `report_institution_link_id`: required UUID foreign key to `report_institution_links.id`.
- `content`: required trimmed, non-empty text, maximum 4000 characters.
- `created_at`: required timezone-aware UTC timestamp.

The link foreign key supplies both the report and institution relationship. Duplicating `report_id` or `institution_id` on the response would permit inconsistent ownership and is unnecessary for this story.

### Cardinality

- One response belongs to exactly one existing `ReportInstitutionLink`.
- A report may have zero, one, or many responses.
- One institution may have zero, one, or many responses for the same report.
- No uniqueness constraint prevents multiple responses for one report/institution link.

### Ordering

Public responses are ordered by `created_at` ascending, then `id` ascending as the deterministic tie-breaker. The database must have the exact index `(report_institution_link_id, created_at, id)` to support relationship lookup and ordering.

### Mutability and deletion

Responses are append-only for RESP-002. No update or delete service, route, migration state, or soft-delete field is introduced. Corrections, withdrawal, moderation, and right of reply require a later approved story.

## Relationship to RESP-001

- A response requires an existing `ReportInstitutionLink`.
- Both `ASSIGNED` and `REFERRED` links are eligible.
- The response stores the link ID, not a separate institution ID or report ID.
- The existing link must belong to the requested report.
- The link relationship type is returned with the public response for context.
- Reporting channels are not consulted and cannot create response records.
- RESP-001 institution codes remain internal-only.

### Inactive institutions

RESP-001 prohibits new links to inactive institutions and keeps existing links readable. RESP-002 applies the same boundary: inactive institutions must not create new responses through existing links, while historical responses remain readable.

## Access model

- Response creation is an internal service capability, for example `create_institution_response(session, report_id, institution_id, content)`.
- The service must resolve the existing link and must not accept an arbitrary unlinked institution.
- No authentication, authorization, actor, or institution-user model is introduced.
- There is no public response create, update, or delete endpoint.
- Public reads are report-scoped and expose only the approved response fields.

## API contract

### Public read

`GET /api/v1/reports/{report_id}/responses`

Response: `200` with a list ordered by response creation time and ID. Each item contains only:

- `response_id`
- `institution_id`
- `institution_name`
- `institution_role`
- `relationship_type`
- `content`
- `created_at`

Unknown report: existing stable `404 Report not found.` response.

Known report with no responses: `200 []`.

No institution code, report description, contact information, evidence internals, actor data, request metadata, or internal operational fields are returned.

### Internal mutation

No HTTP endpoint is exposed. The internal service operation accepts:

- `report_id`
- `institution_id`
- `content`

The service resolves the relationship and persists one response. It does not accept a relationship type separately because the existing RESP-001 link is authoritative.

Stable failures:

- Unknown report: `404 Report not found.`
- Unknown institution: `404 Institution not found.`
- Institution is not linked to the report: `409 Institution is not linked to this report.`
- Linked institution is inactive: `422 Institution is inactive.`
- Empty or overlong content: `422 The institution response is invalid.`

No response creation failure may expose database, credential, actor, or request details.

## CIVIC-002 interaction

- Creating a response does not change report status.
- Creating a response does not create a `CitizenReportStatusTransition` row.
- There is no automatic `REFERRED` transition.
- There is no automatic `RESPONDED` transition.
- Responses are allowed for every existing report status, including `CLOSED`. RESP-002 does not own the report lifecycle.
- Existing explicit CIVIC-002 transitions remain the only status mutation path.

## Privacy and provenance

Public response fields are limited to the response ID, public institution identity, relationship type, response content, and creation timestamp.

The public response must exclude:

- citizen contact information
- the citizen report description unless separately returned by the existing report contract
- internal institution code
- internal notes
- actor identity
- request metadata
- credentials
- moderation or operational metadata
- storage keys and evidence-processing internals

Institution response content is institutional-submitted information, not an official verification result and not a replacement for the citizen report. It must remain separate from citizen-submitted evidence and official source records.

## Evidence

RESP-002 preserves existing report evidence but does not add response evidence references, uploads, retrieval, moderation, OCR, or provenance processing. The existing `EvidenceRecord` model and its `report_id` relationship remain unchanged.

The evidence specification's institutional-response evidence class is recognized as a future provenance category, but no evidence workflow is invented here.

## Migration

Create one reversible migration after the current head:

- `institution_responses`
  - `id` UUID primary key
  - `report_institution_link_id` UUID non-null foreign key to `report_institution_links.id`
  - `content` string/text non-null with a database check that its trimmed value is non-empty and has a maximum length of 4000 characters
  - `created_at` timezone-aware non-null timestamp

Add exactly this index:

- `ix_institution_responses_link_created_at_id` on `(report_institution_link_id, created_at, id)`

No uniqueness constraint may be added for report, institution, link, or content because duplicate responses are allowed. No new enum is required because RESP-002 has no response status or visibility field.

Do not modify prior migrations or existing tables, including `citizen_issue_reports`, `citizen_report_status_transitions`, `institutions`, `report_institution_links`, `reporting_channels`, or `evidence_records`.

The migration must support upgrade, downgrade, and re-upgrade without production response rows being required.

## Seed and fixtures

No production institution or response rows are added. Tests use synthetic reports, institutions, links, responses, and evidence metadata only.

## Tests

The focused RESP-002 test matrix must cover:

- valid response creation through an existing assigned link
- valid response creation through an existing referred link
- multiple responses for one report and institution relationship
- multiple institution relationships and response ordering
- empty and overlong content validation
- unknown report
- unknown institution
- institution not linked to the report
- inactive institution behavior after approval
- public GET route is read-only
- public empty result is `200 []`
- deterministic `created_at`, then ID ordering
- response payload excludes institution code and private report fields
- response payload excludes contact information, actor/request metadata, credentials, internal notes, and evidence internals
- response creation leaves report status unchanged
- response creation creates no CIVIC-002 transition history
- no automatic `REFERRED` or `RESPONDED` transition
- original citizen report remains unchanged
- original citizen evidence remains unchanged and distinct
- reporting channels do not create responses
- no update or delete behavior is exposed
- regression coverage for RESP-001 institution/link lookup and CIVIC-001/CIVIC-002 behavior
- migration upgrade, downgrade, and re-upgrade

## Dependencies

- RESP-001 institution and report-link model
- CIVIC-001 issue report submission
- CIVIC-002 status tracking
- EVD-001/EVD-002/EVD-003 evidence metadata and lifecycle boundaries

## Explicit non-goals

- RESP-003 right of reply
- notifications
- case management
- moderation
- institution authentication or authorization
- actor identity or attribution
- institution administration
- public response mutation endpoints
- response editing or deletion
- response evidence upload or attachment workflow
- frontend
- AI
- external government integrations
- automatic referral
- automatic report status transitions
- channel-to-institution or channel-to-response resolution
- official verification of an institutional response
- new institution hierarchy, contacts, or directories

## Definition of done

- The approved RESP-002 contract is implemented without introducing response status, visibility, actor, or authentication fields.
- Institution responses are stored against existing RESP-001 report links.
- Public report response reads are deterministic and privacy-safe.
- Original report, status history, and evidence remain unchanged by response creation.
- No RESP-003 or unrelated workflow is introduced.
- Focused tests, adjacent regressions, and reversible migration checks pass.
