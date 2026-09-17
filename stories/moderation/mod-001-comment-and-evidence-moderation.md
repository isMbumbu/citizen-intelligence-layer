# MOD-001: Comment and evidence moderation

## Goal

Define a moderation lifecycle for citizen comments and uploaded evidence so the
platform can safely handle abuse, spam, sensitive content, and policy violations
without conflating unverified content with false content.

## User

Moderator / reviewer / administrator

## Context

Citizen comments and evidence are user-submitted content. They require moderation
so the platform can protect users and maintain trust while preserving the
principle that unverified does not mean false.

## Requirements

- Define moderation states for comments and evidence.
- Support moderation actions for spam, harassment, inappropriate content,
  malicious file content, personal information, and abuse.
- Keep an audit trail of moderation actions.
- Preserve the content record while applying policy state changes where needed.
- Allow hidden or removed content to remain traceable for accountability.

## Acceptance criteria

### AC1: Moderation state is persisted
Given a comment or evidence record is submitted
When a moderator reviews it
Then the moderation state is stored and returned through the API.

### AC2: Abuse categories are supported
Given content violates a moderation rule
When the moderator applies a policy action
Then the content is labelled with the correct moderation outcome.

### AC3: Unverified content is not treated as false content
Given a comment or evidence item is flagged for review or hidden
When the public API is queried
Then it is still represented as citizen-submitted or moderated content, not as an official fact.

## Data requirements

- moderation state enum
- moderation reason or policy category
- actor and timestamp
- content target id
- audit record link

## API requirements

- `POST /comments/{comment_id}/moderation`
- `POST /evidence/{evidence_id}/moderation`
- `GET /comments/{comment_id}/moderation` and similar moderation history records

## UI requirements

- moderator queue for flagged content
- visible moderation labels in public-facing content
- hidden or removed content handling without exposing private moderation details

## Security requirements

- moderation actions require explicit permission
- audit actions do not expose private actor details to the public
- malicious file or abusive content is removed or hidden without deleting the
  audit trail

## Provenance requirements

- moderation actions preserve the original content and decision context
- unverified content remains clearly labelled as such
- moderation is separate from verification authority

## Tests

- comment flagged for harassment moves to flagged state
- malicious evidence is hidden or removed with audit trail
- unverified content remains labelled as citizen-submitted
- moderator action history is persisted

## Dependencies

- CIV-001
- EVD-001
- SEC-001

## Non-goals

- not truth-determination for each comment
- not automatic deletion of all user input
- not a broad social moderation platform

## Definition of done

- moderation lifecycle is defined and persisted
- content safety and abuse handling are supported
- the platform preserves unverified content distinctions and auditability
