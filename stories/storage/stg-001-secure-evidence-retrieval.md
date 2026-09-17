# STG-001: Secure evidence retrieval

## Goal

Define a safe retrieval flow for uploaded PDFs and images so citizens and staff can
view evidence without exposing private or pending files, enabling traversal,
unauthorized access, or direct-object attacks.

## User

Citizen / reviewer / moderator / administrator

## Context

Once evidence can be uploaded, the platform must support retrieval in a way that
is secure, controlled, and consistent with the visibility model. Retrieval must
prevent unauthorized access and must not expose private or moderated uploads.

## Requirements

- Retrieve files by generated storage keys, not user-supplied names.
- Verify authorization before granting access.
- Prevent path traversal and direct-object manipulation.
- Support protected and public visibility modes as appropriate.
- Preserve correct content type and content-disposition headers.
- Do not allow uploaded files to be executed or interpreted as application code.
- Prefer short-lived signed URLs when public access is required.

## Acceptance criteria

### AC1: Only authorized users can retrieve protected files
Given an evidence record is private or pending moderation
When a user without the required permission tries to fetch it
Then the request is denied with a stable access error.

### AC2: Retrieval uses safe storage keys
Given a file is requested through the evidence API
When the backend resolves the file
Then the object is loaded from the backend-managed storage key and not from a user-controlled path.

### AC3: Response headers are correct and safe
Given a valid file is retrieved
When the response is generated
Then the content type is set according to the stored file and the file is sent as a download or inline representation appropriate for its class.

## Data requirements

- evidence record with storage key
- visibility and moderation state
- ownership and authorization metadata
- optional signed URL workflow metadata

## API requirements

- `GET /evidence/{evidence_id}` or equivalent secure retrieval endpoint
- `GET /evidence/{evidence_id}/download` if separate file streams are required

## UI requirements

- evidence viewer for PDF and image records
- inaccessible or pending content states for restricted content

## Security requirements

- no path traversal
- no direct object access to untrusted file paths
- no execution permissions on uploaded files
- no storage path leakage to users
- private resources require access validation before retrieval

## Provenance requirements

- retrieval is not treated as verification
- the original evidence record remains the authoritative artifact
- moderator or visibility state must remain auditable

## Tests

- authorized retrieval succeeds
- unauthorized retrieval fails
- path traversal attempt is rejected
- pending/private file is not publicly exposed
- content type and disposition are correct for pdf and image responses

## Dependencies

- EVD-001
- EVD-002
- SEC-001
- MOD-001

## Non-goals

- not a general-purpose file-hosting system
- not broad document indexing or OCR workflow
- not full public asset CDN integration

## Definition of done

- evidence retrieval is secure and authorization-aware
- uploaded files are never executable or interpreted as application code
- public and private retrieval flows are separated and testable
