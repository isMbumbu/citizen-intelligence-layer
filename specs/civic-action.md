# Civic-action specification

Citizens can submit a report for an existing project with a category,
description, and optional contact information. New reports are always created
with `SUBMITTED` status and a timezone-aware submission time. Contact
information is optional, retained only on the report, and never written to
request logs.

Authentication, attachments, reporting channels, moderation, notification, and
case-management workflows are outside this five-day vertical slice.
