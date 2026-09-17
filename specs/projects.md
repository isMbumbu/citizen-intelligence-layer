# Projects specification

The vertical slice exposes a browseable public-project record with its
location, purpose, type, lifecycle status, timeline, contractor, reported
progress, financial summary, verification state, and evidence. Projects use
UUID primary keys and reference a ward. The public browse endpoint supports
county, ward, project type, status, and text search filters with pagination.

`GET /api/v1/projects/{project_id}` is the project-page contract. It returns
the current, scoped summary of these concepts; detailed claim provenance remains
available from the project's sources endpoint. No ingestion, project editing,
or complete public-project registry is implied by this slice.
