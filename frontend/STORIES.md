# CIVICACT Frontend Stories Specification

## Purpose

This document captures the implementation-ready frontend user stories for CIVICACT based on the current backend API contract documented in the frontend integration guide. It is intentionally scoped to real backend capabilities and required frontend-only UX behavior. It does not invent unsupported auth, AI, data, or mutation features.

## Source of truth

- Frontend API Integration Guide: `frontend/INTEGRATION.md`
- Backend contract: mounted FastAPI endpoints and current service behavior
- Product principles: `frontend/PRINCIPLES.md`

## Story format

Each story includes:
- Story ID
- Epic
- User Story
- Backend/API Dependency
- Acceptance Criteria
- UI Requirements
- Error States
- Data Mapping
- Definition of Done

---

# EPIC 1 — Application Shell & Design System

## Story ID
CIVICACT-FE-001

### Epic
Application shell and global navigation

### User Story
As a citizen, I want a consistent public-facing app shell, so that I can navigate the platform without confusion across desktop and mobile.

### Backend/API Dependency
Frontend only

### Acceptance Criteria
- Given the user opens the app, When the shell loads, Then the top navigation and content areas render correctly.
- Given the user navigates between sections, When page state changes, Then the active nav state updates.
- Given the app is loading data, When a route resolves, Then the shell remains stable.
- Given a page fails to load, When an error occurs, Then the layout does not collapse.

### UI Requirements
- App shell with header, main content, footer
- Mobile menu drawer
- Global page container
- Clear page boundaries
- Institutional color palette with Kenyan red accent usage

### Error States
- Global fetch failure: inline error state
- Route 404: safe not-found page
- 500/503: service unavailable state

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-002

### Epic
Design system and public trust visual language

### User Story
As a product user, I want a civic-tech design system grounded in credible government-style visuals, so that the experience feels trustworthy and public-service oriented.

### Backend/API Dependency
Frontend only

### Acceptance Criteria
- Given the app loads, When the design system is applied, Then black, red, green, white, and charcoal are used intentionally and sparingly.
- Given critical states appear, When warnings or civic actions are shown, Then colors are reserved for meaning rather than decoration.
- Given the user reads dense content, When contrast is evaluated, Then text remains readable and accessible.
- Given keyboard navigation is used, When focus lands on controls, Then focus styles are visible.

### UI Requirements
- Public-service styling tokens
- Shared card, form, alert, and button system
- Accessible typography and spacing
- Consistent status colors

### Error States
- N/A

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-003

### Epic
Shared state surfaces

### User Story
As a user, I want consistent loading, empty, and error surfaces, so that every page gives clear feedback when data is not ready or unavailable.

### Backend/API Dependency
Frontend only

### Acceptance Criteria
- Given a request is pending, When data is being fetched, Then a loading state appears.
- Given no results are available, When the section loads, Then an empty state is shown.
- Given an API call fails, When the user interacts, Then an error state appears without breaking the page.
- Given a protected resource is attempted, When access is denied, Then the UI shows a permission state.

### UI Requirements
- Reusable loading skeletons
- Empty state components
- Retry controls
- Permission banner patterns

### Error States
- 401, 403, 404, 422, 429, 500, 503

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 2 — Project Discovery

## Story ID
CIVICACT-FE-004

### Epic
Project list and browsing

### User Story
As a citizen exploring public projects, I want a project list page, so that I can browse relevant public investment and civic work.

### Backend/API Dependency
- GET /api/v1/projects

### Acceptance Criteria
- Given the projects page loads, When the API succeeds, Then project cards render with key metadata.
- Given the API call is pending, When the list loads, Then a loading state renders.
- Given no projects are returned, When the list loads, Then an empty state is shown.
- Given the API fails, When the fetch rejects, Then a safe error state is displayed.

### UI Requirements
- Project listing cards
- Search and filter integration
- Pagination controls
- Tags for project type and status

### Error States
- 404 for invalid filter cases
- 422 for invalid category/subtype combination
- 429 for rate-limit
- 500/503 for backend failure

### Data Mapping
- id
- name
- description
- project_type
- category
- subtype
- status
- location
- page
- page_size
- total

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-005

### Epic
Project search and filtering

### User Story
As a citizen, I want strong search and filtering, so that I can narrow the project list to relevant work.

### Backend/API Dependency
- GET /api/v1/projects

### Acceptance Criteria
- Given a search term is entered, When the user applies it, Then the request includes the query and results update.
- Given filters are selected, When they are applied, Then project results refresh according to those filters.
- Given invalid filter values are returned, When the response has 404 or 422, Then the UI shows a clear state.
- Given the rate limit is triggered, When 429 is returned, Then Retry-After is respected.

### UI Requirements
- Search input
- Filter panel or chips
- County, ward, status and project type selection
- Clear all filters action

### Error States
- 404
- 422
- 429
- 500

### Data Mapping
- query params
- list output

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-006

### Epic
Project list pagination

### User Story
As a citizen, I want project list pagination, so that I can move through larger result sets without losing context.

### Backend/API Dependency
- GET /api/v1/projects

### Acceptance Criteria
- Given multiple pages exist, When the user changes page, Then the request uses the correct page parameter.
- Given the backend returns pagination metadata, When the UI renders, Then page count and total items show correctly.
- Given the user is mobile, When pagination is used, Then controls remain readable.

### UI Requirements
- Previous/next page controls
- Clear page indicator
- Keyboard support for pagination controls

### Error States
- 429
- 500

### Data Mapping
- page
- page_size
- total

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-007

### Epic
Project taxonomy loading

### User Story
As a citizen using filters, I want taxonomy loaded from the API, so that category and subtype values stay current and consistent with backend configuration.

### Backend/API Dependency
- GET /api/v1/project-categories
- GET /api/v1/project-categories/{category_id}/subtypes

