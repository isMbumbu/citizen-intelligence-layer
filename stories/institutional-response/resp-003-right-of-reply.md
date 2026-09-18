# RESP-003: Right of reply

## Status

Approved contract. No implementation is included in this story draft.

## Goal

Allow the public to compare a citizen issue with the existing institutional response that contests or clarifies it, while keeping the citizen issue and institutional response as separate, auditable information types.

## Roadmap authority

The roadmap defines RESP-003 as:

- Goal: allow institutions to contest or clarify information.
- Acceptance criterion: a response remains separate from the original claim and can be audited.
- Acceptance criterion: the public can compare the original issue against the institution response.

## Chosen scope

RESP-003 reuses the approved RESP-002 `InstitutionResponse` record and adds a read-only comparison contract. It does not introduce another persistent reply, claim, version, or audit entity.

This is the smallest contract that satisfies the roadmap because RESP-002 already provides:

- an append-only response record
- an existing `ReportInstitutionLink` ownership boundary
- institution identity and relationship type
- a stable response ID and UTC creation timestamp
- public response reads

The term “original claim” in this story means the citizen issue represented by `CitizenIssueReport` and its public category and description. It does not mean the official `Claim` model, which has no relationship to citizen issue reports in the existing domain model.

## Data model

No new table or persistent entity is introduced by RESP-003.

The existing relationship remains authoritative:

`CitizenIssueReport -> ReportInstitutionLink -> InstitutionResponse`

`InstitutionResponse` remains the only institutional response record and retains exactly its RESP-002 fields:

- `id`: UUID primary key
- `report_institution_link_id`: foreign key to an existing `ReportInstitutionLink`
- `content`: trimmed, non-empty text with a maximum of 4000 characters
- `created_at`: timezone-aware UTC timestamp

Responses remain append-only and auditable through their stable ID, existing institution link, content, and creation timestamp. No actor attribution, edit history, response status, visibility state, deletion field, or second reply table is added.

### Cardinality and ordering

- A comparison belongs to one existing citizen report.
- A report may have zero, one, or many existing institution responses.
- Multiple responses for the same report/institution relationship remain allowed.
- Responses are ordered by `created_at` ascending, then response `id` ascending.
- No uniqueness or mutation rule changes from RESP-002.

## Relationship to RESP-001 and RESP-002

- RESP-001 `Institution` and `ReportInstitutionLink` remain unchanged.
- RESP-002 `InstitutionResponse` remains the source of institutional response content.
- Responses must already be associated with the requested report through `ReportInstitutionLink`.
- Both `ASSIGNED` and `REFERRED` links remain valid because RESP-002 already permits both.
- Inactive institutions cannot create new responses under RESP-002; existing responses remain readable and appear in comparison results.
- `ReportingChannel` is not consulted and cannot create or alter comparison results.
- No competing institutional relationship model is introduced.

## Public comparison API

### Endpoint

`GET /api/v1/reports/{report_id}/comparison`

This is a public, read-only endpoint. It returns the original issue and its existing institution responses as separately identifiable objects in one comparison envelope.

### Success response

A known report returns `200` with this shape:

```json
{
  "issue": {
    "report_id": "uuid",
    "category": "QUALITY",
    "description": "The citizen-submitted issue description.",
    "submitted_at": "2026-09-18T00:00:00Z"
  },
  "responses": [
    {
      "response_id": "uuid",
      "institution_id": "uuid",
      "institution_name": "Public Office",
      "institution_role": "PUBLIC_AGENCY",
      "relationship_type": "ASSIGNED",
      "content": "The institution response.",
      "created_at": "2026-09-18T01:00:00Z"
    }
  ]
}
```

The `responses` list is empty when the report has no institution responses: `200 {"issue": {...}, "responses": []}`.

Responses use the RESP-002 deterministic order: `created_at ASC`, then `response_id ASC`.

### Unknown resource behavior

An unknown report returns the existing stable response:

- HTTP `404`
- detail: `Report not found.`

Responses are loaded through the report relationship. Orphaned or unrelated response records must not appear in another report's comparison.

### Public fields

The comparison issue object contains only:

- `report_id`
- `category`
- `description`
- `submitted_at`

The comparison response objects contain only the approved RESP-002 public fields:

- `response_id`
- `institution_id`
- `institution_name`
- `institution_role`
- `relationship_type`
- `content`
- `created_at`

The issue description is public in this comparison contract because the roadmap explicitly requires public comparison with the original issue. This endpoint does not expose the report's contact information.

