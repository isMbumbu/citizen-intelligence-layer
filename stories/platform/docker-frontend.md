# Frontend Docker delivery

## Scope

Containerize the Next.js frontend as part of the local Citizen Intelligence
Layer stack. This story is governed by `principles/architecture.md`,
`principles/security.md`, and `specs/api.md`.

## Acceptance criteria

1. The frontend uses a reproducible, multistage build based on the committed
   npm lockfile and produces a minimal Next.js standalone runtime image.
2. The runtime image runs as an unprivileged user and excludes source,
   environment files, development dependencies, and build caches.
3. Compose serves the frontend on port 3000 and routes its server-side and
   same-origin API requests to the internal `api` service, not host localhost.
4. The frontend receives no database, broker, or application-secret
   environment variables.
5. The lint and production build commands pass, and the Compose frontend can
   reach the API health endpoint through the integrated stack.
