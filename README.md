# Enlace Microservice Reference

Standardized schemas and contracts for microservices that exchange data across three roles:

- **Retriever** — pull data from arbitrary sources and emit `RetrievedPayload`
- **Curation** — transform retrieved data into `CuratedPayload` for presentation and action
- **Action** — execute side effects from curated data and emit `ActionResult`

Contracts are **transport-agnostic** (Pydantic models + JSON Schema). The reference demo wires services with Redis pub/sub via Docker Compose.

## Quickstart

### Run tests locally

```bash
source $HOME/.local/bin/env   # if uv was just installed
uv sync --dev
uv run pytest
uv run python scripts/export_schemas.py
```

### Run the end-to-end demo

```bash
docker compose up --build
```

Trigger a retrieval against the mounted fixture:

```bash
curl -s -X POST http://localhost:8001/retrieve \
  -H 'Content-Type: application/json' \
  -d '{
    "adapter": "file",
    "source": {
      "handle": "/fixtures/sample.json",
      "label": "Sample Fixture"
    }
  }'
```

Watch service logs:

```bash
docker compose logs -f curation action
```

The action service delivers to httpbin (`http://httpbin:8080/post`) when `RECIPIENT_ADAPTER=webhook`.

### Integration test against compose

```bash
docker compose up --build -d
ENLACE_INTEGRATION=1 uv run pytest tests/integration/test_compose.py
```

## Repository layout

```
packages/
  enlace-core/        Shared envelope, lineage, errors, data reliability snapshots
  enlace-contracts/   Boundary payloads (retrieved, curated, action-result)
  enlace-retriever/   Retriever protocol + BaseRetriever
  enlace-curation/    Curator protocol + ReferenceCurator
  enlace-action/      ActionExecutor protocol + idempotency
  enlace-transport/   InMemoryBus, RedisBus, HTTP helpers
examples/adapters/    File/HTTP source adapters, logging/webhook recipients
services/             Runnable FastAPI reference microservices
tests/                Contract, role, and integration tests
schemas/json/         Exported JSON Schema (generated)
```

## Message flow

1. `POST /retrieve` on retriever-service
2. Retriever publishes `RetrievedMessage` on Redis topic `retrieved`
3. Curation-service consumes, curates, publishes `CuratedMessage` on `curated`
4. Action-service consumes, delivers via adapter, publishes `ActionResultMessage` on `action-result`

See [docs/architecture.md](docs/architecture.md) for design details.
