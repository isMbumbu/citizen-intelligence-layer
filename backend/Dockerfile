# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

WORKDIR /app

FROM base AS builder

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel

# Keep the project metadata explicit: the image build fails early when a package
# dependency or the application package definition is invalid.
COPY pyproject.toml README.md ./
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/pip \
    /opt/venv/bin/pip install .

FROM builder AS development

# The API development target includes the backend's test and static-analysis
# tools. Compose bind-mounts the source over /app, while PYTHONPATH ensures the
# running process uses that mounted source rather than the installed copy.
RUN --mount=type=cache,target=/root/.cache/pip \
    /opt/venv/bin/pip install --group dev .

COPY alembic ./alembic
COPY alembic.ini ./

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS runtime

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
