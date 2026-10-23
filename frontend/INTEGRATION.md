# Frontend API Integration Guide

## 1. Overview

This document describes the current mounted and implemented backend API behavior only.

- Current backend commit: `84c33ad`
- This document reflects the actual backend routes, schemas, services, dependencies, and tests currently in the repository.
- Frontend developers must not assume undocumented routes or service-layer functionality exists as public API.
- If a capability is not listed here as a mounted route, it should be treated as unavailable to the frontend unless the implementation is separately verified.

## 2. Base API

Base prefix:

- `/api/v1`

Current mounted routers include:

- projects
- project taxonomy
- civic action / reports
- comments
- evidence
- moderation

The backend app exposes:

- `GET /api/v1/health`
- `GET /api/v1/health/ready`

Important backend behavior:

- APIs are mounted under the FastAPI application at `/api/v1`.
- Security headers are added by middleware and include `x-content-type-options`, `x-frame-options`, `referrer-policy`, and `cache-control` defaults.
- The backend does not implement real user identity or auth. The security layer is a placeholder trusted-actor system only.

## 3. Authentication

Current reality:

- There is no login endpoint.
- There is no registration endpoint.
- There is no JWT implementation.
- There is no session authentication.
- There is no API-key authentication.
- There is no token issuance or refresh flow.
- Protected routes currently depend on the backend trusted-actor placeholder defined in the security layer.
- This is not a frontend authentication system.

Exact semantics currently enforced by the backend:

- If no trusted actor is provided on a protected route:
  - `401 Unauthorized`
  - `detail: "Authentication is required."`
- If a trusted actor is provided but lacks the required permission:
  - `403 Forbidden`
  - moderation permission: `"Moderation permission is required."`
  - protected evidence permission: `"Protected evidence permission is required."`

Notes:

- Public endpoints are intentionally anonymous.
- Protected endpoints are guarded by placeholder permission checks, not an actual identity layer.
- Frontend developers must not invent or assume a login flow that is not mounted by the backend.

## 4. Health

### GET `/api/v1/health`

Purpose:

- Liveness endpoint.

Auth:

- public/anonymous

Response:

- `200 OK`
- Body: `{ "status": "ok" }`

Errors:

- none

### GET `/api/v1/health/ready`

Purpose:

- readiness check for PostgreSQL and Redis connectivity.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ReadinessReport`
  - `status`: `"ready"` or `"not_ready"`
  - readiness details are returned in the payload

Errors:

- `503 Service Unavailable` if the backend is not ready
- `detail` contains the report payload

## 5. Projects

### GET `/api/v1/projects`

Purpose:

- Browse/filter the public project list.

Auth:

- public/anonymous

Query parameters:

- `page` (int >= 1, default 1)
- `page_size` (int 1..100, default 20)
- `county` (string, optional)
- `ward` (string, optional)
- `project_type` (string, optional)
- `category_id` (UUID, optional)
- `subtype_id` (UUID, optional)
- `status` (`PLANNED`, `IN_PROGRESS`, `COMPLETED`, `ON_HOLD`)
- `search` (string, optional)

Response:

- `200 OK`
- `ProjectPageResponse`
  - `items[]`
    - `id`
    - `name`
    - `description`
    - `project_type`
    - `category`: `{ id, code, name }`
    - `subtype`: `{ id, code, name } | null`
    - `status`
    - `location`: `{ county_id, county, sub_county_id, sub_county, ward_id, ward }`
  - `page`
  - `page_size`
  - `total`

Errors:

- `404` if category filter is invalid: `"Project category not found."`
- `404` if subtype filter is invalid: `"Project subtype not found."`
- `422` if subtype/category mismatch: `"Project subtype does not belong to project category."`

Notes:

- Pagination is server-side.
- Project taxonomy filters are mounted and implemented.

### GET `/api/v1/projects/{project_id}`

Purpose:

- Fetch the project detail page contract.

Auth:

- public/anonymous

Path parameters:

- `project_id` (UUID)

Response:

- `200 OK`
- `ProjectDetailResponse`
  - `id`, `name`, `description`
  - `project_type`
  - `category`, `subtype`
  - `status`
  - `location`
  - `financial_summary`
    - `allocated`, `committed`, `contracted`, `spent`, `reported`
    - each item has `kind`, `amount`, `currency`, `financial_period`, `evidence`
  - `contractor` or `null`
  - `progress` or `null`
  - `timeline`
  - `last_verified_at`
  - `verification` or `null`
  - `anomalies[]`
  - `evidence[]`

Errors:

- `404`: `"Project not found."`

### GET `/api/v1/projects/{project_id}/sources`

Purpose:

- Return project claims with their source chains.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ClaimEvidenceResponse[]`
  - `id`
  - `claim_kind`
  - `field_name`
  - `value_text`
  - `numeric_value`
  - `currency`
  - `financial_period`
  - `sources[]`
    - `source_id`
    - `source_record_id`
    - `publisher`
    - `title`
    - `source_type`
    - `url`
    - `publication_date`
    - `retrieved_at`
    - `record_summary`

