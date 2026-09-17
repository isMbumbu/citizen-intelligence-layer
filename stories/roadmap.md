# Story roadmap

## Purpose

This roadmap defines the product-level story map for the Citizen Intelligence
Layer. It keeps delivery anchored to the citizen journey and prevents scope
expansion into unrelated infrastructure or speculative features.

---

## Epic 1: Foundation

### FND-001: Application foundation
Goal: Establish the backend application structure.

User: developer / operator

Acceptance criteria:
- FastAPI application starts via Docker Compose.
- Configuration is environment-based.
- PostgreSQL and Redis connections work asynchronously.
- Health and readiness endpoints report correct dependency state.
- Logging is configured.
- Ruff, mypy, and pytest can run inside the project environment.

### FND-002: Database migration system
Goal: Ensure the schema is safely versioned.

Acceptance criteria:
- Alembic is configured.
- Initial schema migration can be applied and rerun safely.
- Docker startup can initialize a fresh database without manual steps.
- Database schema matches SQLModel persistence models.

### FND-003: Demo data seeding
Goal: Create a realistic public-sector demo dataset.

Acceptance criteria:
- Seed is deterministic and idempotent.
- Demo data includes counties, wards, projects, budgets, contractors, and claim
  records.
- At least one review signal is created from sourced values.

---

## Epic 2: Geography

### GEO-001: Geography hierarchy
Goal: Represent county, sub-county, and ward relationships.

Acceptance criteria:
- Geography records have stable identifiers.
- Projects belong to a ward.
- Relationships are constrained and queryable.
- API responses expose the location structure without leaking persistence internals.

### GEO-002: Geographic project discovery
Goal: Allow residents to discover projects in a selected area.

Acceptance criteria:
- A user can select county, sub-county, and ward.
- API returns only projects for the selected geography.
- Empty results produce a stable empty-state response.

---

## Epic 3: Project Explorer

### PROJ-001: Browse projects
Goal: Let a resident browse and search public projects.

Acceptance criteria:
- `GET /api/v1/projects` supports pagination.
- It filters by county, ward, project type, status, and text search.
- Sorting and filtering remain deterministic.

### PROJ-002: Project detail
Goal: Expose the project summary page.

Acceptance criteria:
- The project detail presents location, status, budget, expenditure, contractor,
  progress, timeline, verification state, and evidence references.
- Material facts are exposed through scoped API contracts rather than raw model
  objects.
- Derived summary values are clearly separated from sourced fact values.

### PROJ-003: Project timeline
Goal: Show the project lifecycle and milestones.

Acceptance criteria:
- The project timeline shows key phases and dates.
- Each milestone has traceable provenance.
- Missing milestone data is handled without misrepresenting the project.

---

## Epic 4: Public Finance

### FIN-001: Project budget
Goal: Represent per-year budget allocations.

Acceptance criteria:
- Budget rows include year, allocation, and source references.
- Budget values are returned as structured summary data.
- Source document references are attached to material financial values.

### FIN-002: Project expenditure
Goal: Record project spending and sources.

Acceptance criteria:
- Spending rows include date, amount, category, and source.
- Totals are derived from sourced entries.
- Expenditure cannot be represented without a supporting value record.

### FIN-003: Financial comparison
Goal: Display budget-to-spend relationships clearly.

Acceptance criteria:
- Derived values such as utilization and variance are presented as derived
  numbers.
- A derived value is never labelled as an official source fact.
- Comparison logic is deterministic and explanation-friendly.

---

## Epic 5: Procurement

### PROC-001: Contractor information
Goal: Show contractor and contract metadata for each project.

Acceptance criteria:
- Contractor records include company name, associated project references, and
  source documents where needed.
- The API exposes data in a project-scoped contract.

### PROC-002: Contract information
Goal: Attach formal contract details to a project.

Acceptance criteria:
- Contract value, dates, and status are queryable.
- Contract records are traceable to source documents.
- The contract record is clearly separated from the project summary.

### PROC-003: Procurement relationship mapping
Goal: Connect a project to contract and contractor records.

Acceptance criteria:
- Relationships are explicit and testable.
- The system allows the citizen to move from project → contract → contractor.

---

## Epic 6: Evidence and provenance

### EVD-001: Source records
Goal: Capture source documents and metadata.

Acceptance criteria:
- Source records include publisher, publication date, type, and URL or reference.
- Source records are reusable across multiple claims.

### EVD-002: Claim model
Goal: Represent factual statements and their evidence.