### Acceptance Criteria
- Given the category filter loads, When taxonomy data is received, Then it is populated from the API response.
- Given a category is selected, When subtype data loads, Then it is fetched using the category_id.
- Given taxonomy is unavailable, When the request fails, Then the UI shows a safe message.
- Given an invalid filter combination is submitted, When the backend rejects it, Then the UI shows a clear message.

### UI Requirements
- Category selector
- Dynamic subtype selector
- Loading state for taxonomy fetch
- Empty state for missing taxonomy

### Error States
- 404
- 422
- 429
- 500

### Data Mapping
- category: id, code, name, description
- subtype: id, code, name, description

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 3 — Project Detail & Transparency

## Story ID
CIVICACT-FE-008

### Epic
Project detail page

### User Story
As a citizen, I want a project detail page, so that I can review the project’s status and key facts in one place.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}

### Acceptance Criteria
- Given a valid project id, When the page loads, Then the detail view renders project metadata.
- Given the project does not exist, When the endpoint returns 404, Then the user sees a not-found state.
- Given the response includes financial summary data, When the detail page loads, Then summary cards render.
- Given the user is on mobile, When the layout loads, Then it stacks cleanly and stays readable.

### UI Requirements
- Hero/info panel
- Financial summary cards
- Status and metadata blocks
- Timeline and project overview

### Error States
- 404
- 429
- 500

### Data Mapping
- id
- name
- description
- project_type
- category
- subtype
- status
- location
- financial_summary
- verification
- timeline

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-009

### Epic
Project progress and timeline

### User Story
As a citizen, I want the project timeline and progress context, so that I can understand project evolution and current status.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}

### Acceptance Criteria
- Given timeline data exists, When the UI renders it, Then it is structured for clarity.
- Given progress data exists, When displayed, Then it is contextualized as project metadata, not a verified finding.
- Given no timeline data exists, When the section loads, Then the empty state is clear.

### UI Requirements
- Timeline section
- Progress card
- Empty state for missing timeline data

### Error States
- 404
- 500

### Data Mapping
- timeline
- progress

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-010

### Epic
Project sources and provenance

### User Story
As a citizen reviewing project transparency, I want source and claim context, so that I can understand how project information is supported.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/sources

### Acceptance Criteria
- Given claim and source data exists, When the user opens the section, Then it renders in a readable structure.
- Given multiple sources exist, When a claim expands, Then each source item appears in order.
- Given no sources exist, When the section loads, Then the empty state is shown.

### UI Requirements
- Claim cards
- Source chain panel
- Expand/collapse details

### Error States
- 404
- 500
- 429

### Data Mapping
- claim_kind
- field_name
- value_text
- numeric_value
- currency
- financial_period
- sources[]

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-011

### Epic
Project evidence integration

### User Story
As a citizen, I want project evidence linked to the detail page, so that I can connect project information to supporting material without exposing internal storage mechanisms.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}
- GET /api/v1/evidence/{evidence_id}
- GET /api/v1/evidence/{evidence_id}/download

### Acceptance Criteria
- Given evidence is attached to a project, When the detail page loads, Then it shows the associated evidence list.
- Given evidence is public, When the user opens it, Then metadata and available actions render.
- Given evidence is hidden or protected, When access is attempted, Then the UI shows the correct restricted state.
- Given internal storage fields are present, When rendering metadata, Then storage_key is never displayed or relied on.

### UI Requirements
- Evidence card list
- File metadata panel
- Download CTA for public evidence
- Protected evidence messaging

### Error States
- 401
- 403
- 404
- 500
- 429

### Data Mapping
- evidence[] metadata fields
- original_filename
- mime_type
- uploaded_at
- moderation_state
- processing_state
- visibility
- is_deleted

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 4 — Project Taxonomy

## Story ID
CIVICACT-FE-012

### Epic
Category taxonomy view

### User Story
As a citizen, I want category data from the API, so that filter options reflect the configured taxonomy.

### Backend/API Dependency
- GET /api/v1/project-categories

### Acceptance Criteria
- Given taxonomy loads, When the category list renders, Then values come from the API response.
- Given no categories are returned, When the fetch completes, Then an empty state is shown.
- Given the request fails, When the UI loads, Then an error state appears.

### UI Requirements
- Category list or selector
- Loading skeletons
- Empty state

### Error States
- 404
- 429
- 500

### Data Mapping
- id
- code
- name
- description

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-013

### Epic
Subtype taxonomy view

### User Story
As a citizen, I want subtype data to depend on the selected category, so that project filtering reflects backend taxonomy rules.

### Backend/API Dependency
- GET /api/v1/project-categories/{category_id}/subtypes

### Acceptance Criteria
- Given a category is selected, When subtype options load, Then the correct API request is used.
- Given subtype fetch fails, When the user selects a category, Then the UI shows a safe fallback state.
- Given the subtype list is empty, When the control loads, Then an empty state is displayed.

### UI Requirements
- Subtype selector
- Dependent loading logic
- Empty state

### Error States
- 404
- 422
- 429
- 500

### Data Mapping
- id
- code
- name
- description

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-014

### Epic
Taxonomy data hygiene

### User Story
As a product team, I want taxonomy data to be API-backed, so that the frontend does not hard-code categories or subtype definitions.

### Backend/API Dependency
- GET /api/v1/project-categories
- GET /api/v1/project-categories/{category_id}/subtypes

### Acceptance Criteria
- Given taxonomy can be loaded from the API, When the frontend renders it, Then it does not use static definitions.
- Given the backend taxonomy changes, When the app refreshes, Then the UI reflects that backend state.
- Given no taxonomy values are available, When the app loads filters, Then the UI does not invent values.

### UI Requirements
- Centralized taxonomy fetch layer
- API-backed option mapping
- Safe failure handling

### Error States
- 404
- 500
- 429

### Data Mapping
- full taxonomy response objects

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 5 — Civic Action / Issue Reporting

## Story ID
CIVICACT-FE-015

### Epic
Issue report submission

