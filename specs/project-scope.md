# Citizen Intelligence Layer product scope

## Product goal

The Citizen Intelligence Layer turns fragmented public budgets, projects,
contracts, expenditure, timelines, and government records into information
citizens can understand, verify, and act on.

The citizen journey is:

Discover → Understand → Verify → Investigate → Act → Follow up

This platform is not a generic data warehouse or a list of admin CRUD screens.
It exists to help residents answer a practical question:

> What is happening with public money and public projects in my area, and what
> evidence supports that understanding?

---

## Full product scope

| Area | What it covers | Priority |
| --- | --- | --- |
| 1. Geography | County → sub-county → ward | Core |
| 2. Projects | Browse, search, filter, project profiles | Core |
| 3. Public Finance | Allocation, expenditure, budget periods | Core |
| 4. Procurement | Contractors, contracts, tenders | Core |
| 5. Evidence & Provenance | Sources, documents, claims, verification dates | Core |
| 6. Intelligence | Discrepancies, anomalies, comparisons, data gaps | Core |
| 7. Citizen Reports | Reporting issues and tracking status | Core |
| 8. Institutional Response | Agencies, reporting channels, responses | Important |
| 9. AI Intelligence Layer | Explain, answer questions, summarize evidence | Important |
| 10. Civic Intelligence Dashboard | Unified citizen-facing experience | Core |

The framework is deliberately shaped around the public-interest journey rather
than around database tables or isolated feature buckets.

---

## Product experience

A citizen should be able to:

1. Choose a location.
2. See projects in that area.
3. Open a project.
4. Understand money, contractor, and progress.
5. See evidence and provenance behind the facts.
6. See system-generated review signals.
7. Ask an AI question grounded in the evidence.
8. Verify information and understand uncertainty.
9. Report an issue.
10. Track the report and institutional response.

This is the product-level objective that all stories should support.

---

## Core principles

### 1. Distinguish fact types explicitly

The system must distinguish between:

- official source information
- derived calculations
- system-generated intelligence
- verification results
- citizen-submitted information
- institutional responses

A derived number, AI summary, or review signal must never be presented as an
authoritative fact.

### 2. Keep provenance attached to material facts

Every material factual claim should be traceable to a source document, source
URL, or other provenance record. The platform should allow a person to answer:

> Where did this number or statement come from?

### 3. Start with explainable intelligence

Start with deterministic, explainable rules instead of opaque model scoring.
Examples:

- expenditure greater than allocation
- contract value greater than allocation
- expenditure greater than contract value
- reported progress significantly exceeding expenditure ratio
- project past expected completion date
- missing required evidence
- incomplete verification

Each anomaly must include:

- rule used
- underlying values
- explanation
- source references
- severity/category if applicable
- clear indication that it is a review signal, not a factual accusation

### 4. AI is explanatory, not authoritative

AI features must be grounded in project records and their provenance. AI should
be able to explain projects, answer factual questions, summarize evidence, and
identify missing information. If information is incomplete, the AI must say so.

AI must not invent facts or automatically determine wrongdoing.

---

## Architecture rules

### Backend

- FastAPI
- Python 3.12+
- Pydantic v2
- SQLModel
- PostgreSQL / PostGIS
- Redis
- RabbitMQ / Celery for asynchronous work where required
- Alembic
- pytest
- Ruff
- mypy
- Docker Compose

### Architectural flow

Routes must remain thin:

API route → service → repository → database

Do not put business logic in routes. Do not bypass SQLModel persistence patterns.
Use asynchronous database and I/O operations wherever appropriate.

### Frontend

- Next.js
- React
- TypeScript

The frontend should align with the citizen journey: landing, explorer, project
page, evidence display, anomaly explanation, and report flow.

---

## Scope control

Do not add unrelated features.

Do not introduce authentication, payments, messaging, social networking, or a
mobile app unless a story explicitly requires them. Do not add abstractions for
possible future use. Prefer the simplest architecture that supports the current
product requirement.

---

## Story generation rules

When generating implementation stories, use this sequence:

1. Foundation
2. Database and migrations
3. Seed and demo data
4. Geography
5. Project explorer
6. Project detail
7. Finance
8. Procurement
9. Evidence and provenance
10. Verification
11. Intelligence and anomalies
12. Citizen reports
13. Institutional response
14. AI intelligence
15. Frontend integration
16. End-to-end hardening

Each story must be small enough for a focused implementation cycle but large
enough to deliver a coherent user outcome.

Every story must include:

- Story ID
- Goal
- User/persona
- Context
- Requirements
- Acceptance criteria
- Data requirements
- API requirements where applicable
- UI requirements where applicable
- Provenance requirements
- Tests
- Dependencies
- Non-goals
- Definition of done

Acceptance criteria must be observable and testable. Avoid vague wording such as
"works correctly" or "good UX" without measurable behavior.

---

## Master prompt for AI story generation

We are building the Citizen Intelligence Layer for public spending.

The product goal is:

"Turn public budgets, projects, contracts, expenditure and government records
into information citizens can understand, verify and act on."

The complete citizen journey is:

DISCOVER → UNDERSTAND → VERIFY → INVESTIGATE → ACT → FOLLOW UP

## Product scope

The system consists of these product areas:

1. Geography
2. Projects
3. Public Finance
4. Procurement and Contracts
5. Evidence and Provenance
6. Verification
7. Intelligence and Anomaly Detection
8. Citizen Reports
9. Institutional Response
10. AI Intelligence Layer
11. Citizen-facing Frontend
12. Administration and ingestion needed to support the above

## Core product principle

The platform must distinguish between:

- official source information
- derived calculations
- system-generated intelligence
- verification results
- citizen-submitted information
- institutional responses

Never present a derived result or AI interpretation as an official fact.

AI must explain evidence and identify review signals. AI must not determine
that wrongdoing occurred, automatically verify claims, or make unsupported
accusations.

Every material factual claim should be traceable to a source document, source
URL, or other provenance record.

## Architecture rules

- Keep API routes thin.
- Route → service → repository → database.
- Use SQLModel and Pydantic.
- Use PostgreSQL, Redis, Celery where required.
- Keep provenance with material facts.
- Use asynchronous database and I/O patterns.
- Keep the implementation story-driven and incremental.

## Story generation rules

- Create implementation stories in dependency order.
- Do not generate stories for database entities alone.
- Prioritize complete workflows over isolated CRUD.
- Every story must include user value and acceptance criteria.
- Do not broaden scope without a corresponding story.
- The objective is to create a coherent roadmap that another agent can execute
  story by story without inventing architecture or expanding scope.

## Output

First produce the complete story map grouped by epic. Then produce the actual
story files for the next implementation milestone. Do not implement anything yet.

---

## Milestone structure

### Milestone 1: Foundation and data

- foundation
- database migrations
- demo data
- geography

### Milestone 2: Project explorer

- browse projects
- filter and search
- project detail
- timeline

### Milestone 3: Money and contracts

- budget
- expenditure
- contractor and contract
- financial comparison

### Milestone 4: Trust and verification

- sources
- claims
- provenance
- verification state
- corrections

### Milestone 5: Intelligence

- anomalies
- data gaps
- discrepancy explanation
- comparisons

### Milestone 6: Civic action

- citizen reports
- status tracking
- institution channels
- response flow

### Milestone 7: AI

- project explanation
- evidence-grounded Q&A
- anomaly explanations
- project comparison

### Milestone 8: Frontend + integration

- dashboard
- explorer UI
- project page UI
- evidence UI
- AI UI

### Milestone 9: Demo hardening

- seed quality
- empty states
- error states
- loading states
- Docker validation

---

## Definition of done for the roadmap

- The product is anchored in the citizen journey.
- Each story matches a plausible user need.
- Provenance is required for material facts.
- Derived or AI-generated outputs are clearly labelled as such.
- Stories are sequenced in dependency order.
- The system supports an end-to-end demo without requiring massive speculative
  architecture.