Errors:

- `404`: `"Project not found."`

### GET `/api/v1/projects/{project_id}/verification`

Purpose:

- Return the explicit project verification record.

Auth:

- public/anonymous

Response:

- `200 OK`
- `VerificationResponse | null`
  - `status`: `UNVERIFIED`, `PARTIALLY_VERIFIED`, `VERIFIED`, `STALE`, `DISPUTED`
  - `verification_date`
  - `recorded_at`
  - `notes`
  - `source` or `null`

Errors:

- `404`: `"Project not found."`

### GET `/api/v1/projects/{project_id}/anomalies`

Purpose:

- Return deterministic project review signals.

Auth:

- public/anonymous

Response:

- `200 OK`
- `AnomalyResponse[]`

Implemented anomaly types:

- `PROGRESS_SPEND_GAP`
  - `status`: `REVIEW_REQUIRED`
  - fields include reported progress percentage, spent budget percentage, and supporting claims
- `SPEND_OVER_ALLOCATION`
  - `status`: `REVIEW_REQUIRED`
- `SPEND_OVER_CONTRACT`
  - `status`: `REVIEW_REQUIRED`
- `TIMELINE_PAST_DUE`
  - `status`: `REVIEW_REQUIRED`
- `DATA_GAP_CLAIM_PROVENANCE`
  - `status`: `REVIEW_REQUIRED`
- `DATA_GAP_VERIFICATION`
  - `status`: `REVIEW_REQUIRED`

Important note:

- These are deterministic review signals, not AI-generated conclusions, accusations, or verification results.

## 6. Taxonomy

### GET `/api/v1/project-categories`

Purpose:

- Return active taxonomy categories with their active subtype hierarchy.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ProjectCategoryResponse[]`
  - `id`, `code`, `name`, `description`
  - `subtypes[]`
    - `id`, `code`, `name`, `description`

### GET `/api/v1/project-categories/{category_id}/subtypes`

Purpose:

- Return active subtypes for one category.

Auth:

- public/anonymous

Path parameters:

- `category_id` (UUID)

Response:

- `200 OK`
- `ProjectSubtypeResponse[]`

Errors:

- `404` if the category is not found or inactive (service contract)

Important note:

- Taxonomy is database-backed reference data and should not be treated as a hard-coded frontend source of truth.

## 7. Civic Reports

### POST `/api/v1/projects/{project_id}/reports`

Purpose:

- Submit a citizen issue report against a project.

Auth:

- public/anonymous

Path parameters:

- `project_id` (UUID)

JSON body:

- `category`: `QUALITY`, `DELAY`, `ACCESS`, `SAFETY`, `OTHER`
- `description` (10..4000 chars)
- `contact_information` (optional string, max 255)

Response:

- `201 Created`
- `CitizenReportResponse`
  - `id`
  - `project_id`
  - `category`
  - `status`
  - `submitted_at`

Errors:

- `404`: `"Project not found."`
- `422`: `"The issue report is invalid."`
- `500`: `"Unable to submit issue report."`

### GET `/api/v1/reports/{report_id}`

Purpose:

- Fetch report detail and status history.

Auth:

- public/anonymous

Response:

- `200 OK`
- `CitizenReportDetailResponse`
  - `id`, `project_id`, `category`, `status`, `submitted_at`
  - `status_history[]`: `{ from_status, to_status, created_at }`

Errors:

- `404`: `"Report not found."`

### GET `/api/v1/reports/{report_id}/channels`

Purpose:

- Resolve reporting channels for a report.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ReportingChannelResponse[]`
  - `id`
  - `office_name`
  - `channel_type`
  - `destination`
  - `display_label`
  - `priority`