### User Story
As a citizen, I want to submit an issue report against a project, so that I can describe a civic problem and note contact information if needed.

### Backend/API Dependency
- POST /api/v1/projects/{project_id}/reports

### Acceptance Criteria
- Given the report form is valid, When the user submits it, Then the request goes to the backend and success confirmation shows.
- Given the project is missing, When the request hits 404, Then the UI displays a not-found state.
- Given the request is rate-limited, When 429 is returned, Then Retry-After is respected.

### UI Requirements
- Form fields: category, description, optional contact information
- Validation states
- Submit button and loading state
- Success confirmation

### Error States
- 404
- 422
- 429
- 500
- 503

### Data Mapping
- category
- description
- contact_information
- id
- project_id
- status
- submitted_at

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-016

### Epic
Issue form validation

### User Story
As a citizen, I want validation feedback on issue submissions, so that I can correct my report before sending it.

### Backend/API Dependency
- POST /api/v1/projects/{project_id}/reports

### Acceptance Criteria
- Given a required field is empty, When the user submits, Then inline validation displays.
- Given text exceeds the configured limit, When the user types, Then the validation matches the backend contract.
- Given the API rejects the payload, When 422 is returned, Then the UI shows a user-friendly message.

### UI Requirements
- Inline validation messages
- Counter or limit info
- Keyboard-friendly form controls

### Error States
- 422
- 429

### Data Mapping
- request validation constraints

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-017

### Epic
Issue response success and failure states

### User Story
As a citizen, I want clear success and failure states for issue reporting, so that I know whether the report was accepted.

### Backend/API Dependency
- POST /api/v1/projects/{project_id}/reports

### Acceptance Criteria
- Given the report is accepted, When the API responds with 201, Then the UI shows a confirmation state.
- Given the request fails, When the API returns an error, Then a retry state is shown.
- Given the service is unavailable, When 503 is returned, Then the app shows a temporary outage message.

### UI Requirements
- Success toast or confirmation panel
- Retry and resubmit actions
- Graceful posting and network failures

### Error States
- 500
- 503
- 429

### Data Mapping
- response payload from create report

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 6 — Report Tracking

## Story ID
CIVICACT-FE-018

### Epic
Report detail page

### User Story
As a citizen, I want a report detail page, so that I can view the report lifecycle and status history.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}

### Acceptance Criteria
- Given a report exists, When the detail page loads, Then the report status and history are shown.
- Given the report does not exist, When 404 occurs, Then a not-found state is displayed.
- Given no history exists, When the payload is empty, Then the UI shows an empty-state message.

### UI Requirements
- Status summary and timeline
- Report metadata fields
- History rows

### Error States
- 404
- 429
- 500

### Data Mapping
- id
- project_id
- category
- status
- submitted_at
- status_history[]

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-019

### Epic
Report channels and institutions

### User Story
As a citizen, I want to inspect reporting channels and institution relationships, so that I understand how the issue is routed and who is involved.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}/channels
- GET /api/v1/reports/{report_id}/institutions

### Acceptance Criteria
- Given channel data exists, When the panel opens, Then office and destination metadata render.
- Given institution relationships exist, When the user opens the section, Then they render clearly.
- Given no channel or institution data exists, When the panel loads, Then an empty state is shown.

### UI Requirements
- Reporting channels list
- Institution relationships list
- Empty state for no relationship data

### Error States
- 404
- 500
- 429

### Data Mapping
- channels: id, office_name, channel_type, destination, display_label, priority
- institutions: institution_id, institution_name, institution_role, relationship_type

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-020

### Epic
Report responses and comparison

### User Story
As a citizen, I want to compare the original issue with institutional responses, so that I can review the issue and response context side by side.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}/responses
- GET /api/v1/reports/{report_id}/comparison

### Acceptance Criteria
- Given responses exist, When the comparison view loads, Then the original issue and responses are grouped clearly.
- Given no responses exist, When the section loads, Then the UI shows a no-response state.
- Given the report is missing, When 404 is returned, Then the missing-report state appears.

### UI Requirements
- Comparison view
- Response cards
- No-response state
- Clear grouping between issue and responses

### Error States
- 404
- 429
- 500

### Data Mapping
- issue data
- responses[]
- institution details

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-021

### Epic
Read-only status experience

### User Story
As a citizen, I want a read-only report status experience, so that I understand current API status without assuming any unsupported mutation capability.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}
- GET /api/v1/reports/{report_id}/comparison

### Acceptance Criteria
- Given the report status is shown, When it renders, Then it only reflects the backend state.
- Given no public status mutation route exists, When the UI is built, Then no status update controls are shown.
- Given a report is resolved, When the backend states it, Then the UI displays it as backend-reported status only.

### UI Requirements
- Read-only status timeline
- No editing controls
- Display-only lifecycle messaging

### Error States
- 404
- 500

### Data Mapping
- status_history[]
- status

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 7 — Comments & Community Discussion

## Story ID
CIVICACT-FE-022

### Epic
Public comments list

### User Story
As a citizen participating in project discussions, I want to view project comments, so that I can understand community feedback and current public discussion.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/comments

### Acceptance Criteria
- Given public comments are available, When the project page loads, Then the comments list renders.
- Given hidden or removed comments exist, When the backend excludes them, Then they are not shown.
- Given no public comments exist, When the section loads, Then the empty state appears.

### UI Requirements
- Comment thread list
- Clear moderation-status tags
- Empty state for no comments

### Error States
- 404
- 429
- 500

### Data Mapping
- conversation metadata and moderation state

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-023

### Epic
Comment submission

### User Story
As a citizen, I want to submit a public comment, so that I can contribute to project discussion.

### Backend/API Dependency
- POST /api/v1/projects/{project_id}/comments

### Acceptance Criteria
- Given the user enters valid comment content, When the form submits, Then it is posted successfully and the list updates.
- Given the content is invalid, When the API rejects it, Then inline validation appears.
- Given the project is missing, When the API returns 404, Then the UI shows a not-found state.
- Given the user is rate limited, When 429 is returned, Then Retry-After is respected.

