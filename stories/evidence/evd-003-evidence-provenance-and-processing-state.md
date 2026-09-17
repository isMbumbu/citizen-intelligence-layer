# EVD-003: Evidence provenance and processing state

## Goal

Track the lifecycle of citizen-submitted evidence so the system can distinguish
raw uploaded files from processed or derived artifacts without treating either as
an official record.

## User

Citizen / reviewer / moderator / intelligence operator

## Context

The project needs stronger provenance around citizen evidence so it can later
support verification work and AI contexts without overclaiming. Uploaded files,
OCR extracts, and indexing results should remain clearly labelled as derived or
unverified material.

## Requirements

- Evidence records include upload, visibility, and processing state.
- Processing states distinguish raw upload, validation passed, extracted, indexed,
  failed, or hidden.
- Derived OCR or other extraction output remains clearly marked as derived.
- Evidence remains separate from official source documents.
- The system supports future intelligence integration without collapsing evidence
  into official records.

## Acceptance criteria

### AC1: Processing lifecycle is represented
Given an evidence file is uploaded and processed
When its state changes
Then the record reflects the correct processing stage.

### AC2: Derived output is labelled as derived
Given extracted text or OCR output is created from a citizen file
When it is stored or queried
Then it is attached as derived content and not treated as an official source.

### AC3: Original file remains authoritative
Given processed output exists
When the evidence record is reviewed
Then the original file and its metadata remain traceable as the source artifact.

## Data requirements

- evidence processing states
- audit of extraction or indexing steps
- derived-output metadata
- original file reference

## API requirements

- `GET /evidence/{evidence_id}` returns processing metadata
- `GET /evidence/{evidence_id}/processing` or an equivalent status endpoint

## UI requirements

- display evidence status, provenance, and raw-vs-derived labels
- allow viewing of original file and extracted text separately

## Security requirements

- OCR or extraction content must not be treated as system instructions
- extracted content remains in an untrusted-data boundary

## Provenance requirements

- preserve upload timestamp, uploader, checksum, and derived-output lineage
- maintain source-of-source traceability

## Tests

- evidence lifecycle advances correctly
- derived extracted text remains labelled as derived
- original file remains authoritative even with extracted output

## Dependencies

- EVD-001
- EVD-002
- MOD-001

## Non-goals

- not a full document intelligence pipeline yet
- not a full AI evidence extraction service

## Definition of done

- evidence lifecycle and processing states are represented and queryable
- derived artifacts stay clearly separate from official source documents
- the system is prepared for later verification and intelligence integration