Acceptance criteria:
- Claims are structured, traceable, and versioned where needed.
- Each material fact belongs to a project or related domain record.
- The API can resolve claim-to-source relationships.

### EVD-003: Evidence display
Goal: Show the evidence behind project facts in the UI.

Acceptance criteria:
- A citizen can see the source behind any material number or statement.
- Evidence-specific UI states exist for missing or disputed sources.

---

## Epic 7: Verification

### VER-001: Verification state
Goal: Represent trust states for project facts.

Acceptance criteria:
- Verification states support UNVERIFIED, PARTIALLY_VERIFIED, VERIFIED,
  DISPUTED, and similar values.
- States are explicit and auditable.
- Verification is separate from intelligence and AI output.

### VER-002: Verification events
Goal: Record who reviewed what, when, and with what evidence.

Acceptance criteria:
- Verification events store actor, date, evidence, and result.
- The system can explain why a fact is verified or disputed.

### VER-003: Corrections and appeals
Goal: Allow corrections to material claims.

Acceptance criteria:
- Correction or review requests are persisted.
- Original claim information remains available for auditability.

---

## Epic 8: Intelligence and anomaly detection

### INT-001: Deterministic anomaly detection
Goal: Surface explainable review signals.

Acceptance criteria:
- Rules detect mismatches between progress, spend, and allocation.
- The output is labelled as a review signal, not as a verified accusation.
- Explanations reference the underlying values and evidence.

### INT-002: Financial anomalies
Goal: Surface spend and allocation inconsistencies.

Acceptance criteria:
- The model identifies when spending exceeds allocation or contract value.
- The issue is explained in plain language.

### INT-003: Timeline anomalies
Goal: Detect delayed or mismatched project milestones.

Acceptance criteria:
- Past-due and stalled milestones are flagged only as review indicators.
- Explanations reference dates and evidence.

### INT-004: Data gaps
Goal: Identify missing evidence and missing verification.

Acceptance criteria:
- The system identifies absent or incomplete data needed for confidence.
- The UI clearly marks the problem as missing information rather than failure.

---

## Epic 9: Taxonomy and community contribution

### TAX-001: Project category reference data
Goal: Replace the narrow project-type enum with a Kenya-aware category model.

Acceptance criteria:
- The project taxonomy supports multiple parent categories and subtypes.
- The model supports county and national public-project records.
- Category data is managed as reference data rather than hard-coded application logic.
- The taxonomy can support filtering and future analytics without redeployment.

### TAX-002: Project category filtering and county/national support
Goal: Expose category and subtype filtering in the project explorer.

Acceptance criteria:
- `GET /api/v1/projects` accepts category and subtype filters.
- The project list returns county and national project records in the same browse flow.
- Category metadata is visible on each project record and in the explorer UI.

### CIV-001: Citizen comment model
Goal: Allow citizens to comment on public projects without turning comments into official facts.

Acceptance criteria:
- Comments are stored with project association, author metadata, status, and moderation state.
- Each comment is clearly labelled as citizen-submitted information.
- Parent-child thread support is available if replies are enabled.
- Comment reporting is supported for abuse and policy violations.

### CIV-002: Create and view project comments
Goal: Let citizens add and read project comments safely.

Acceptance criteria:
- The API supports comment creation and retrieval for a project.
- Comment data includes lifecycle and visibility metadata.
- Comments are rendered with trust labels rather than as official project facts.

### EVD-001: Evidence storage model
Goal: Support evidence attachments for comments and citizen reports.

Acceptance criteria:
- Evidence metadata is stored separately from the actual file.
- Evidence remains distinct from official source documents.
- The model preserves ownership, checksum, processing state, and visibility.
- Image and PDF evidence can be stored and retrieved later for verification work.

### EVD-002: Secure evidence upload
Goal: Accept safe image and PDF uploads from citizens.

Acceptance criteria:
- Only supported file types are accepted.
- Malformed or oversized uploads are rejected.
- Files are stored with generated keys and integrity metadata.
- The system never executes uploaded content or accepts a user-controlled path.

### MOD-001: Comment and evidence moderation
Goal: Apply moderation to citizen content without confusing unverified content with falsehood.

Acceptance criteria:
- Moderation states are persisted for comments and evidence.
- A moderator can flag or hide content due to spam, harassment, personal data, malicious content, or inappropriate behavior.
- Hidden or removed content retains an audit trail and provenance context.
- Unverified content is labelled as such and never equated with falsehood.

