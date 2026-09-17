# Citizen evidence, moderation, and security specification

## Purpose

This specification extends the existing Citizen Intelligence Layer architecture by
adding a structured, trusted evidence layer for citizen participation, including
citizen comments, uploaded evidence, moderation, abuse prevention, and secure
file handling.

It is designed to fit the current repository architecture:

- API routes remain thin
- business logic stays in services and repositories
- provenance remains attached to material facts
- official records, derived values, citizen-submitted content, and review signals
  remain distinct

This specification intentionally does not rebuild the foundation or change the
project’s existing product principles. It expands them in a way that matches the
current architecture and the larger citizen-journey model.

---

## 1. Product objective

The platform should allow citizens to contribute useful context to public-works
information without letting that input be mistaken for official fact.

The platform must support the following distinction:

- official record
- derived calculation
- system-generated intelligence
- citizen-submitted comment
- citizen-submitted evidence
- institutional response
- verification record
- moderation action

A citizen comment is not a verified fact. A citizen photo is not a proof of
public-sector accuracy. A derived anomaly is not a finding of wrongdoing.

This distinction is essential to trust and must be visible throughout the UI and
API.

---

## 2. Kenyan public-project taxonomy

### 2.1 Goals

The project type model must support realistic Kenyan public-project examples
without forcing the application to redeploy for every new funding category.

The existing enum approach is too rigid for the planned project scope. The system
should use database-managed reference data, not a closed static enum, for the
long-term project taxonomy.

### 2.2 Recommended model

Use a hierarchical reference-data structure:

```
ProjectCategory
- id
- code
- name
- description
- parent_id (nullable)
- is_active
- created_at
- updated_at

ProjectSubtype
- id
- category_id
- code
- name
- description
- is_active
- created_at
- updated_at
```

This allows categories to evolve without requiring app redeployment and supports
future analytics and filtering.

### 2.3 Recommended category structure

#### Transport and roads
- roads and transport
  - road construction
  - road rehabilitation
  - bridge construction
  - pedestrian walkways
  - traffic infrastructure
  - public transport facilities

#### Water and sanitation
- water and sanitation
  - borehole
  - water pipeline
  - sewerage
  - water treatment
  - drainage
  - sanitation facility

#### Health
- health
  - health centre
  - hospital upgrade
  - maternity facility
  - dispensary
  - medical equipment

#### Education
- education
  - classroom construction
  - ECDE centre
  - school laboratory
  - library
  - school sanitation

#### Agriculture and food security
- agriculture and food security
  - irrigation scheme
  - storage facility
  - livestock facility
  - agribusiness infrastructure

#### Housing and urban development
- housing and urban development
  - affordable housing
  - settlement improvement
  - public housing facility

#### Energy and electrification
- energy and electrification
  - street lighting
  - electrification project
  - solar installation
  - energy kiosk

#### ICT and digital infrastructure
- ICT and digital infrastructure
  - public Wi-Fi
  - digital centre
  - connectivity backbone
  - e-government facilities

#### Environment and climate
- environment and climate
  - reforestation
  - climate resilience
  - flood control
  - environmental restoration

#### Markets and trade
- markets and trade
  - market construction
  - market rehabilitation
  - trade hub

#### Public administration
- public administration
  - office construction
  - government service centre
  - records facility

#### Security and emergency services
- security and emergency services
  - police post
  - fire station
  - emergency response facility

#### Sports, culture, and recreation
- sports, culture, and recreation
  - sports facility
  - cultural centre
  - community hall

#### Social protection and community development
- social protection and community development
  - community centre
  - support facility
  - youth and women facility

#### Drainage and flood management
- drainage and flood management
  - drainage channel
  - culvert works
  - flood control structure

#### Waste management
- waste management
  - solid waste transfer station
  - waste treatment facility
  - landfill or recycling facility

#### Public facilities
- public facilities
  - public toilet
  - community facility
  - public shelter

#### Other
- other
  - unspecified or cross-cutting project type

### 2.4 Fields for each project type

Each category or subtype should include:

- category code
- display name
- machine-readable identifier
- description
- examples of public use
- active flag
- parent category if nested

### 2.5 Scope note

This taxonomy should support both:

- county-level projects
- national government projects
- agency implementation projects

It should not assume that every project is a county project. The model should be
future-proof enough for analytics and filtering.

---

## 3. Citizen comments

