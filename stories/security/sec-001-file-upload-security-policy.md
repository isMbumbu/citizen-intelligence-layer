# SEC-001: File upload security policy

## Goal

Define and enforce the secure handling of uploaded files so untrusted citizen
content is stored, processed, and retrieved safely.

## User

Developer / reviewer / administrator

## Context

The project is moving toward citizen comments and evidence uploads. These files
are untrusted input and must be handled according to a clear security policy.

## Requirements

- Uploaded files must undergo validation before storage.
- Only allow-listed MIME types and extension combinations are accepted.
- Filenames are sanitized and never used as storage paths.
- Files are stored with generated storage keys.
- File size limits are enforced.
- File checksums are stored for integrity verification.
- Uploaded content never executes in the application environment.
- Private or moderated files are only retrievable through controlled access.

## Acceptance criteria

### AC1: Unsafe uploads are rejected
Given a file with a disallowed MIME type or suspicious content signature
When the upload endpoint is called
Then the request is rejected with a clear validation error.

### AC2: Storage is isolated and safe
Given an accepted upload
When the file is stored
Then it is placed in a secure storage layer using a generated storage key.

### AC3: File integrity is preserved
Given a stored upload
When the file is retrieved or re-validated
Then the checksum remains available for integrity checks.

## Data requirements

- upload metadata
- user or actor identifier
- file size and checksum
- validation result
- moderation status

## API requirements

- `POST /projects/{project_id}/evidence`
- `POST /comments/{comment_id}/evidence` if implementation expands to comment-level evidence

## UI requirements

- safe upload state, validation feedback, and error messages

## Security requirements

- no executable handling
- no trust of client MIME type
- no direct user-controlled paths
- implementation must support isolated storage

## Provenance requirements

- uploaded file records must preserve upload timestamp and source identity
- file records are not treated as official source facts by default

## Tests

- valid upload accepted
- invalid extension rejected
- oversized file rejected
- checksum is persisted
- file is stored under generated storage key

## Dependencies

- FND-001
- EVD-001

## Non-goals

- not AI extraction pipeline yet
- not broad moderation workflow beyond secure storage rules

## Definition of done

- file upload policies are explicit and testable
- storage handling prevents execution and path traversal risks
- integrity metadata is preserved