### UI Requirements
- Comment composer
- Content validation
- Loading state on submit
- Success confirmation

### Error States
- 404
- 422
- 429
- 500

### Data Mapping
- author_id
- content
- parent_comment_id
- project_id
- status
- moderation_state
- visibility

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-024

### Epic
Comment abuse reporting

### User Story
As a citizen, I want to report inappropriate comments, so that harmful or abusive content can be reviewed by the platform.

### Backend/API Dependency
- POST /api/v1/comments/{comment_id}/reports

### Acceptance Criteria
- Given the user selects a report reason and submits it, When the API accepts it, Then a confirmation message is shown.
- Given the comment does not exist, When 404 is returned, Then the missing-comment state appears.
- Given the rate limit is reached, When 429 is returned, Then the user sees a clear retry message.

### UI Requirements
- Report reason selection
- Submit and confirmation flow
- Rate-limit warning

### Error States
- 404
- 429
- 500

### Data Mapping
- comment_id
- reporter_id
- reason
- status
- submitted_at

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-025

### Epic
Comment trust and framing

### User Story
As a product user, I want community discussion to clearly distinguish public comments from verified information, so that the UI does not overstate trust.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/comments

### Acceptance Criteria
- Given comments display in the UI, When they appear publicly, Then they are framed as citizen-submitted information rather than verified fact.
- Given moderation state appears, When the UI renders it, Then it is represented as moderation metadata, not public verification.
- Given the user reads the section, When trust context is interpreted, Then it reinforces evidence-before-conclusions.

### UI Requirements
- Trust status labels
- Copy clarifying citizen-submitted content
- Distinct styling from verification panel

### Error States
- 404
- 429
- 500

### Data Mapping
- moderation_state
- visibility
- status

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 8 — Evidence

## Story ID
CIVICACT-FE-026

### Epic
Evidence upload

### User Story
As a citizen submitting evidence, I want to upload an allowed file type, so that I can attach support material to a comment, report, or project.

### Backend/API Dependency
- POST /api/v1/comments/{comment_id}/evidence
- POST /api/v1/reports/{report_id}/evidence
- POST /api/v1/projects/{project_id}/evidence
- POST /api/v1/projects/{project_id}/reports/{report_id}/evidence

### Acceptance Criteria
- Given a supported file type is selected, When upload starts, Then the backend request is made using the correct API contract.
- Given an unsupported file is chosen, When the upload starts, Then the UI shows validation feedback.
- Given the API rejects the payload, When 422 is returned, Then the user sees a validation state.
- Given the user is rate-limited, When 429 is returned, Then the UI respects Retry-After.

### UI Requirements
- File picker or drag-and-drop upload
- Allowed type validation
- Loading state during upload
- Metadata summary after success

### Error States
- 404
- 422
- 429
- 500
- 503

### Data Mapping
- uploader_id
- file
- metadata response fields

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-027

### Epic
Evidence metadata view

### User Story
As a citizen, I want to view uploaded evidence metadata, so that I can understand what was uploaded and how it is classified.

### Backend/API Dependency
- GET /api/v1/evidence/{evidence_id}

### Acceptance Criteria
- Given evidence metadata loads successfully, When the user opens it, Then filename, type, upload time, and state values render.
- Given evidence is hidden or removed, When the record is requested, Then a not-found state appears.
- Given the evidence is protected, When the user lacks access, Then a protected-access state is shown.

### UI Requirements
- Data panel for evidence metadata
- Public/protected distinction
- Empty state if no metadata is available

### Error States
- 401
- 403
- 404
- 500
- 429

### Data Mapping
- id
- original_filename
- mime_type
- file_size_bytes
- checksum_sha256
- moderation_state
- processing_state
- visibility
- uploaded_at

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-028

### Epic
Evidence download behavior

### User Story
As a citizen, I want evidence download behavior that follows the backend’s public-versus-protected rules, so that I can safely access public evidence without guessing behind protected boundaries.

### Backend/API Dependency
- GET /api/v1/evidence/{evidence_id}/download

### Acceptance Criteria
- Given evidence is public, When the user triggers download, Then the file can be served through the API contract.
- Given evidence is hidden or removed, When the request hits 404, Then a not-found state is shown.
- Given evidence is protected, When access is denied, Then a permission state is shown.
- Given file retrieval fails, When 500 is returned, Then a retrieval failure UI appears.

### UI Requirements
- Download button
- Protected evidence notice
- Download failure handling

### Error States
- 401
- 403
- 404
- 500
- 429

### Data Mapping
- actual file content and metadata response from the backend

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-029

### Epic
Evidence processing state

### User Story
As a user reviewing evidence, I want to see processing state and artifact lineage, so that I understand the evidence lifecycle without relying on unsupported internal storage paths.

### Backend/API Dependency
- GET /api/v1/evidence/{evidence_id}/processing

### Acceptance Criteria
- Given processing metadata exists, When the user opens the section, Then the processing timeline and artifact list render.
- Given no processing data exists, When the section loads, Then an empty state is shown.
- Given the API fails, When the section loads, Then an error state is shown.

### UI Requirements
- Processing summary card
- Event timeline
- Derived artifacts list

### Error States
- 404
- 429
- 500

### Data Mapping
- evidence_id
- processing_state
- events[]
- derived_artifacts[]

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-030

### Epic
Evidence contract boundaries

### User Story
As a product team, I want the frontend to never expose storage keys or rely on backend-internal file paths, so that evidence handling remains consistent with the public contract.

### Backend/API Dependency
- All evidence endpoints

### Acceptance Criteria
- Given evidence metadata is rendered, When the UI shows it, Then it does not expose storage_key.
- Given public evidence flows are used, When actions fire, Then they use the public API endpoints, not internal storage assumptions.
- Given the backend later changes its internal implementation, When the UI refreshes, Then it remains aligned to the public contract.

