# syntax=docker/dockerfile:1.7

FROM node:22-bookworm-slim AS base

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

FROM base AS dependencies

# npm ci installs exactly the dependency tree committed in package-lock.json.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

FROM dependencies AS builder

# next.config.ts is evaluated during next build, so the rewrite destination is
# deliberately supplied as a build argument for each deployment environment.
ARG API_BASE_URL=http://api:8000
ENV API_BASE_URL=${API_BASE_URL}

COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN groupadd --system nextjs \
    && useradd --system --gid nextjs --shell /usr/sbin/nologin nextjs

# Next.js standalone output contains only the traced runtime files. Static and
# public assets are copied explicitly because standalone output omits them.
COPY --from=builder --chown=nextjs:nextjs /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