Errors:

- `404`: `"Report not found."`
- `404`: `"Project not found."`
- `404`: `"Project location not found."`

### GET `/api/v1/reports/{report_id}/institutions`

Purpose:

- Return institution relationships for a report.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ReportInstitutionResponse[]`
  - `institution_id`
  - `institution_name`
  - `institution_role`
  - `relationship_type`

### GET `/api/v1/reports/{report_id}/responses`

Purpose:

- Return institution responses for a report.

Auth:

- public/anonymous

Response:

- `200 OK`
- `InstitutionResponseResponse[]`
  - `response_id`
  - `institution_id`
  - `institution_name`
  - `institution_role`
  - `relationship_type`
  - `content`
  - `created_at`

### GET `/api/v1/reports/{report_id}/comparison`

Purpose:

- Compare the original issue to institution responses.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ReportComparisonResponse`
  - `issue`: `{ report_id, category, description, submitted_at }`
  - `responses[]`: `InstitutionResponseResponse[]`

Report status values:

- `SUBMITTED`
- `UNDER_REVIEW`
- `REFERRED`
- `RESPONDED`
- `RESOLVED`
- `CLOSED`

Important note:

- Report status-transition logic exists in the backend service layer, but there is currently no public report-status mutation endpoint mounted.

## 8. Comments

### POST `/api/v1/projects/{project_id}/comments`

Purpose:

- Create a citizen comment on a project.

Auth:

- public/anonymous

Path parameters:

- `project_id` (UUID)

JSON body:

- `author_id` (UUID)
- `content` (10..4000 chars, trimmed)
- `parent_comment_id` (UUID, optional)

Response:

- `201 Created`
- `CitizenCommentResponse`
  - `id`, `project_id`, `parent_comment_id`
  - `author_id`, `content`
  - `status` (`ACTIVE`)
  - `moderation_state` (`PENDING`, `FLAGGED`, `HIDDEN`, `REMOVED`)
  - `visibility` (`PUBLIC`)
  - `is_citizen_submitted` = `true`
  - `trust_label` = `"CITIZEN_SUBMITTED_INFORMATION"`
  - `created_at`, `updated_at`

Errors:

- `404`: `"Project not found."`
- `404`: `"Parent comment not found for project."`
- `429`: rate limit exceeded

Rate limit:

- comments: `10 / 600 seconds`

### GET `/api/v1/projects/{project_id}/comments`

Purpose:

- List publicly visible comments for a project.

Auth:

- public/anonymous

Response:

- `200 OK`
- `CitizenCommentResponse[]`

Visibility behavior:

- `HIDDEN` and `REMOVED` comments are excluded from list results.

### POST `/api/v1/comments/{comment_id}/reports`

Purpose:

- Report a comment for abuse or policy review.

Auth:

- public/anonymous

Path parameters:

- `comment_id` (UUID)

JSON body:

- `reporter_id` (UUID)
- `reason`: `SPAM`, `HARASSMENT`, `PERSONAL_INFORMATION`, `INAPPROPRIATE`, `OTHER`

Response:

- `201 Created`
- `CommentReportResponse`
  - `id`, `comment_id`, `reporter_id`, `reason`, `status`, `submitted_at`

Errors:

- `404`: `"Comment not found."`
- `429`: rate limit exceeded

Rate limit:

- reports: `10 / 600 seconds`

## 9. Evidence

### POST `/api/v1/comments/{comment_id}/evidence`

Purpose:

- Upload evidence attached to a comment.

Auth:

- public/anonymous

Request:

- multipart/form-data
  - `uploader_id` (UUID)
  - `file` (binary upload)

Response:

- `201 Created`
- `EvidenceResponse`
  - `id`, `project_id`, `comment_id`, `report_id`, `uploader_id`
  - `source_class`
  - `original_filename`, `mime_type`, `file_size_bytes`, `checksum_sha256`
  - `moderation_state`, `processing_state`, `visibility`, `is_deleted`
  - `uploaded_at`
  - `is_official_source` (always `false`)
  - `trust_label` (`"CITIZEN_SUBMITTED_EVIDENCE"`)

### POST `/api/v1/reports/{report_id}/evidence`

Purpose:

- Upload evidence attached to a report.

Auth:

- public/anonymous

Request:

- multipart/form-data
  - `uploader_id` (UUID)
  - `file` (binary upload)

### POST `/api/v1/projects/{project_id}/evidence`

Purpose:

- Upload evidence attached directly to a project.

Auth:

- public/anonymous

Request:

- multipart/form-data
  - `uploader_id` (UUID)
  - `comment_id` (UUID, optional)
  - `file` (binary upload)

### POST `/api/v1/projects/{project_id}/reports/{report_id}/evidence`

Purpose:

- Upload evidence attached to a project report.

Auth:

- public/anonymous

Request:

- multipart/form-data
  - `uploader_id` (UUID)
  - `comment_id` (UUID, optional)
  - `file` (binary upload)

Supported upload MIME types:

- `application/pdf`
- `image/gif`
- `image/jpeg`
- `image/png`
- `image/webp`

Upload validation rules:

- file extension must match allowed types
- file content must be validated using its real bytes/signature
- unsupported or malformed files are rejected
- PDF content with embedded active content markers is rejected
- oversize files are rejected
- MIME type must match the detected content
- filename is sanitized before storage; it is not used as a storage path

### GET `/api/v1/evidence/{evidence_id}`

Purpose:

- Return evidence metadata without returning the file bytes.

Auth:

- public/anonymous only for evidence that is public, not hidden/removed, and not deleted
- otherwise the backend applies placeholder trusted-actor permission enforcement

Response:

- `200 OK`
- `EvidenceResponse`

Errors:

- `404`: `"Evidence not found."`
- `401`: `"Authentication is required."`
- `403`: `"Protected evidence permission is required."`

### GET `/api/v1/evidence/{evidence_id}/download`

Purpose:

- Download the original evidence file.

Auth:

- public/anonymous only for public, non-hidden, non-removed, non-deleted evidence
- otherwise the backend applies placeholder trusted-actor permission enforcement

Response:

- `200 OK`
- raw binary content
- `Content-Type` set to the actual evidence MIME type
- `Content-Disposition` set to `attachment; filename="..."`

Errors:

- `404`: `"Evidence not found."`
- `404`: `"Evidence file not found."`
- `401`: `"Authentication is required."`
- `403`: `"Protected evidence permission is required."`
- `500`: `"Unable to retrieve evidence file."`

Important evidence rules:

- `storage_key` is an internal backend value and is never exposed in the frontend contract.
- Frontend must never send, construct, display, or depend on `storage_key`.
- There is currently no signed-URL contract.
- Hidden or removed evidence returns `404 "Evidence not found."`
- Deleted evidence is not publicly retrievable and is protected by the placeholder trust boundary.