### UI Requirements
- No storage_key rendering
- No internal path assumptions
- Public API-only download flow

### Error States
- 404 / 500 / 429

### Data Mapping
- public response payload only

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 9 — Verification

## Story ID
CIVICACT-FE-031

### Epic
Project verification panel

### User Story
As a citizen, I want to see project verification state, so that I know whether the project has an active verification record.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/verification

### Acceptance Criteria
- Given verification exists, When the user loads project detail, Then the status is displayed.
- Given there is no verification record, When the page loads, Then the UI states that the project is unverified rather than implying trust.
- Given the verification status is stale or disputed, When shown, Then the state is presented clearly.

### UI Requirements
- Verification status card
- Notes and dates
- Distinct visual treatment from citizen content

### Error States
- 404
- 429
- 500

### Data Mapping
- status
- verification_date
- recorded_at
- notes
- source

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-032

### Epic
Verification and citizen-content separation

### User Story
As a general public user, I want verification and citizen-submitted content clearly separated, so that I can understand what is confirmed versus what is public input.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/verification
- GET /api/v1/projects/{project_id}/sources

### Acceptance Criteria
- Given both verification and citizen content are displayed, When a user reads the project, Then they are visually distinct.
- Given citizen-submitted information is shown, When the UI renders it, Then it is not labeled as verified by default.
- Given the user reviews the page, When they evaluate evidence, Then the UI reinforces evidence-before-conclusions.

### UI Requirements
- Verification panel and citizen content separation
- Trust labeling patterns
- No false certainty wording

### Error States
- 404
- 500
- 429

### Data Mapping
- verification fields
- source data

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 10 — Deterministic Review Signals / Anomalies

## Story ID
CIVICACT-FE-033

### Epic
Anomaly listing

### User Story
As a general public user, I want deterministic review signals displayed transparently, so that I understand project risk signals without mistaking them for confirmed faults.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/anomalies

### Acceptance Criteria
- Given anomaly data exists, When the detail page loads, Then it renders in a list.
- Given the anomaly is a review signal, When it appears, Then it is clearly labeled as a review signal.
- Given no anomaly signals exist, When the section loads, Then an empty state is shown.

### UI Requirements
- Alert card list
- Labeling for review signal status
- Empty state if none exist

### Error States
- 404
- 429
- 500

### Data Mapping
- type
- status
- message
- requires_verification
- supporting_claims[]

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-034

### Epic
Anomaly details and support claims

### User Story
As a user reviewing anomalies, I want to see support claims and context, so that I can understand why a review signal was raised.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/anomalies

### Acceptance Criteria
- Given a signal includes supporting claims, When the user expands it, Then the supporting claim list displays.
- Given metrics exist, When they render, Then they are readable and non-accusatory.
- Given the user is on mobile, When the detail expands, Then the layout remains usable.

### UI Requirements
- Expandable anomaly detail cards
- Supporting claims list
- Readable metric display

### Error States
- 404
- 500
- 429

### Data Mapping
- message
- metrics
- supporting_claims[]

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-035

### Epic
Anomaly verification separation

### User Story
As a user, I want anomaly results clearly separated from verified information, so that I do not confuse review signals with confirmed project status.

### Backend/API Dependency
- GET /api/v1/projects/{project_id}/anomalies
- GET /api/v1/projects/{project_id}/verification

### Acceptance Criteria
- Given a project has both verification and anomalies, When the page loads, Then the anomaly state is clearly different from verified status.
- Given anomaly content is displayed, When the user reads it, Then it is not framed as a finding or accusation.
- Given the UI is built for public trust, When review signals are shown, Then the wording is careful and evidential.

### UI Requirements
- Visual contrast between review signals and verification status
- Neutral copy with no accusation language
- Card-level note explaining review-signal semantics

### Error States
- 404
- 429
- 500

### Data Mapping
- verification status
- anomaly metadata

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 11 — Institutions & Responses

## Story ID
CIVICACT-FE-036

### Epic
Institution relationships

### User Story
As a citizen, I want to see institutions linked to a report, so that I can understand which offices or bodies are connected to the issue.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}/institutions

### Acceptance Criteria
- Given institutions exist, When the report page loads, Then their names and roles render clearly.
- Given there are no linked institutions, When the section loads, Then an empty state explains that no institutions are currently linked.
- Given the API fails, When the section loads, Then the UI shows a safe error state.

### UI Requirements
- Institution relationship list
- Empty state for no linked institutions

### Error States
- 404
- 429
- 500

### Data Mapping
- institution_id
- institution_name
- institution_role
- relationship_type

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-037

### Epic
Institution responses

### User Story
As a citizen, I want to view institution responses to a report, so that I can understand the public response context.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}/responses

### Acceptance Criteria
- Given responses exist, When the user opens the response section, Then the institution and response content render clearly.
- Given no responses are available, When the section loads, Then the empty state says no response has been provided yet.
- Given response content is long, When displayed, Then readability and spacing remain strong.

### UI Requirements
- Response cards
- Empty state if no response exists
- Readable typography for content blocks

### Error States
- 404
- 429
- 500

### Data Mapping
- institution details
- content
- created_at

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-038

### Epic
Report and response comparison

### User Story
As a citizen, I want a comparison view between the original report and institutional responses, so that I can inspect the relationship between the issue and the response.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}/comparison

### Acceptance Criteria
- Given the comparison payload loads, When the view renders, Then the issue and response content are grouped clearly.
- Given no responses exist, When the section loads, Then the no-response state appears.
- Given the report is missing, When 404 occurs, Then the missing-report state appears.

### UI Requirements
- Side-by-side comparison view or grouped cards
- Original issue block
- Institution response block

### Error States
- 404
- 429
- 500

### Data Mapping
- issue payload
- responses[]

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-039

### Epic
Read-only response UX

