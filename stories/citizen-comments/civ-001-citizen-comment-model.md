# CIV-001: Citizen comment model

## Goal

Create the content model for citizen comments so public project discussion can be
stored, moderated, and clearly labelled as non-official information.

## User

Citizen / reviewer / moderator

## Context

The platform now needs a user-generated discussion layer attached to projects.
This content must be stored separately from official facts and must remain
constrained by moderation and safety controls.

## Requirements

- A project can have project comments.
- A comment can belong to a parent comment for threading or replies.
- A comment stores author identity, status, and moderation state.
- Comment content is clearly labelled as citizen-submitted information.
- The system supports reporting comments for abuse or policy violation.

## Acceptance criteria

### AC1: Comment records are created reliably
Given a project and authenticated user
When a citizen comment is submitted
Then a comment record is created with status and moderation metadata.

### AC2: Comments are distinct from official project facts
Given a comment exists
When it is rendered in the UI or API
Then it is labelled as citizen-submitted, not official information.

### AC3: Moderation state is tracked
Given a comment is flagged or hidden
When the moderation workflow is applied
Then the state is persisted and visible to staff.

## Data requirements

- project relationship
- author identity
- optional parent comment relationship
- timestamps
- moderation state
- visibility state

## API requirements

- `POST /projects/{project_id}/comments`
- `GET /projects/{project_id}/comments`
- `POST /comments/{comment_id}/reports`

## UI requirements

- comment composer, comment list, and trust labels
- moderator-visible metadata where relevant

## Security requirements

- users cannot edit or delete other users’ comments
- moderation actions require explicit review permissions
- content is rate-limited and abuse-detected

## Provenance requirements

- comment content is labelled as citizen-submitted and not independently verified
- the system preserves moderation history without exposing private personal data

## Tests

- create comment under valid project
- reject comment for unauthorized project
- label comment as citizen-submitted in API response
- report a comment and track report state

## Dependencies

- FND-001
- FND-002
- CIV-001 (this story)

## Non-goals

- not official verification workflow
- not broad social platform features
- not reputation system or ranking

## Definition of done

- comment model is persisted and queryable
- comment trust labels are enforced
- moderation state is available for later review workflows
