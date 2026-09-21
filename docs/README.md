<img width="1435" height="762" alt="Screenshot 2026-09-21 at 23 45 38" src="https://github.com/user-attachments/assets/f6d1194b-15c5-4abb-86d6-4abc719b5b9a" />

# Citizen Intelligence Layer

A citizen-first platform for understanding public projects, budgets, expenditure,
contracts, evidence, and civic action.

## Frontend

The frontend is a Next.js application that presents public project information
and evidence in a citizen-friendly interface.

Run the frontend locally:

```bash
cd frontend
npm run dev
```

Open <http://localhost:3000>.
<img width="1439" height="698" alt="Screenshot 2026-09-21 at 23 46 57" src="https://github.com/user-attachments/assets/baa98145-6bcc-465a-b716-7fb29395d7dc" />

<img width="1423" height="749" alt="Screenshot 2026-09-21 at 23 47 20" src="https://github.com/user-attachments/assets/8be9364b-3f51-4699-8068-7f44b8e3bbd4" />

<img width="427" height="556" alt="Screenshot 2026-09-21 at 23 47 40" src="https://github.com/user-attachments/assets/7fd761f1-0211-4d84-9104-a661417065e5" />


See the complete frontend guide in [frontend/README.md](../frontend/README.md).

## Backend

<img width="1431" height="768" alt="Screenshot 2026-09-21 at 23 48 11" src="https://github.com/user-attachments/assets/556cff39-310b-403d-8fea-786730302020" />


The backend is an asynchronous FastAPI service with SQLModel persistence,
PostgreSQL, Redis, Celery, RabbitMQ, and Alembic migrations.

The API exposes project records with:

- Location and project details
- Allocated, contracted, and spent amounts
- Contractor and progress information
- Verification status
- Source and claim provenance
- Evidence-grounded review flags
- Citizen issue reports

Run the complete stack:

```bash
docker compose up --build
```

Useful endpoints:

- Frontend: <http://localhost:3000>
- API documentation: <http://localhost:8000/docs>
- API health: <http://localhost:8000/health>
- Project list: <http://localhost:8000/api/v1/projects>

See the complete backend guide in [backend/README.md](../backend/README.md).

## Adding screenshots

Store frontend screenshots and backend/API screenshots in this directory or in
`frontend/public/`, then reference them with repository-relative Markdown:

```markdown
![Project explorer](../frontend/public/project-explorer.png)
![API documentation](./api-docs.png)
```

Keep image files small and use descriptive names. Screenshots should not include
real credentials, personal information, or private API data.

## Evidence principle

Every material claim should remain traceable to its source record. Derived
review flags are signals for verification, not accusations, and AI explanations
must never replace the underlying evidence.