Citizen comments are a distinct content type. They represent user-submitted
context, not official data.

### 3.1 Core model

```
ProjectComment
- id
- project_id
- author_id (nullable if anonymous is allowed)
- parent_comment_id (nullable)
- body
- status
- moderation_state
- created_at
- updated_at
- edited_at (nullable)
- visibility
- is_anonymous (nullable or boolean)
- source_context (optional)
```

### 3.2 Comment statuses

- DRAFT
- SUBMITTED
- VISIBLE
- FLAGGED
- HIDDEN
- REMOVED
- REVIEWED

### 3.3 Author identity model

The platform should support at least these actor classes:

- citizen
- reviewer
- administrator
- institutional user (optional future extension)

A citizen comment should preserve only the minimum identity needed for abuse
prevention, moderation, and security. It should not automatically assemble a
full profile or collect unnecessary personal information.

### 3.4 Anonymous comments

Anonymous commenting may be allowed only with safeguards. The system should not
assume anonymity is required or safe unless explicitly designed for it.

If anonymity is enabled:

- do not expose exact personal data in public responses
- keep moderation metadata separate from public display
- apply rate limiting and abuse detection
- require a minimum content quality gate if needed
- keep moderation actions auditable

### 3.5 Reporting comments

A user should be able to report a comment for reasons such as:

- spam
- harassment
- false or misleading content
- personal information
- inappropriate content
- suspected manipulation
- other

The reporting model should store:

- report_id
- comment_id
- reporter_id
- reason
- notes
- created_at
- status
- reviewed_by
- reviewed_at

### 3.6 Important rule

Citizen comments must never be treated as official facts. They should be labeled
in the UI and API as:

- citizen-submitted information
- not independently verified
- may require moderation or review

---

## 4. Citizen evidence

Citizen evidence refers to supporting artifacts submitted alongside comments,
reports, or verification requests.

### 4.1 Evidence model

```
EvidenceRecord
- id
- project_id (nullable)
- comment_id (nullable)
- report_id (nullable)
- uploader_id
- kind
- title
- description
- storage_key
- original_filename
- mime_type
- file_size_bytes
- checksum_sha256
- uploaded_at
- moderation_state
- processing_state
- visibility
- is_deleted
- deleted_at (nullable)
```

### 4.2 Evidence classes

Evidence must be separated into different classes for clarity:

- official document
- citizen-submitted evidence
- verification document
- institutional response document
- AI-derived extracted content (not primary evidence)

### 4.3 Hard requirement

Evidence metadata and the actual stored file must be kept separate.

The system must preserve:

- file hash
- storage key
- upload timestamp
- uploader
- processing history
- moderation state

This allows the project to detect tampering or file replacement.

---

## 5. File security and upload protection

All uploaded files are untrusted input. They must be treated as hostile until
validated.

### 5.1 Required protections

- allow-listed MIME types only
- extension validation
- file-size limits
- filename sanitization
- random storage keys instead of user-controlled paths
- malware scan integration where possible
- image validation
- PDF validation
- archive bomb and decompression protection
- metadata stripping where appropriate
- content-type verification from signatures
- duplicate detection by checksum
- checksum calculation before public exposure
- no execution permissions for uploaded content
- storage outside the application code path and outside the executable web root

### 5.2 Storage requirements

Uploaded content should be stored in an isolated storage layer such as object
storage or a dedicated secure upload bucket. The file path must never be derived
from client-supplied names or user-controlled values.

### 5.3 Download behavior

Protect downloads with controlled access, especially for private or moderated
uploads. Prefer signed, short-lived URLs over permanent public links.

### 5.4 Validation principles

- the filename is not trusted
- the client MIME type is not trusted
- extension is not trusted
- the system must inspect file signatures/content where practical

---

## 6. Image privacy and document handling

### 6.1 Image privacy

Images may contain personal data such as:

- faces
- vehicle number plates
- phone numbers
- addresses
- GPS coordinates
- timestamps
- other incidental identifying data

The system should strip unnecessary EXIF metadata before public display where
possible.

### 6.2 Trust boundaries

The system must preserve:

- upload timestamp
- checksum
- processing history
- moderation state

but it must not claim that an uploaded image is authentic proof of a specific
location or event merely because it exists.

### 6.3 OCR and PDF processing

