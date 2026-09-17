# Compose PostgreSQL extensions from prebuilt, multi-architecture layers rather
# than downloading packages during the local image build.
FROM postgres:17-trixie

RUN rm -f /etc/apt/sources.list.d/pgdg.list \
	&& apt-get update \
	&& apt-get install --yes --no-install-recommends libldap2 \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/pglayers/pgx-pgvector:17 / /
COPY --from=ghcr.io/pglayers/pgx-postgis:17 / /
