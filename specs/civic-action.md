# Civic-action specification

Citizens can submit a report for an existing project with a category,
description, and optional contact information. New reports are always created
with `SUBMITTED` status and a timezone-aware submission time. Contact
information is optional, retained only on the report, and never written to
request logs.

Authentication, attachments, reporting channels, moderation, notification, and
case-management workflows are outside this five-day vertical slice.

## Browsing reports

Anyone can browse submitted reports, newest first, optionally filtered by
project, status, or category. List entries show only the report identifier,
project, category, status, and submission time; descriptions and contact
information are never included in the list. Each report's own status page
continues to show its description as before, so listing reports makes those
pages discoverable.