### User Story
As a public user, I want no invented institution-response mutation controls, so that the UI represents only the current supported public capabilities.

### Backend/API Dependency
- GET /api/v1/reports/{report_id}/responses
- GET /api/v1/reports/{report_id}/comparison

### Acceptance Criteria
- Given no public mutation route exists, When the UI is built, Then no create or update controls are shown.
- Given the interface renders responses, When the user reads the page, Then the content is presentation-only.
- Given the user expects actions, When they inspect the page, Then they are clearly in a read-only public view.

### UI Requirements
- Read-only response list
- No editing actions
- Contextual explanatory copy

### Error States
- 404
- 500
- 429

### Data Mapping
- public response payload only

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 12 — Moderation

## Story ID
CIVICACT-FE-040

### Epic
Comment moderation actions

### User Story
As a moderator, I want to review a reported comment and apply an action, so that harmful content can be moderated under the current permission boundary.

### Backend/API Dependency
- POST /api/v1/comments/{comment_id}/moderation
- GET /api/v1/comments/{comment_id}/moderation-history

### Acceptance Criteria
- Given a moderator is able to act, When they submit a moderation action, Then the request is sent to the correct endpoint.
- Given the comment is missing, When the action happens, Then the UI shows a missing-resource state.
- Given the API returns 401 or 403, When access is denied, Then the UI shows the restricted state without exposing internals.

### UI Requirements
- Moderator action panel
- Reason and notes inputs
- History timeline

### Error States
- 401
- 403
- 404
- 409
- 429
- 500

### Data Mapping
- action
- reason
- notes
- history payload

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-041

### Epic
Evidence moderation actions

### User Story
As a moderator, I want to review evidence moderation history, so that I can track actions taken and the current evidence state.

### Backend/API Dependency
- POST /api/v1/evidence/{evidence_id}/moderation
- GET /api/v1/evidence/{evidence_id}/moderation-history

### Acceptance Criteria
- Given the user opens evidence moderation actions, When the data loads, Then the moderation history and actions display.
- Given the evidence record is missing, When the API returns 404, Then the UI shows the safe not-found state.
- Given the moderation transition is invalid, When 409 is returned, Then the user sees the reason and can retry correctly.

### UI Requirements
- Evidence moderation controls
- History timeline
- Invalid transition messaging

### Error States
- 401
- 403
- 404
- 409
- 429
- 500

### Data Mapping
- moderation action details
- history response

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-042

### Epic
Permission-aware moderation UX

### User Story
As a moderator, I want stable moderation-state UX, so that the interface communicates the current state while preserving the current backend permission model.

### Backend/API Dependency
- All moderation endpoints

### Acceptance Criteria
- Given a moderator action succeeds, When the UI updates, Then the comment or evidence state reflects the backend result.
- Given the user lacks permission, When moderation UI is accessed, Then the UI presents a permission state instead of internal error details.
- Given no real authentication system exists, When the UI is built, Then it does not invent login or token flows.

### UI Requirements
- Protected-access messaging
- Action feedback and outcomes
- Read-only placeholder state for no auth system

### Error States
- 401
- 403
- 404
- 409
- 429
- 500
- 503

### Data Mapping
- moderation action result fields

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 13 — Health & Backend Status

## Story ID
CIVICACT-FE-043

### Epic
Platform health status

### User Story
As a platform user, I want to see backend service health indicators, so that I know whether the public service is operational.

### Backend/API Dependency
- GET /api/v1/health
- GET /api/v1/health/ready

### Acceptance Criteria
- Given the health endpoint succeeds, When the app loads, Then the platform status can be shown safely.
- Given the readiness endpoint reports not ready, When the app loads data, Then an operational warning appears.
- Given the health endpoint fails with 503, When the user loads the app, Then the outage state is shown.

### UI Requirements
- Health banner or status indicator
- Minimal operational message
- Service unavailable state

### Error States
- 503
- 500

### Data Mapping
- status
- readiness payload

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-044

### Epic
Minimal health messaging

### User Story
As a product maintainer, I want health status displayed clearly but minimally, so that public users receive operational information without being overwhelmed by internal diagnostics.

### Backend/API Dependency
- GET /api/v1/health
- GET /api/v1/health/ready

### Acceptance Criteria
- Given the system is healthy, When health is checked, Then the message remains quiet and non-noisy.
- Given the backend is degraded, When the status is not ready, Then clear public instructions appear.
- Given the user is on a public page, When a problem exists, Then the message remains useful and understandable.

### UI Requirements
- Compact public status message
- Optional operational banner
- No internal debug details

### Error States
- 500
- 503

### Data Mapping
- status fields from health endpoints

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 14 — API Error, Loading, Empty and Permission States

## Story ID
CIVICACT-FE-045

### Epic
Loading state consistency

### User Story
As a user, I want consistent API loading states, so that I know when public data is still loading.

### Backend/API Dependency
- Any public endpoint

### Acceptance Criteria
- Given a public page fetches data, When the request is pending, Then a loading state is displayed.
- Given multiple API calls happen in a screen, When they are pending, Then the load states remain consistent.
- Given data is slow, When the page waits, Then the loading message remains clear and accessible.

### UI Requirements
- Skeletons or spinners
- Reusable loading component
- Section-level loading patterns

### Error States
- 429
- 500
- 503

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-046

### Epic
Empty state consistency

### User Story
As a user, I want consistent empty states, so that I know when the backend has no public data for a section.

### Backend/API Dependency
- Any public endpoint

### Acceptance Criteria
- Given a list or section is empty, When the data loads, Then a clear empty state appears.
- Given a page has no data, When the user reads it, Then the UI explains the condition instead of showing blank space.
- Given the user is on mobile, When the empty state appears, Then it remains readable and useful.

### UI Requirements
- Reusable empty-state components
- Clear copy for no-data state
- Section-level fallback UI

### Error States
- 404
- 500

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-047

### Epic
API error handling