### GET `/api/v1/evidence/{evidence_id}/processing`

Purpose:

- Return evidence processing state, event history, and derived artifact lineage.

Auth:

- public/anonymous

Response:

- `200 OK`
- `EvidenceProcessingResponse`
  - `evidence_id`
  - `processing_state`
  - `events[]`
    - `from_state`, `to_state`, `event_type`, `error_code`, `error_message`, `created_at`
  - `derived_artifacts[]`
    - `id`, `evidence_id`, `artifact_type`, `content_hash`, `source_class`, `trust_classification`, `created_at`

## 10. Verification

### GET `/api/v1/projects/{project_id}/verification`

Purpose:

- Return the current explicit verification state for a project.

Auth:

- public/anonymous

Response:

- `200 OK`
- `VerificationResponse | null`
  - `status`
  - `verification_date`
  - `recorded_at`
  - `notes`
  - `source`

Verification states:

- `UNVERIFIED`
- `PARTIALLY_VERIFIED`
- `VERIFIED`
- `STALE`
- `DISPUTED`

Important note:

- Verification information is also included in the project detail response.
- Service-layer review request functionality exists in the backend, but there is no public route exposing review-request creation.

## 11. Intelligence / Anomalies

### GET `/api/v1/projects/{project_id}/anomalies`

Purpose:

- Return deterministic project review signals.

Auth:

- public/anonymous

Response:

- `200 OK`
- `AnomalyResponse[]`

Currently implemented anomaly types:

- `PROGRESS_SPEND_GAP`
- `SPEND_OVER_ALLOCATION`
- `SPEND_OVER_CONTRACT`
- `TIMELINE_PAST_DUE`
- `DATA_GAP_CLAIM_PROVENANCE`
- `DATA_GAP_VERIFICATION`

Fields:

- `type`
- `status`
- `message`
- `requires_verification`
- type-specific metrics
- `supporting_claims[]`

Important note:

- These are deterministic review signals.
- They are not AI-generated conclusions.
- They are not accusations.
- They are not verified findings.

## 12. Institutions and Responses

### GET `/api/v1/reports/{report_id}/institutions`

Purpose:

- Return institutions linked to the report.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ReportInstitutionResponse[]`

### GET `/api/v1/reports/{report_id}/responses`

Purpose:

- Return institution responses for the report.

Auth:

- public/anonymous

Response:

- `200 OK`
- `InstitutionResponseResponse[]`

### GET `/api/v1/reports/{report_id}/comparison`

Purpose:

- Return original report issue with institution response comparison payload.

Auth:

- public/anonymous

Response:

- `200 OK`
- `ReportComparisonResponse`

Important note:

- Institution-response creation/mutation is not currently exposed publicly.

## 13. Moderation

### POST `/api/v1/comments/{comment_id}/moderation`

Purpose:

- Apply a moderation action to a comment.

Auth:

- protected, placeholder trusted-actor requirement

Request body:

- `action`: `FLAG`, `HIDE`, `REMOVE`, `RESTORE`
- `reason`: `SPAM`, `HARASSMENT`, `PERSONAL_INFORMATION`, `MALICIOUS_CONTENT`, `INAPPROPRIATE_CONTENT`, `ABUSE`
- `notes` (optional)

Response:

- `201 Created`
- `ModerationHistoryResponse`

Errors:

- `404`: `"Comment not found."`
- `401`: `"Authentication is required."`
- `403`: `"Moderation permission is required."`
- `409` for invalid transition, message includes the invalid transition state/action

### POST `/api/v1/evidence/{evidence_id}/moderation`

Purpose:

- Apply a moderation action to evidence.

Auth:

- protected, placeholder trusted-actor requirement

Response:

- `201 Created`
- `ModerationHistoryResponse`

Errors:

- `404`: `"Evidence not found."`
- `401`: `"Authentication is required."`
- `403`: `"Moderation permission is required."`
- `409` for invalid transition

### GET `/api/v1/comments/{comment_id}/moderation-history`

Purpose:

- Return moderation history for a comment.

Auth:

- protected, placeholder trusted-actor requirement

### GET `/api/v1/evidence/{evidence_id}/moderation-history`

Purpose:

- Return moderation history for evidence.

Auth:

- protected, placeholder trusted-actor requirement

Important note:

- This is a trusted-actor placeholder system, not a real user auth implementation.

## 14. Rate Limiting

Exact implemented rate-limit configuration:

- comment creation: `10 / 600 seconds`
- comment reporting: `10 / 600 seconds`
- evidence upload: `5 / 600 seconds`

Rate-limited endpoints:

- `POST /api/v1/projects/{project_id}/comments`
- `POST /api/v1/comments/{comment_id}/reports`
- upload endpoints under evidence

Behavior on limit exceed:

- `429 Too Many Requests`
- `detail`: `"Rate limit exceeded."`
- response headers:
  - `Retry-After`
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

Redis dependency failure behavior:

- `503 Service Unavailable`
- `detail`: `"Rate limiting is temporarily unavailable."`

Frontend behavior:

- honor `Retry-After` for backoff. 
- handle 429 as an explicit rate-limit condition rather than a validation error.

## 15. Common Errors

| Status | Meaning | Exact confirmed detail where stable |
| --- | --- | --- |
| 401 | authentication required for protected access | `"Authentication is required."` |
| 403 | permission denied for protected action | `"Moderation permission is required."` or `"Protected evidence permission is required."` |
| 404 | resource not found | `"Project not found."`, `"Report not found."`, `"Comment not found."`, `"Evidence not found."`, `"Evidence file not found."` |
| 409 | invalid or duplicate moderation or link state | `"Report is already linked to this institution."` or moderation invalid transition text |
| 422 | invalid payload or validation failure | `"The issue report is invalid."`, `"The claim review request is invalid."`, upload validation messages |
| 429 | rate limit exceeded | `"Rate limit exceeded."` |
| 500 | internal backend failure for a mounted route | route-specific detail text |
| 503 | rate-limit dependency unavailable | `"Rate limiting is temporarily unavailable."` |

## 16. Frontend Capabilities Available Now

The frontend can currently rely on:

- project browsing and detail views
- taxonomy filters and category/subtype lookups
- civic report creation and read-only report lifecycle/detail/comparison views
- comment creation, listing, and reporting
- evidence upload and metadata/download behavior for the current public/protected rules
- verification reads
- deterministic project anomaly display
- institution and response reads

## 17. Not Currently Available

The following are not currently available as mounted public backend functionality:

- real authentication
- registration/login
- JWT/session/API-key flow
- token issuance or refresh
- public report status mutation
- public claim-review mutation
- institution-response creation/mutation
- AI endpoints or AI-generated explanations
- ingestion pipeline and document extraction routes
- signed-URL architecture
- any frontend-facing storage-key contract

## 18. Frontend Integration Rules

1. Treat the mounted API responses and schemas as the source of truth.
2. Treat taxonomy as API-backed reference data, not a hard-coded frontend source of truth.
3. Never expose or depend on `storage_key`.
4. Do not assume service-layer functionality has a public route.
5. Handle `401` and `403` separately.
6. Honor rate-limit headers and backoff on `429`.
7. Treat anomaly results as review signals, not verified findings.
8. Do not invent authentication, AI, ingestion, or signed-URL flows.
9. Do not assume protected evidence is anonymously accessible.
10. Do not treat citizen-submitted information as automatically verified.

> Source of truth: current mounted backend routes, schemas, services, and tests. If this document conflicts with the implementation, verify the implementation before changing frontend behavior.
