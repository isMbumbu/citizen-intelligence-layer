# Domain model specification

The first delivery creates only platform infrastructure and a non-business
`ServiceState` SQLModel table to validate the migration path. Future domain
models use UUID identifiers, timezone-aware timestamps, explicit relationships,
and provenance references where they represent material facts.
