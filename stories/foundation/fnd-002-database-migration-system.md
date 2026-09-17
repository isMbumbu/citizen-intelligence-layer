# FND-002: Database migration system

## Goal

Establish a reliable migration path for the backend so schema changes are
versioned, repeatable, and safe to use during local and CI development.

## User

Developer / operator

## Context

The project already includes Alembic configuration and migration files, but the
product requires a disciplined workflow for schema creation and verification.
This story is about making the migration system dependable instead of ad hoc.

## Requirements

- Alembic is configured and consistent with the SQLModel persistence model.
- Initial migration can be applied to a fresh local database.
- Migration execution is repeatable without corrupting schema state.
- The database schema remains aligned with the application model.
- Schema changes are versioned and reviewable.

## Acceptance criteria

### AC1: New database initializes cleanly
Given a fresh local database instance
When the migration command is run
Then the schemas required by the application are created successfully.

### AC2: Re-runs remain safe
Given the database is already initialized
When the migration command is executed again
Then it reports a clean state and does not create duplicate schema changes.

### AC3: Versioned schema changes are reviewable
Given a schema update is made
When the migration is generated and committed
Then the migration file clearly reflects the intended change and is safe to review.

## Data requirements

- Persistence metadata for application state and future domain models
- Database connection configuration through environment settings

## API requirements

- No public API changes are required in this story.

## UI requirements

- None.

## Provenance requirements

- Database metadata should not store personal or sensitive information by default.

## Validation

- Alembic upgrade succeeds on a fresh database.
- Alembic downgrade/upgrade cycle remains valid for the initial schema path.
- Application boots against the migrated schema.

## Tests

- migration applies cleanly
- repeated migration execution is idempotent
- app can connect to migrated database

## Non-goals

- Not business domain feature implementation
- Not ingestion or public data import logic
- Not complex migration rollback automation beyond the baseline flow

## Dependencies

- FND-001

## Definition of done

- Migration path is reliable and repeatable.
- Local development can initialize the backend database from scratch.
- Schema state is consistent with the app’s Python models.