The public response must never expose:

- citizen contact information
- institution code
- actor identity or request metadata
- credentials
- internal notes
- evidence or provenance internals
- storage keys
- moderation or operational metadata
- raw persistence objects

The issue and response remain separately labelled as citizen-submitted issue content and institutional response content. Neither is presented as an official verification result.

## Creation and mutation

RESP-003 introduces no new mutation operation.

Institution response creation continues to use the internal RESP-002 service capability and all RESP-002 rules remain in force:

- creation requires an existing report and `ReportInstitutionLink`
- both `ASSIGNED` and `REFERRED` relationships are eligible
- inactive institutions cannot create new responses
- content is trimmed, non-empty, and limited to 4000 characters
- no public unauthenticated mutation endpoint exists
- no response editing or deletion exists

The comparison endpoint only reads `CitizenIssueReport`, `ReportInstitutionLink`, `Institution`, and `InstitutionResponse` data.

## CIVIC-002 status and history

RESP-003 leaves CIVIC-002 unchanged:

- comparison does not change report status
- comparison does not create status history
- existing response creation does not change report status
- no automatic `REFERRED`, `RESPONDED`, `RESOLVED`, or `CLOSED` transition is introduced
- reports in every existing status, including `CLOSED`, may be compared

## Evidence and provenance

RESP-003 introduces no evidence relationship, upload, retrieval, moderation, verification, or provenance workflow.

The original report and its existing citizen-submitted evidence remain unchanged and separate from `InstitutionResponse`. The comparison response contains neither evidence records nor evidence-processing metadata.

Institution response content remains institutional-submitted information, not an official source or verification result.

## Privacy and access

- Public comparison is allowed because its fields are explicitly limited and safe for public display.
- No authentication or authorization system is introduced.
- No actor or institution-user model is introduced.
- No internal institution code, contact data, credentials, private notes, or operational metadata is returned.
- The citizen contact field remains stored only on the report and is excluded from the comparison contract.
- Existing RESP-002 public response privacy rules remain unchanged.

## Migration and seed data

No new migration is required.

RESP-003 adds no tables, columns, enums, foreign keys, indexes, constraints, or seed rows. Existing RESP-001 and RESP-002 migrations remain untouched, including `institution_responses` migration `20260918_0010`.

No production seed data is added. Existing synthetic fixtures remain sufficient for comparison tests.

## Tests

Focused RESP-003 tests must cover:

- known report with one existing institution response
- known report with multiple responses
- comparison ordering by `created_at`, then response ID
- known report with no responses returns `200` and an empty `responses` list
- unknown report returns `404 Report not found.`
- issue and institution responses are returned as separate identifiable objects
- public issue fields are limited to report ID, category, description, and submission time
- public response fields match the RESP-002 safe payload exactly
- citizen contact information is absent
- institution code is absent
- actor/request metadata, credentials, internal notes, evidence internals, and operational metadata are absent
- existing report object remains unchanged
- existing `InstitutionResponse` records remain unchanged
- existing evidence remains unchanged and separate
- comparison does not change report status or create status history
- comparison does not derive data from `ReportingChannel`
- RESP-001 institution/link ownership remains authoritative
- RESP-002 response creation and public response behavior remain unchanged
- CIVIC-001/CIVIC-002/CIVIC-003 regression behavior remains unchanged

No tests are required for response creation, editing, deletion, moderation, authentication, notifications, or evidence upload because those behaviors are outside RESP-003 and owned by other contracts.

## Explicit non-goals

- RESP-001 institution or report-link changes
- RESP-002 response storage or response mutation changes
- response editing or deletion
- response status or visibility workflows
- authentication or authorization
- actor attribution
- moderation
- notifications
- case management
- institution administration CRUD
- institution contacts or directories
- response evidence or evidence attachments
- evidence upload or retrieval changes
- automatic report status transitions
- automatic referral
- reporting-channel resolution
- official verification or adjudication of an issue or response
- frontend
- AI
- external government integrations
- a new official `Claim` relationship
- a second institutional relationship model

## Definition of done

- The comparison endpoint returns the original citizen issue and existing institution responses as separate public-safe objects.
- Existing RESP-001 and RESP-002 ownership, append-only, privacy, and status rules remain unchanged.
- Empty and unknown report behavior is stable and deterministic ordering is tested.
- Original report, response, status history, and evidence records remain unchanged by comparison.
- No new persistence model or migration is introduced.
- No RESP-003-excluded workflow is introduced.
