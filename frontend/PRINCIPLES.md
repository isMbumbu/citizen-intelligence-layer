# CIVICACT Frontend Principles

## Product mission

CIVICACT is a Kenyan civic-tech platform for public projects, spending transparency, citizen reporting, evidence, verification, and accountability. The frontend must help citizens understand public information clearly, act responsibly, and evaluate claims with evidence rather than assumption.

## Product promise

The product should feel credible, public-service oriented, transparent, modern, and accessible. It should support the public interest without overstating facts or presenting citizen input as verified truth.

## Core product principles

### 1. Evidence before conclusions
- Never frame citizen-submitted content as verified.
- Never imply a report is resolved unless the API explicitly says so.
- Treat deterministic anomalies as review signals, not accusations or verified findings.
- Prioritize provenance, source chain, and explanation over polished marketing language.

### 2. Clear distinction between content types
- Verified information must be visually and semantically distinct from citizen-submitted content.
- Public discussion and evidence must not be confused with official verification.
- Review signals must be labeled clearly as non-finding, non-accusation review metadata.

### 3. Public trust through transparency
- Show what is known, what is unverified, and what is under review.
- Avoid false certainty and avoid hiding uncertainty when the backend contract is limited.
- Preserve a clear difference between facts, claims, and risk signals.

### 4. API contract adherence
- Treat the frontend API integration guide as the single source of truth.
- Do not invent unauthorized endpoints, authentication flows, AI endpoints, or backend capabilities.
- If a feature is not currently available in the backend, mark it as backend dependency / not currently available.
- Do not depend on internal storage keys or private file paths.

### 5. Respect the current backend boundaries
- There is no real login, registration, JWT, session, API-key, token issuance, or refresh flow in the current backend.
- Protected routes are backend permission-bound, not frontend-authenticated flows.
- The frontend must not create fake auth experiences or imply system access that does not exist.

### 6. Progressive disclosure
- Keep complex project information understandable by layering detail.
- Expose summary information first, then allow deeper inspection of evidence, sources, and reviews.
- Avoid overwhelming users with unneeded detail on initial load.

### 7. Strong search and filtering
- Search and filters must help citizens quickly discover relevant public projects and detail.
- Taxonomy must be loaded from the API rather than hard-coded.
- Filtering logic should be predictable, debuggable, and accessible.

### 8. State handling is part of the product
- Loading, empty, error, and permission states are mandatory.
- Handle 401, 403, 404, 409, 422, 429, 500, and 503 explicitly where applicable.
- Respect Retry-After and rate-limit headers for 429 responses.

### 9. Accessible civic service design
- High contrast and legible typography are mandatory.
- Keyboard navigation and focus states must work across all interactive components.
- Forms must have clear labels and helpful validation feedback.
- Mobile responsiveness is non-negotiable.

### 10. Design language and civic trust
Use the following design principles:
- Black as a strong institutional/navigation anchor.
- Kenyan red as accent for important actions, warnings, reporting, civic-action emphasis, and public risk states.
- Kenyan green for positive, verified, healthy, or ready states.
- White and very light neutrals for clarity and calm reading.
- Dark charcoal text for excellent readability.
- Use accent colors sparingly and consistently; do not make the interface a literal Kenyan flag.
- Avoid excessive gradients, glassmorphism, neon color schemes, and AI-dashboard styling.

## Content and UX principles

### Public information must be readable
- Use concise, plain-language explanations for public project and reporting data.
- Pair metrics with context; avoid unqualified numbers.
- Avoid jargon and legalistic language where civic language is clearer.

### Evidence-first communication
- Show evidence summaries and source chains where available.
- Link report status to actual API state instead of generic claims.
- Separate reasoned review signals from certified findings.

### Civic action must be clear and safe
- Users should always know whether they are submitting a citizen report, a public comment, or evidence.
- Success confirmations must be explicit and non-misleading.
- The interface must avoid implying that a report has been resolved unless the backend says so.

### Protected access must be honest
- If a route or action is protected by the backend permission model, communicate that fact rather than creating fake login UX.
- Keep the experience readable, not technically confusing.

## Frontend implementation standards

### Respect for backend capability
- All page and component work must map to a real backend endpoint or a frontend-only UX requirement needed to consume an existing endpoint.
- Use the API guide as the source of truth for available routes and response contracts.
- Any unsupported capability must be marked as: Backend dependency / not currently available.

### Data handling rules
- Never expose or depend on storage_key.
- Never construct or rely on file paths or storage URLs not described by the API.
- Treat taxonomy as API-backed data, not hard-coded front-end definitions.
- Handle non-verified data with neutral wording.

### Testing expectations
- Tests should cover the default state, loading state, empty state, and error states for each story.
- Validate API contract mapping and error handling, especially 401, 403, 404, 409, 422, 429, 500, and 503 flows.
- Do not assert mock-only behavior; verify the real UI and API state transitions.

## Definition of done for every frontend story
A story is done only when all of the following are true:
- responsive implementation
- accessibility
- loading state
- empty state
- error state
- API integration
- validation
- tests where appropriate
- no invented API behavior

## Product boundaries

The frontend may implement:
- project discovery and detail views
- project taxonomy loading and filtering
- public citizen reporting flows
- report tracking and comparison views
- public comments and abuse reporting
- evidence upload and retrieval interfaces
- verification display
- deterministic anomaly visualization
- read-only institution and response display
- moderation UI for the configured backend permission boundary
- health and system-status messaging

The frontend must not implement as current product capability:
- real login or registration
- JWT/session/API-key flows
- token issuance or refresh
- signed-URL architecture
- database-backed ingestion or AI features not mounted by the backend
- fabricated storage contracts or fake auth experiences

## Summary

The frontend should be a trustworthy civic information experience that helps citizens understand public projects and accountability flows without overclaiming certainty. It must be evidence-first, API-driven, backend-honest, accessible, and production-ready.
