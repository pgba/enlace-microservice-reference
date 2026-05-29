# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
COPY packages/ packages/
COPY examples/ examples/
COPY services/ services/

ARG SERVICE=retriever-service
RUN uv sync --frozen --package ${SERVICE}

FROM python:3.12-slim-bookworm
WORKDIR /app

ARG SERVICE=retriever-service
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app /app

CMD ["uv", "run", "retriever-service"]
