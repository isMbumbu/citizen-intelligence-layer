# MOD-002: Moderation auditability and hidden-content retention

## Goal

Preserve a clear audit trail for comment and evidence moderation decisions so
hidden or removed content can be reviewed without exposing unnecessary private
information.

## User

Moderator / reviewer / administrator

## Context

Moderation must protect the platform while preserving accountability. When a
comment or evidence item is hidden or removed, the system should keep enough
history to explain what happened without revealing sensitive personal data or the
full content to the public.

## Requirements

- Record moderator actions with actor, timestamp, reason, and target.
- Keep the original item and moderation outcome separate.
- Preserve removal or hidden-state history for review and accountability.
- Do not expose moderator or personal information unnecessarily.
- Allow review of moderation events without re-enabling hidden content.

## Acceptance criteria

### AC1: Moderation history is persisted
Given a comment or evidence item is moderated
When the moderation event is recorded
Then the actor, reason, and timestamp are stored in the audit trail.

### AC2: Hidden content is retained for accountability
Given content is hidden or removed
When the moderation record is reviewed
Then the system can explain the action without exposing the full item to unrelated users.

### AC3: Hidden content is not reenabled by default
Given a content item is removed or hidden
When the moderation record is consulted
Then the system keeps the item in a controlled state unless an authorized review action reopens it.

## Data requirements

- moderation action record
- content target id
- actor identity
- action type
- reason category
- created_at
- outcome

## API requirements

- `GET /comments/{comment_id}/moderation-history`
- `GET /evidence/{evidence_id}/moderation-history`
- `POST /comments/{comment_id}/moderation` and `POST /evidence/{evidence_id}/moderation`

## UI requirements

- moderator queue and audit log access
- minimal public transparency when content is hidden

## Security requirements

- moderators require explicit review permissions
- audit logs must not contain sensitive personal data or raw uploaded files

## Provenance requirements

- moderation records are operational metadata
- hidden or removed content remains associated with its original creation context
- moderation state is separate from verification claims

## Tests

- moderation action persists actor and reason
- hidden or removed content retains auditability
- unauthorized user cannot access moderation history

## Dependencies

- MOD-001
- CIV-001
- EVD-001

## Non-goals

- not a full enforcement engine
- not a public debate moderation scoreboard

## Definition of done

- moderation actions are auditable and preserve accountability
- hidden or removed content remains traceable without exposing private data
- the platform can support a safe moderation workflow without conflating content with truth claims