PDFs and image documents may eventually feed into intelligence workflows, but
those extracted contents must be clearly labeled as derived or OCR-based.

Recommended pipeline:

```
Upload
→ validation
→ malware scan
→ secure storage
→ extraction/indexing
→ provenance association
```

The original document remains authoritative. Extracted text is not a verified
fact by itself.

OCR output must be clearly marked as OCR-derived and content must remain linked
back to the original document. OCR errors must be tolerated and represented as
possible extraction noise.

---

## 7. Provenance and evidence integrity

This specification extends the existing provenance model rather than replacing it.

There are distinct evidence classes:

1. official source
2. official document
3. platform-derived record
4. citizen-submitted evidence
5. citizen statement/comment
6. institutional response
7. verification record

These must not be collapsed into a single generic source type.

### 7.1 Display expectation

The UI should clearly distinguish between:

- official record
- derived value
- citizen-submitted evidence
- unverified public input
- moderated or hidden input

Example display patterns:

```
OFFICIAL RECORD
County Budget Estimates
Published June 2026
```

```
CITIZEN EVIDENCE
Photo submitted by a citizen
Uploaded September 17, 2026
Not independently verified
```

### 7.2 Integrity rules

- stored files must have checksums
- checksum mismatches must be detectable
- evidence attachments should remain linked to the original project/comment/report
- evidence should include provenance metadata
- content with moderation actions should retain an audit trail

---

## 8. Security model and threat mitigation

The system should operate under a pragmatic threat model designed for a
hackathon-grade product that handles untrusted user input.

### 8.1 Threats to address

- authentication abuse
- authorization bypass
- IDOR / BOLA
- SQL injection
- cross-site scripting
- request flooding
- credential stuffing
- file upload attacks
- malicious PDFs
- malicious images
- path traversal
- SSRF
- spam and comment abuse
- report abuse
- fake evidence
- impersonation
- data scraping
- secret leakage
- log injection
- unsafe AI prompts
- prompt injection via uploaded documents
- resource exhaustion
- oversize upload attacks

### 8.2 Mitigation model

Each threat should map to one or more mitigations, implemented in the relevant
layer:

- authentication and authorization layer
- API validation layer
- storage layer
- moderation layer
- audit logging layer
- AI integration layer

Security controls should be proportionate to the product and should not require
enterprise infrastructure unless genuinely necessary.

---

## 9. Authentication and authorization

If authentication is not yet implemented, the minimum necessary model should be
specified for:

- citizen
- reviewer/moderator
- administrator
- institutional user (future extension)

### 9.1 Authorization expectations

Citizens should not be able to:

- edit another person’s comment
- delete another person’s evidence
- change official project records
- modify financial totals
- alter verification results
- manipulate anomaly calculations

Reviewers and admins should have a separate permission model.

The project should avoid introducing a large RBAC system until it is clearly
needed, but every mutation must have a clear authorization boundary.

---

## 10. Moderation lifecycle

Moderation should focus on content safety and quality, not on imposing a truth
claim on all citizen content.

Recommended moderation lifecycle:

- PENDING
- VISIBLE
- FLAGGED
- HIDDEN
- REMOVED
- REVIEWED

### 10.1 Moderation goals

- detect abuse
- remove illegal or unsafe material
- remove spam or harassment
- protect personally identifying information
- prevent malicious uploads
- maintain a documented history of actions

### 10.2 Important principle

Unverified does not mean false.

The moderation system should protect the platform without forcing the platform to
judge the truth of every citizen statement.

---

## 11. Rate limiting and abuse controls

To avoid abuse, the platform should limit:

- comment creation
- report creation
- file uploads
- authentication attempts
- AI requests
- expensive search operations

Redis is already part of the architecture and is suitable for this purpose.

Limits must be configurable rather than deeply hard-coded across the application.

---

## 12. Audit logging

Sensitive actions should produce a minimal, auditable record.

Examples include:

- moderation action
- verification change
- evidence deletion
- project data correction
- institutional response
- administrative change

### 12.1 Audit log content

An audit record should include:

- actor
- action
- target
- timestamp
- relevant metadata
- outcome

### 12.2 Audit log exclusions

Audit records must not include:

- passwords
- authentication tokens
- raw sensitive personal data
- uploaded documents
- unnecessary request bodies

---

## 13. AI security and prompt injection controls

Citizen comments and uploaded documents are untrusted input. Their contents must
be treated as data, not instructions.

