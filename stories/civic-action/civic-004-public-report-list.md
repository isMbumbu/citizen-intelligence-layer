# CIVIC-004: Browse citizen reports

## Goal

Let citizens find reports and check their status without needing to keep or
type a report identifier.

## User

Citizen

## Requirements

- List reports newest first with pagination.
- Filter by project, status, and category.
- Return project name, category, status, and submission time for each report.
- Remember reports submitted from the same browser so a citizen can reopen
  them from a "My reports" list.

## Acceptance criteria

### AC1: Reports can be browsed

Given submitted reports exist
When `GET /api/v1/reports` is requested
Then a page of reports is returned newest first with the total matching count.

### AC2: Filters narrow the list

Given reports across projects, statuses, and categories
When `project_id`, `status`, or `category` is supplied
Then only matching reports are returned; invalid status or category values
return 422.

### AC3: Report content stays out of the list

Given a report with a description and contact information
When it appears in the list
Then neither the description nor the contact information is included.

### AC4: Citizens find their own reports

Given a citizen submitted a report from this browser
When they open the reports page
Then the report appears under "My reports" with a link to its status page.

### AC5: Project pages show their reports

Given a project has reports
When its page loads
Then recent reports for that project are listed with links to their status.

## API requirements

- `GET /api/v1/reports?page=&page_size=&project_id=&status=&category=`
- `page_size` is between 1 and 100; unknown projects return an empty page.

## Security and privacy requirements

- Never list descriptions or contact information.
- "My reports" is stored only in the citizen's browser; nothing about the
  citizen is sent to the backend.
- Do not introduce authentication or authorization.

## Dependencies

- CIVIC-001
- CIVIC-002

## Non-goals

- no search over report descriptions
- no report moderation or hiding
- no notifications or accounts

## Definition of done

- The list endpoint follows route → service → repository.
- Focused tests cover the list contract, privacy, filters, and query shape.
- The frontend reports page, "My reports", and project report list are in place.
