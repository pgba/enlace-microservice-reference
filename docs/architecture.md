# Architecture

## Service roles

| Role | Input | Output | Responsibility |
|------|-------|--------|----------------|
| Retriever | External source (via adapter) | `RetrievedMessage` | Normalize arbitrary ingress into standard contract |
| Curation | `RetrievedMessage` | `CuratedMessage` | Build presentation view and action hints |
| Action | `CuratedMessage` | `ActionResultMessage` | Execute side effects via recipient adapter |

Arbitrary formats and protocols live **only in adapters**. Shared contracts never embed source-specific shapes.

## Envelope

Every inter-service message uses `Envelope[T]` from `enlace-core`:

- `message_id`, `correlation_id`, `causation_id` — tracing and causality
- `schema_version` — semver compatibility gate
- `producer` — `ServiceIdentity` with role
- `payload` — typed contract body
- `lineage` — provenance (`source`, `retrieval_id`, `curation_id`, hop history)

## Contracts

| Contract | Topic | Producer | Consumer |
|----------|-------|----------|----------|
| `RetrievedPayload` | `retrieved` | Retriever | Curation |
| `CuratedPayload` | `curated` | Curation | Action |
| `ActionResult` | `action-result` | Action | Audit / feedback |

`CuratedPayload` separates:

- **presentation** — blocks for UI (`text`, `table`, `link`, `metric`)
- **action_hints** — structured suggestions with params for the action service

## Adapter SPI

### Source adapters (retriever)

```python
class SourceAdapter(Protocol):
    async def fetch(self, source: SourceRef) -> RawFetchResult: ...
```

Examples: `FileSourceAdapter`, `HttpSourceAdapter`.

### Recipient adapters (action)

```python
class RecipientAdapter(Protocol):
    async def deliver(self, recipient: RecipientRef, body: DeliveryBody) -> DeliveryOutcome: ...
```

Examples: `LoggingRecipientAdapter`, `WebhookRecipientAdapter`.

## Transport

Contracts do not depend on transport. The reference demo uses:

- **Redis pub/sub** (`RedisBus`) between compose services
- **InMemoryBus** for unit tests
- **HttpTransport** for direct HTTP publish (optional)

Topics: `retrieved`, `curated`, `action-result`.

## Versioning policy

- **Major** — breaking payload or envelope changes; consumers reject mismatched major versions
- **Minor** — additive fields only; older consumers remain compatible
- **Patch** — documentation or non-serialized changes

Current schema version: `1.0.0` (`enlace_core.versioning.CURRENT_SCHEMA_VERSION`).

Golden JSON fixtures live in `tests/contract/fixtures/`. Export schemas with:

```bash
uv run python scripts/export_schemas.py
```

## Idempotency

Action execution deduplicates on `idempotency_key = "{correlation_id}:{hint_id}"`. Duplicate deliveries return `ActionStatus.SKIPPED`.

## Extension checklist

1. Implement a `SourceAdapter` or `RecipientAdapter`
2. Wire it in your service bootstrap (see `services/*/main.py`)
3. Do **not** modify shared contracts for source-specific fields — use `metadata` on `RetrievedPayload` or adapter-local config
4. Add contract tests if you extend shared payloads