### User Story
As a user, I want consistent API error states, so that I understand backend problems and know what action to take next.

### Backend/API Dependency
- All public and protected endpoints

### Acceptance Criteria
- Given 401 occurs, When a protected action is attempted, Then a permission message appears.
- Given 403 occurs, When access is denied, Then the action is clearly explained.
- Given 404 occurs, When the resource is missing, Then a not-found state is displayed.
- Given 409 occurs, When a conflict exists, Then the conflict reason is shown.
- Given 422 occurs, When validation fails, Then the form or field error is shown.
- Given 429 occurs, When rate limiting occurs, Then Retry-After is respected and the user is informed.
- Given 500 or 503 occurs, When the backend is unstable, Then a generic public-safe outage state is shown.

### UI Requirements
- Global and section-level error handling
- Retry actions
- Public-safe error messages

### Error States
- 401
- 403
- 404
- 409
- 422
- 429
- 500
- 503

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-048

### Epic
Permission-state handling

### User Story
As a citizen or moderator, I want explicit permission-state messaging, so that I understand protected content boundaries without false assumptions.

### Backend/API Dependency
- Protected endpoints only

### Acceptance Criteria
- Given protected content is attempted without permission, When access is denied, Then the UI shows a permission state.
- Given the backend has no auth flow, When the user reaches protected functionality, Then the system presents the backend boundary honestly.
- Given a permission error is returned, When the message appears, Then it explains the restriction without exposing internal implementation details.

### UI Requirements
- Permission banners or restricted-state cards
- Clear messaging without fake login UX

### Error States
- 401
- 403

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

# EPIC 15 — Accessibility, Responsiveness & Production Readiness

## Story ID
CIVICACT-FE-049

### Epic
Accessibility compliance

### User Story
As a citizen using assistive devices, I want accessible public pages, so that I can navigate and understand civic information effectively.

### Backend/API Dependency
Frontend only

### Acceptance Criteria
- Given a user navigates by keyboard, When focus moves, Then visible focus styles are present.
- Given a form field is required, When it is labeled, Then it is accessible to assistive technology.
- Given a list or detail view is rendered, When a screen reader reads it, Then the structure remains understandable.
- Given interactive controls exist, When focus is managed, Then there are no keyboard traps or hidden interactions.

### UI Requirements
- Semantic markup
- Focus states
- Labels and aria attributes when appropriate
- Form and list accessibility checks

### Error States
- N/A

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-050

### Epic
Responsive design

### User Story
As a user on any device, I want the platform to adapt to mobile, tablet, and desktop layouts, so that public information remains usable everywhere.

### Backend/API Dependency
Frontend only

### Acceptance Criteria
- Given the app is viewed on mobile, When content loads, Then it stacks gracefully and remains readable.
- Given the user is on tablet or desktop, When layouts are rendered, Then density remains useful and not cramped.
- Given forms are used on smaller screens, When the user interacts, Then controls remain usable and legible.

### UI Requirements
- Responsive layouts
- Mobile-first card stacking
- Form resizing and touch targets

### Error States
- N/A

### Data Mapping
None

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Story ID
CIVICACT-FE-051

### Epic
Production readiness and contract validation

### User Story
As a product team, I want production-ready quality checks, so that the platform is reliable, testable, and aligned with the backend contract.

### Backend/API Dependency
- All mounted public and protected endpoints

### Acceptance Criteria
- Given the frontend is implemented, When stakeholders review it, Then each screen maps to the correct API contract.
- Given stories are built, When tests run, Then UI tests cover happy-path, error-path, and empty-state behaviors.
- Given an unsupported feature is identified, When it is under review, Then it is marked as backend dependency / not currently available.
- Given hidden or protected evidence is encountered, When the UI renders, Then it follows the API contract and not invented assumptions.

### UI Requirements
- Test coverage plan
- Contract validation review
- UX and accessibility review
- Final readiness checklist review

### Error States
- all relevant API states

### Data Mapping
- contract mapping for each supported screen

### Definition of Done
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

---

## Traceability summary

