# EVD-005: Browse public evidence

## Goal

Let the public discover citizen evidence through projects and places instead
of typing evidence identifiers.

## User

Citizen / public visitor

## Requirements

- List public evidence newest first with project name, county, and category.
- Filter by project, category, county, and type (photo or document).
- Return only browse-safe fields: never uploader identifiers, filenames,
  checksums, storage keys, or moderation notes.
- Express review state neutrally: not yet reviewed or under review.

## Acceptance criteria

### AC1: Evidence can be browsed with project context
Given public evidence exists
When `GET /api/v1/evidence` is requested
Then a page of evidence cards is returned newest first with project name,
county, category, what it was shared on, type, review status, and total.

### AC2: Filters narrow the feed
Given evidence across projects, counties, categories, and types
When `project_id`, `category_id`, `county`, or `kind` is supplied
Then only matching evidence is returned; an invalid `kind` returns 422.

### AC3: Identifying data stays out
Given evidence with an uploader identifier, filename, and checksum
When it appears in the feed
Then none of those values are included.

### AC4: Only public evidence appears
Given private, hidden, removed, or deleted evidence
When the feed is requested
Then it is excluded.

## API requirements

- `GET /api/v1/evidence?page=&page_size=&project_id=&category_id=&county=&kind=`
- `page_size` is between 1 and 60.

## Dependencies

- EVD-004

## Non-goals

- no free-text search over evidence
- no public reporting of individual evidence items (needs a separate story)
