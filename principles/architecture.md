# Architecture principle

Organize backend code by feature module, with thin API routes that delegate to
services and repositories. Keep cross-cutting infrastructure in `app/core` and
background work in Celery tasks. Choose the simplest structure that makes a
capability testable and keeps domain rules out of transport code.
