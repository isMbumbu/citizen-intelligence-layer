# EVD-001: Evidence storage model

## Goal

Define the underlying evidence model for citizen-submitted attachments so images
and PDFs can be stored, tracked, and later used in verification and intelligence
workflows without confusing them with official source documents.

## User

Citizen / reviewer / moderator / operator

## Context

The platform needs a structured evidence layer that supports attachments to
comments and citizen reports. These artifacts must be stored with provenance,
ownership, and processing metadata while staying separate from official records.

## Requirements

- Store evidence metadata separately from stored file content.
- Preserve ownership and project association.
- Support images and PDFs initially.
- Keep evidence records distinct from official source documents.
- Store checksum, visibility, lifecycle, and moderation metadata.
- Preserve enough context to later use evidence in verification and intelligence.

## Acceptance criteria

### AC1: Evidence records are created with required metadata
Given a citizen attaches an image or PDF to a comment or report
When the evidence record is created
Then the system stores ownership, project association, moderation state, and file metadata.

### AC2: Evidence is distinct from official records
Given the same project has both official source documents and citizen-submitted evidence
When the data is retrieved
Then the system distinguishes the two record classes clearly.

### AC3: Integrity metadata is persisted
Given an evidence record has been uploaded
When the file is read back
Then the checksum and file-size metadata are available for audit and validation.

## Data requirements

- `EvidenceRecord`
- optional project relation
- optional comment or report relation
- uploader identity
- checksum and storage key
- moderation state
- processing state
- visibility
- deletion state

## API requirements

- `POST /projects/{project_id}/evidence`
- `POST /projects/{project_id}/reports/{report_id}/evidence`
- `GET /evidence/{evidence_id}`

## UI requirements

- evidence upload interface
- evidence list and metadata display
- clear labels for citizen-submitted evidence vs official sources

## Security requirements

- file storage key is generated and not user-controlled
- evidence can be private or pending moderation
- uploaded files are treated as untrusted input

## Provenance requirements

- evidence records preserve upload time and uploader identity
- the platform must not present evidence as authoritative without relevant
  verification metadata

## Tests

- evidence record created successfully
- project and report associations are stored correctly
- checksum and size metadata persist correctly
- evidence retrieval returns correct metadata and visibility state

## Dependencies

- SEC-001
- CIV-001
- FND-001

## Non-goals

- not AI extraction pipeline
- not official source management
- not broad document workflow beyond upload and retrieval metadata

## Definition of done

- evidence records exist with clear metadata and ownership
- evidence is distinct from official source documents
- the model supports later verification and intelligence layers
