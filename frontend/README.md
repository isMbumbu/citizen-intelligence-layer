# Citizen Intelligence Layer frontend

Next.js 16 (App Router) with React 19, TypeScript, and Tailwind CSS 4. It
consumes the FastAPI backend in `backend/`.

## Getting started

1. (Optional, for local dev) copy the template: `cp .env.example .env.local`.
2. Run the development server:

```bash
npm run dev
```

3. Open <http://localhost:3000>.

The home page renders the backend health status, so it doubles as a check that
the API wiring works.

## Backend request flow

The backend API is versioned (`/api/v1`) and runs on port 8000. Two routes are
used to reach it, both handled by `lib/api.ts`:

- **Server components** fetch `API_BASE_URL` (default `http://localhost:8000`)
  directly.
- **Client components** fetch the same-origin `NEXT_PUBLIC_API_URL` prefix
  (default `/api/v1`), which `next.config.ts` rewrites to the backend.

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

- Server-first: fetch data in Server Components and pass props down. Use
  `"use client"` only for interactive islands (maps, filters, citations).
- Keep UI types in `lib/` and mirror backend Pydantic contracts. As domain
  endpoints land, generate types from the OpenAPI schema
  (`openapi-typescript` against `/openapi.json`) instead of hand-writing them.
- Follow the root `AGENTS.md` working agreement: no business features without a
  matching specification and story.

Note: running `next dev` maintains the `AGENTS.md` file next to this README
with Next.js 16 agent instructions.