| Story ID | Epic | Screen/Component | API Endpoint | Backend Supported? | Status |
|---|---|---|---|---|---|
| CIVICACT-FE-001 | EPIC 1 | App shell | Frontend only | No | Planned |
| CIVICACT-FE-002 | EPIC 1 | Design system | Frontend only | No | Planned |
| CIVICACT-FE-003 | EPIC 1 | Shared state surfaces | Frontend only | No | Planned |
| CIVICACT-FE-004 | EPIC 2 | Projects list | GET /api/v1/projects | Yes | Planned |
| CIVICACT-FE-005 | EPIC 2 | Search and filters | GET /api/v1/projects | Yes | Planned |
| CIVICACT-FE-006 | EPIC 2 | Pagination | GET /api/v1/projects | Yes | Planned |
| CIVICACT-FE-007 | EPIC 2 | Taxonomy filters | GET /api/v1/project-categories; GET /api/v1/project-categories/{category_id}/subtypes | Yes | Planned |
| CIVICACT-FE-008 | EPIC 3 | Project detail | GET /api/v1/projects/{project_id} | Yes | Planned |
| CIVICACT-FE-009 | EPIC 3 | Timeline and progress | GET /api/v1/projects/{project_id} | Yes | Planned |
| CIVICACT-FE-010 | EPIC 3 | Sources | GET /api/v1/projects/{project_id}/sources | Yes | Planned |
| CIVICACT-FE-011 | EPIC 3 | Evidence integration | GET /api/v1/projects/{project_id}; GET /api/v1/evidence/{evidence_id}; GET /api/v1/evidence/{evidence_id}/download | Yes | Planned |
| CIVICACT-FE-012 | EPIC 4 | Category taxonomy | GET /api/v1/project-categories | Yes | Planned |
| CIVICACT-FE-013 | EPIC 4 | Subtype taxonomy | GET /api/v1/project-categories/{category_id}/subtypes | Yes | Planned |
| CIVICACT-FE-014 | EPIC 4 | Taxonomy data layer | GET /api/v1/project-categories; GET /api/v1/project-categories/{category_id}/subtypes | Yes | Planned |
| CIVICACT-FE-015 | EPIC 5 | Issue reporting | POST /api/v1/projects/{project_id}/reports | Yes | Planned |
| CIVICACT-FE-016 | EPIC 5 | Report validation | POST /api/v1/projects/{project_id}/reports | Yes | Planned |
| CIVICACT-FE-017 | EPIC 5 | Report success and failure states | POST /api/v1/projects/{project_id}/reports | Yes | Planned |
| CIVICACT-FE-018 | EPIC 6 | Report detail | GET /api/v1/reports/{report_id} | Yes | Planned |
| CIVICACT-FE-019 | EPIC 6 | Channels and institutions | GET /api/v1/reports/{report_id}/channels; GET /api/v1/reports/{report_id}/institutions | Yes | Planned |
| CIVICACT-FE-020 | EPIC 6 | Comparison view | GET /api/v1/reports/{report_id}/responses; GET /api/v1/reports/{report_id}/comparison | Yes | Planned |
| CIVICACT-FE-021 | EPIC 6 | Read-only report status | GET /api/v1/reports/{report_id}; GET /api/v1/reports/{report_id}/comparison | Yes | Planned |
| CIVICACT-FE-022 | EPIC 7 | Comments list | GET /api/v1/projects/{project_id}/comments | Yes | Planned |
| CIVICACT-FE-023 | EPIC 7 | Comment composer | POST /api/v1/projects/{project_id}/comments | Yes | Planned |
| CIVICACT-FE-024 | EPIC 7 | Comment reporting | POST /api/v1/comments/{comment_id}/reports | Yes | Planned |
| CIVICACT-FE-025 | EPIC 7 | Comment trust framing | GET /api/v1/projects/{project_id}/comments | Yes | Planned |
| CIVICACT-FE-026 | EPIC 8 | Evidence upload | POST evidence endpoints | Yes | Planned |
| CIVICACT-FE-027 | EPIC 8 | Evidence metadata | GET /api/v1/evidence/{evidence_id} | Yes | Planned |
| CIVICACT-FE-028 | EPIC 8 | Evidence download | GET /api/v1/evidence/{evidence_id}/download | Yes | Planned |
| CIVICACT-FE-029 | EPIC 8 | Processing state | GET /api/v1/evidence/{evidence_id}/processing | Yes | Planned |
| CIVICACT-FE-030 | EPIC 8 | Storage contract guardrails | All evidence endpoints | Yes | Planned |
| CIVICACT-FE-031 | EPIC 9 | Verification panel | GET /api/v1/projects/{project_id}/verification | Yes | Planned |
| CIVICACT-FE-032 | EPIC 9 | Verification framing | GET /api/v1/projects/{project_id}/verification; GET /api/v1/projects/{project_id}/sources | Yes | Planned |
| CIVICACT-FE-033 | EPIC 10 | Anomaly list | GET /api/v1/projects/{project_id}/anomalies | Yes | Planned |
| CIVICACT-FE-034 | EPIC 10 | Anomaly support details | GET /api/v1/projects/{project_id}/anomalies | Yes | Planned |
| CIVICACT-FE-035 | EPIC 10 | Review-signal separation | GET /api/v1/projects/{project_id}/anomalies; GET /api/v1/projects/{project_id}/verification | Yes | Planned |
| CIVICACT-FE-036 | EPIC 11 | Institutions list | GET /api/v1/reports/{report_id}/institutions | Yes | Planned |
| CIVICACT-FE-037 | EPIC 11 | Response list | GET /api/v1/reports/{report_id}/responses | Yes | Planned |
| CIVICACT-FE-038 | EPIC 11 | Comparison view | GET /api/v1/reports/{report_id}/comparison | Yes | Planned |
| CIVICACT-FE-039 | EPIC 11 | Read-only response UX | GET /api/v1/reports/{report_id}/responses; GET /api/v1/reports/{report_id}/comparison | Yes | Planned |
| CIVICACT-FE-040 | EPIC 12 | Comment moderation | POST /api/v1/comments/{comment_id}/moderation; GET /api/v1/comments/{comment_id}/moderation-history | Yes | Planned |
| CIVICACT-FE-041 | EPIC 12 | Evidence moderation | POST /api/v1/evidence/{evidence_id}/moderation; GET /api/v1/evidence/{evidence_id}/moderation-history | Yes | Planned |
| CIVICACT-FE-042 | EPIC 12 | Moderation access handling | All moderation endpoints | Yes | Planned |
| CIVICACT-FE-043 | EPIC 13 | Health status | GET /api/v1/health; GET /api/v1/health/ready | Yes | Planned |
| CIVICACT-FE-044 | EPIC 13 | Health messaging | GET /api/v1/health; GET /api/v1/health/ready | Yes | Planned |
| CIVICACT-FE-045 | EPIC 14 | Loading states | Any public endpoint | Yes | Planned |
| CIVICACT-FE-046 | EPIC 14 | Empty states | Any public endpoint | Yes | Planned |
| CIVICACT-FE-047 | EPIC 14 | Error states | All public and protected endpoints | Yes | Planned |
| CIVICACT-FE-048 | EPIC 14 | Permission states | Protected endpoints only | Partial | Planned |
| CIVICACT-FE-049 | EPIC 15 | Accessibility | Frontend only | No | Planned |
| CIVICACT-FE-050 | EPIC 15 | Responsiveness | Frontend only | No | Planned |
| CIVICACT-FE-051 | EPIC 15 | Production readiness | All mounted endpoints | Yes | Planned |

## Final scope note

This specification includes every currently available frontend capability documented in the API guide and excludes unsupported features such as real login, real auth flows, AI endpoints, storage URL architecture, and invented backend capabilities. All stories remain aligned to the current backend contract and product principles.
