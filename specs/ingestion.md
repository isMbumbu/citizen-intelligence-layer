# Ingestion specification

Ingestion supports government APIs, CSV, Excel, PDF, web pages, reports,
contracts, and budget documents. Each pipeline follows retrieve → store raw
artifact → extract → parse → normalize → validate → persist → create
provenance. Long-running stages run as Celery tasks.
