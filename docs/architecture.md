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

## Data reliability

Each contract payload carries a `DataReliabilitySnapshot` recording the pipeline stage, source identity, estimated reliability (0–1), and data age:

| Stage | Field location | Recorded by |
|-------|----------------|-------------|
| Retrieved | `RetrievedPayload.data_reliability` | Retriever (from adapter estimate + observed time) |
| Curated | `CuratedPayload.data_reliability` | Curator (refreshed age; optional staleness adjustment) |
| Action | `ActionResult.data_reliability` | Action executor (refreshed age at delivery) |

`DataReliabilitySnapshot` fields:

- `source` — `SourceRef` for the originating data source
- `estimated_reliability` — adapter or stage-specific score from 0 to 1
- `data_observed_at` — when the underlying source data was last known valid
- `snapshot_at` — when the current stage recorded its reading
- `data_age_seconds` — age of source data at `snapshot_at`
- `stage` — `retrieved`, `curated`, or `action`
- `reliability_basis` — optional explanation (e.g. `file-mtime`, `curator-staleness-adjustment`)

Lineage hops may also attach `data_reliability` when a stage completes. Helpers in `enlace_core.reliability` (`create_snapshot`, `advance_snapshot`) propagate source and observed time while recalculating age at each hop.

Source adapters supply initial estimates via `RawFetchResult.estimated_reliability` and `RawFetchResult.data_observed_at`.

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

Current schema version: `1.1.0` (`enlace_core.versioning.CURRENT_SCHEMA_VERSION`).

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
