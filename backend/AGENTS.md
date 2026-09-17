# Backend instructions

Follow the repository-level working agreement first. The backend uses the
feature-module convention already established by `sfnotifications`:

```text
app/
├── api/v1/modules/<domain>/  routes, schemas, repository, service
├── core/                    configuration, database, security, logging
├── models/                  SQLModel tables
└── tasks/                   Celery application and task entry points
```

- Keep every database operation asynchronous through `AsyncSession` and
  `asyncpg`.
- Register every SQLModel table from `app.models` so Alembic sees it.
- Create and review an Alembic migration for every persistence-model change.
- Keep worker task functions small; task orchestration should call services.
- Do not add domain endpoints, models, or integrations without the matching
  root specification and story.
