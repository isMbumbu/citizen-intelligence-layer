# Citizen Intelligence Layer frontend

Next.js 16 (App Router) with React 19, TypeScript, and Tailwind CSS 4. It
provides the public CIVICACT experience and consumes the FastAPI backend in
`backend/`.

## Public experience

The frontend helps citizens explore public projects, understand sources and
verification, submit civic reports, and follow reports submitted from their
browser. It separates public project records, verification, review signals,
and citizen-submitted material in both wording and visual treatment.

Key routes include:

- `/projects` — searchable, URL-synchronised project catalogue.
- `/projects/[id]` — project trust summary, finance, provenance, evidence,
  reports, and comments.
- `/reports` — public reports and browser-local report tracking.
- `/categories` — project categories and subtypes.
- `/evidence` — evidence and source guidance.
- `/how-it-works` and `/community-safety` — public trust and safety guidance.

## Getting started

1. (Optional, for local dev) copy the template: `cp .env.example .env.local`.
2. Run the development server:

```bash
npm run dev
```

3. Open <http://localhost:3000>.

The home page shows a live API health indicator and public-project count, so
it doubles as a quick check that the frontend proxy and backend are connected.

## Docker

The root Compose stack serves the production-style frontend image at
<http://localhost:3000>:

```bash
docker compose up --build
```

The image uses Next.js standalone output, runs as an unprivileged user, and
contains only traced runtime files, public assets, and static build assets.
Compose supplies `http://api:8000` as the internal API address; the browser
still uses the same-origin `/api/v1` prefix, so no API CORS configuration is
needed. It intentionally does not receive the root backend `.env` file.

For quick UI iteration on Docker Desktop, use `npm run dev` on the host instead
of a bind-mounted container. Next.js recommends this because host filesystem
mounts can make Fast Refresh slow or unreliable on macOS and Windows.

## Backend request flow

The backend API is versioned (`/api/v1`) and runs on port 8000. Two routes are
used to reach it, both handled by `lib/api.ts`:

- **Server components** fetch `API_BASE_URL` (default `http://localhost:8000`)
  directly.
- **Client components** fetch the same-origin `NEXT_PUBLIC_API_URL` prefix
  (default `/api/v1`), which `next.config.ts` rewrites to the backend.
- The health indicator uses same-origin `/api/health`, which rewrites to the
  backend’s `/health` endpoint.

No CORS configuration is needed for client-side calls because the browser never
talks to the backend origin.

## Commands

```bash
npm run dev     # development server
npm run lint    # eslint
npm run build   # production build
npm run start   # serve the production build
```

## Conventions

- Keep `lib/api.ts` as the single typed API boundary. Reusable loading, retry,
  and stale-response behavior lives in `lib/use-api-query.ts`.
- Keep filter state in the URL so search results can be shared and revisited.
- Use `"use client"` for interactive islands such as filters, forms, theme
  choice, and report tracking; keep purely presentational pieces small.
- Keep UI types in `lib/` and mirror backend Pydantic contracts. As domain
  endpoints land, generate types from the OpenAPI schema
  (`openapi-typescript` against `/openapi.json`) instead of hand-writing them.
- Follow the root `AGENTS.md` working agreement: no business features without a
  matching specification and story.

Note: running `next dev` maintains the `AGENTS.md` file next to this README
with Next.js 16 agent instructions.
