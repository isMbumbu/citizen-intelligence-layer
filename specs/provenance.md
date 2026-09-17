# Provenance specification

Important project claims identify supporting source records through
`ClaimSource`. Financial values, contractor information, and reported progress
all carry a claim reference. `GET /api/v1/projects/{project_id}/sources`
returns the project claims and their sources so clients can answer where each
material fact came from.

Derived anomaly flags, verification records, and citizen reports are separate
record types. A derived flag links back to claims but is not a source or a
verification result.
