# EVD-004: Public citizen evidence images

## Goal

Let anyone see the photos and documents citizens attach to projects, reports,
and comments, without exposing personal metadata embedded in those files.

## User

Citizen / public visitor / moderator

## Requirements

- Strip EXIF and text metadata (GPS, device, timestamps, author) from JPEG,
  PNG, and WebP uploads before storage, applying EXIF orientation to the pixels
  first. Size and checksum describe the cleaned file.
- Store validated uploads as `PUBLIC`; moderators keep hiding and removing
  them through the existing moderation actions.
- List public evidence for a project (including its report and comment
  attachments), a report, or a comment.
- Serve image downloads inline so they display in the browser; documents still
  download as attachments.
- Show evidence galleries on project pages, report pages, and comments, and an
  image preview on the evidence record, labelled as citizen evidence, not
  verification.

## Acceptance criteria

### AC1: Uploaded images carry no personal metadata
Given a JPEG with GPS coordinates and an orientation tag
When it is uploaded
Then the stored image has no EXIF data, displays upright, and its checksum
matches the stored bytes.

### AC2: Uploads are publicly viewable
Given a valid upload
When it is stored
Then its visibility is `PUBLIC` and its metadata and file can be retrieved
without authentication.

### AC3: Moderated-away evidence stays hidden
Given evidence that is hidden, removed, deleted, or private
When public evidence is listed or retrieved
Then it is excluded or returns not found / authentication required.

### AC4: Evidence can be discovered
Given public evidence on a project, report, or comment
When `GET /api/v1/{projects|reports|comments}/{id}/evidence` is requested
Then the evidence is returned newest first, up to 100 items.

## API requirements

- `GET /api/v1/projects/{project_id}/evidence`
- `GET /api/v1/reports/{report_id}/evidence`
- `GET /api/v1/comments/{comment_id}/evidence`
- `GET /api/v1/evidence/{evidence_id}/download` returns `inline` for images.

## Security and privacy requirements

- Never publish an image that has not been re-encoded without metadata.
- Evidence uploaded before this change keeps its previous `PRIVATE`
  visibility, because it was stored with its original metadata.
- GIFs are stored unchanged (no EXIF block; re-encoding breaks animation).
- PDF document metadata is not stripped.

## Dependencies

- EVD-001
- EVD-002
- EVD-003

## Non-goals

- no face or number-plate blurring
- no signed URLs or CDN
- no pre-moderation queue
