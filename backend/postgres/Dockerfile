# The PostGIS image supplies spatial extensions; pgvector is installed from the
# PostgreSQL package repository used by the PostgreSQL 16 base image.
FROM postgis/postgis:16-3.5

RUN sed -i 's|http://apt.postgresql.org|https://apt.postgresql.org|' /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install --yes --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