The AI system must not allow a document or comment to manipulate operating
instructions or expose internal system details.

### 13.1 Required protections

- treat uploaded text as untrusted content
- keep AI context scoped to approved application data
- do not expose internal system instructions or secrets to the model
- separate retrieved evidence from system configuration
- mark extracted OCR text as derived content
- avoid allowing AI to claim that unverified content is factual

This is especially important for PDFs, scanned docs, and OCR-derived output.

---

## 14. Data retention and lifecycle rules

The system should define lifecycle rules for:

- comments
- uploaded files
- reports
- moderation records
- audit logs
- deleted content

### 14.1 Retention principle

Do not permanently delete information that may be required for accountability,
unless there is a lawful reason and an explicit deletion policy.

When content is deleted from public view, a minimal audit record should remain to
show that moderation or deletion occurred.

---

## 15. API design

The API should remain intentionally scoped. It should only include endpoints needed
for actual product requirements.

Suggested resource structure:

- `GET /projects`
- `GET /projects/{project_id}`
- `GET /projects/{project_id}/comments`
- `POST /projects/{project_id}/comments`
- `GET /projects/{project_id}/evidence`
- `POST /projects/{project_id}/evidence`
- `GET /projects/{project_id}/reports`
- `POST /projects/{project_id}/reports`
- `GET /comments/{comment_id}`
- `POST /comments/{comment_id}/reports`
- `GET /evidence/{evidence_id}`
- `GET /reports/{report_id}`

This is a minimal foundation for evidence and comment support without creating a
large sprawling API surface.

---

## 16. Frontend experience requirements

The project page should eventually display:

- project information
- financial information
- contractor information
- progress and timeline
- verification state
- official evidence
- review signals
- citizen comments
- submitted evidence
- report issue action
- AI question interface

The UI must clearly distinguish between:

- official
- derived
- citizen-submitted
- verified
- unverified
- review signal

A resident should never need to guess where a fact came from.

---

## 17. Story-generation requirement

After this specification is approved, generate implementation stories in
dependency order. Suggested story families include:

- taxonomy and project classification
- citizen comments and moderation
- evidence storage and secure uploads
- privacy and document processing
- AI and prompt-injection protection
- evidence-aware frontend flows

Suggested stories:

### Taxonomy
- TAX-001: Project category reference data
- TAX-002: Project category/subtype migration
- TAX-003: Expanded project filtering

### Security
- SEC-001: File upload security policy
- SEC-002: Authorization boundaries
- SEC-003: Rate limiting and abuse protection
- SEC-004: Audit logging

### Citizen interaction
- CIV-001: Citizen comment model
- CIV-002: Create project comment
- CIV-003: View project comments
- CIV-004: Comment moderation
- CIV-005: Comment reporting

### Evidence
- EVD-001: Evidence storage abstraction
- EVD-002: Secure file upload
- EVD-003: Evidence metadata and checksum
- EVD-004: Evidence attached to comments
- EVD-005: Evidence attached to reports
- EVD-006: Evidence processing
- EVD-007: Secure evidence retrieval

### Privacy and AI
- PRI-001: Privacy protections for uploaded media
- AI-001: Evidence-aware document extraction
- AI-002: Citizen evidence in AI context
- AI-003: Prompt-injection protection for untrusted content

### Frontend
- FE-001: Project category navigation
- FE-002: Project comments UI
- FE-003: Evidence upload UI
- FE-004: Evidence viewer
- FE-005: Moderation/reporting UI
- FE-006: Trust/provenance indicators

All stories must include:

- story ID
- goal
- user/persona
- context
- requirements
- acceptance criteria
- data requirements
- API requirements
- UI requirements where relevant
- security requirements
- provenance requirements
- tests
- dependencies
- non-goals
- definition of done

Acceptance criteria must be observable and testable.

---

## 18. Final scope rule

Do not implement these features yet. This task is only to create the precise
product specification before implementation begins.

The purpose is to give future coding agents a secure, coherent implementation
plan that fits the current project architecture without blowing up the product
scope.

The following is the core product principle that should guide all future work:

Comment ≠ evidence ≠ report ≠ official source.

A comment is user context. Evidence is a stored artifact with provenance. A
report is a structured civic concern. An official source is an authority-backed
record. These items are related but not equivalent, and the system should show
that distinction clearly.
