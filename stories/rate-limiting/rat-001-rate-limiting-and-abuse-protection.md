# RAT-001: Rate limiting and abuse protection

## Goal

Protect the platform from abuse across comments, reports, file uploads, and other
expensive operations by enforcing configurable rate limits and abuse controls.

## User

Citizen / reviewer / administrator / operator

## Context

The project will soon allow user-generated content and file uploads. These
operations must be protected against spam, brute force, excessive costs, and
resource exhaustion using the existing Redis infrastructure where possible.

## Requirements

- Apply rate limits to comments, reports, and uploads.
- Consider anonymous and authenticated users separately where relevant.
- Use Redis-backed counters or equivalent rate-limiting primitives.
- Make limits configurable rather than hard-coded across the application.
- Protect expensive operations such as AI requests and search endpoints.
- Add tests for rate-limit behavior and retry-after responses.

## Acceptance criteria

### AC1: High-volume abuse is throttled
Given a user exceeds the configured limit for comment, report, or upload creation
When the API request is made again
Then the request is rejected with a rate-limit response.

### AC2: Different actor classes can be treated differently
Given the system distinguishes anonymous and authenticated users
When thresholds are configured
Then the appropriate limits are applied for each class.

### AC3: Configurable limits are read from settings
Given rate-limit configuration values are changed in settings
When the application starts or reloads config
Then those values are used by request guard logic.

## Data requirements

- rate-limit configuration values
- actor identity and request metadata
- request counters or TTL data in Redis
- optional abuse risk metadata

## API requirements

- rate-limit enforcement on comment creation
- rate-limit enforcement on report submission
- rate-limit enforcement on upload endpoints
- evaluation for AI or expensive search endpoints in future stories

## UI requirements

- user-friendly throttle or retry messaging
- moderation or support guidance when limits are reached

## Security requirements

- no open-ended abuse of expensive operations
- limit by IP, actor, or request context as applicable
- protect authentication-related flows from brute-force abuse

## Provenance requirements

- rate-limit events may be recorded in audit or operational logs
- rate-limit metadata is operational data, not evidence

## Tests

- rate limit triggers on repeated comment submissions
- upload endpoint enforces limit
- rate-limit response includes retry guidance
- authenticated and anonymous thresholds differ where configured

## Dependencies

- FND-001
- CIV-001
- EVD-001
- SEC-001

## Non-goals

- not a full bot management platform
- not a reputation-based anti-abuse engine
- not international fraud detection beyond rate limiting

## Definition of done

- abuse protection is in place for user-generated content and uploads
- limits are configurable and use the existing Redis infrastructure
- rate-limit behavior is verified with tests