### RAT-001: Rate limiting and abuse protection
Goal: Reduce abuse for comments, reports, uploads, and expensive operations.

Acceptance criteria:
- Comments, reports, uploads, and expensive request paths are rate-limited.
- Redis-backed enforcement is used where appropriate.
- The limit values are configurable.
- The API returns a clear rate-limit response.
- Tests cover both normal and over-limit behavior.

### STG-001: Secure evidence retrieval
Goal: Provide safe retrieval for uploaded images and PDFs.

Acceptance criteria:
- Retrieval is authorization-aware and visibility-aware.
- Generated storage keys are used for all file access.
- Path traversal and direct object manipulation attempts are rejected.
- Pending or private files are not publicly exposed.
- Correct content-disposition and content-type headers are applied.

---

## Epic 10: Citizen reports

### CIVIC-001: Issue report submission
Goal: Allow a resident to report a problem for a project.

Acceptance criteria:
- The report includes project reference, issue type, description, and optional
  evidence.
- Invalid reports return clear validation errors.
- Contact information is not logged or exposed unnecessarily.

### CIVIC-002: Report status tracking
Goal: Show a report through its lifecycle.

Acceptance criteria:
- Reports move through states such as SUBMITTED, UNDER_REVIEW, REFERRED,
  RESPONDED, RESOLVED, and CLOSED.
- Status transitions are auditable.

### CIVIC-003: Reporting channels
Goal: Show where the report should be sent.

Acceptance criteria:
- Relevant authorities or offices are returned with a report channel.
- Channels are linked to the correct issue type and location.

---

## Epic 11: Institutional response

### RESP-001: Institution model
Goal: Represent public institutions and agencies.

Acceptance criteria:
- Institutions have stable identifiers and typed roles.
- Reports can be assigned or referred to an institution.

### RESP-002: Response flow
Goal: Connect citizen reports to institution responses.

Acceptance criteria:
- Institution responses are stored and shown alongside issues.
- The system preserves the original citizen report and evidence.

### RESP-003: Right of reply
Goal: Allow institutions to contest or clarify information.

Acceptance criteria:
- A response is kept separate from the original claim and can be audited.
- The public can compare the original issue against the institution response.

---

## Epic 12: AI intelligence layer

### AI-001: Project explanation
Goal: Explain what a project is and why it matters.

Acceptance criteria:
- AI replies are based on project records and provenance.
- The system clearly distinguishes fact from explanation.

### AI-002: Evidence-grounded Q&A
Goal: Answer project questions using sourced records.

Acceptance criteria:
- The answer cites source records or structured values.
- Missing evidence leads to a transparent uncertainty response.

### AI-003: Compare projects
Goal: Compare projects by metrics and anomalies.

Acceptance criteria:
- Projects can be compared using budget, spending, contractor, status, and
  verification state.
- Comparison output references the relevant evidence.

### AI-004: Explain anomalies
Goal: Turn review indicators into natural-language explanations.

Acceptance criteria:
- Explanations reference the rule, the values, and the evidence.
- No unsupported accusation is made.

---

## Epic 13: Frontend integration

### FE-001: Landing page
Goal: Present the project concept clearly.

Acceptance criteria:
- The landing page motivates the platform around public project understanding.
- The primary CTA guides users to project exploration.

### FE-002: Project explorer UI
Goal: Deliver filterable project discovery.

Acceptance criteria:
- Users can filter by county, ward, status, and search text.
- The UI renders empty and loading states cleanly.

### FE-003: Project page UI
Goal: Show the core project screen.

Acceptance criteria:
- The project summary includes budget, expenditure, contractor, timeline, and
  evidence references.
- System review flags are presented clearly and contextually.

### FE-004: Report flow UI
Goal: Let residents submit reports and observe status.

Acceptance criteria:
- Reports can be created with validation.
- Status updates are visible in a user-friendly form.

---

## Recommended sequencing

The first implementation milestone should be:

1. Foundation
2. Database migrations
3. Geography
4. Project explorer
5. Seed/demo data

This gives the team a real product slice that can be demoed in a short time while
keeping the architecture aligned to the full platform.

---

## Definition of done for the roadmap

- Stories are product-oriented rather than database-oriented.
- Each story has a clear user outcome.
- Provenance is attached to material facts.
- Derived or AI-generated metrics are clearly labelled.
- The stories are sequenced in dependency order.
- The roadmap can be implemented incrementally without arbitrary scope expansion.
