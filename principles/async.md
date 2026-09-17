# Async principle

HTTP handlers, database access, and external network clients must be
asynchronous. Never perform blocking I/O in an async request path. Queue
expensive, retryable, or long-running work to Celery.
