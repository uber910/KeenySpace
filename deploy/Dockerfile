FROM python:3.14.1-slim-bookworm AS builder

RUN pip install --no-cache-dir uv==0.5.20

WORKDIR /app
COPY pyproject.toml .
COPY packages/server/pyproject.toml packages/server/pyproject.toml
COPY packages/shared/pyproject.toml packages/shared/pyproject.toml
COPY packages/client/pyproject.toml packages/client/pyproject.toml
COPY uv.lock .
COPY packages/server/keenyspace_server packages/server/keenyspace_server
COPY packages/shared/keenyspace_shared packages/shared/keenyspace_shared
COPY packages/client/keenyspace packages/client/keenyspace

RUN uv sync --frozen --no-dev --package keenyspace-server

FROM python:3.14.1-slim-bookworm AS runtime

# The admin backup/restore endpoints shell out to pg_dump/psql. The client
# major must be >= the postgres server major (17), and bookworm ships 15 —
# pull postgresql-client-17 from PGDG (publishes amd64 + arm64).
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    install -d /usr/share/postgresql-common/pgdg && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc && \
    echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client-17 && \
    apt-get purge -y curl && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 10001 nonroot && \
    useradd --uid 10001 --gid 10001 --no-create-home nonroot

WORKDIR /app

COPY --from=builder /app/.venv .venv
COPY --from=builder /app/packages/server/keenyspace_server packages/server/keenyspace_server
COPY --from=builder /app/packages/shared/keenyspace_shared packages/shared/keenyspace_shared
COPY packages/server/alembic.ini packages/server/alembic.ini
COPY packages/server/alembic packages/server/alembic
COPY blueprints blueprints

ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV KEENYSPACE_FS__ROOT=/var/lib/keenyspace

RUN mkdir -p /var/lib/keenyspace && chown nonroot:nonroot /var/lib/keenyspace

USER nonroot

EXPOSE 8000

CMD [".venv/bin/uvicorn", "keenyspace_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
