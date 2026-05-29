from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from enlace_action.base import BaseActionExecutor
from enlace_action.idempotency import InMemoryIdempotencyStore
from enlace_action.protocols import DeliveryBody, DeliveryOutcome
from enlace_contracts.curation import ActionHint, CuratedPayload, Priority
from enlace_contracts.messages import CuratedMessage
from enlace_contracts.retrieved import RetrievedPayload
from enlace_core.envelope import create_envelope
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_core.lineage import Lineage
from enlace_core.refs import RecipientRef, SourceRef
from enlace_curation.base import ReferenceCurator
from enlace_retriever.base import BaseRetriever
from enlace_retriever.protocols import RawFetchResult
from enlace_transport.in_memory import InMemoryBus
from enlace_transport.topics import TOPIC_CURATED, TOPIC_RETRIEVED


class FakeSourceAdapter:
    async def fetch(self, source: SourceRef) -> RawFetchResult:
        return RawFetchResult(
            raw_format="application/json",
            content={"value": 42},
            metadata={"title": "Metric Alert", "summary": "Value is high"},
        )


class FakeRecipientAdapter:
    def __init__(self) -> None:
        self.deliveries: list[tuple[RecipientRef, DeliveryBody]] = []

    async def deliver(self, recipient: RecipientRef, body: DeliveryBody) -> DeliveryOutcome:
        self.deliveries.append((recipient, body))
        return DeliveryOutcome(success=True, outcome="delivered")


@pytest.mark.asyncio
async def test_retriever_pipeline() -> None:
    identity = ServiceIdentity(name="retriever", instance="1", role=ServiceRole.RETRIEVER)
    retriever = BaseRetriever(adapter=FakeSourceAdapter(), identity=identity)
    source = SourceRef(handle="fake", label="Fake Source")
    message = await retriever.retrieve(source)
    assert message.payload.raw_format == "application/json"
    assert message.lineage.retrieval_id is not None


@pytest.mark.asyncio
async def test_curation_pipeline() -> None:
    source = SourceRef(handle="fake", label="Fake")
    retrieval_id = uuid4()
    retrieved = RetrievedPayload(
        retrieval_id=retrieval_id,
        source=source,
        raw_format="application/json",
        content={"x": 1},
        retrieved_at=datetime.now(tz=UTC),
        metadata={"title": "Alert", "summary": "Something happened"},
    )
    lineage = Lineage(source=source, retrieval_id=str(retrieval_id))
    retriever_identity = ServiceIdentity(name="retriever", instance="1", role=ServiceRole.RETRIEVER)
    retrieved_message = create_envelope(
        payload=retrieved,
        producer=retriever_identity,
        lineage=lineage,
    )

    curator = ReferenceCurator(
        identity=ServiceIdentity(name="curation", instance="1", role=ServiceRole.CURATION)
    )
    curated = await curator.curate(retrieved_message)
    assert curated.payload.title == "Alert"
    assert len(curated.payload.action_hints) >= 1


@pytest.mark.asyncio
async def test_action_idempotency() -> None:
    adapter = FakeRecipientAdapter()
    executor = BaseActionExecutor(
        adapter=adapter,
        identity=ServiceIdentity(name="action", instance="1", role=ServiceRole.ACTION),
        idempotency_store=InMemoryIdempotencyStore(),
    )
    source = SourceRef(handle="fake", label="Fake")
    lineage = Lineage(source=source)
    curated_payload = CuratedPayload(
        curation_id=uuid4(),
        title="Alert",
        summary="Do something",
        action_hints=[
            ActionHint(hint_id="h1", action_type="notify", label="Notify", params={})
        ],
        priority=Priority.NORMAL,
    )
    message = create_envelope(
        payload=curated_payload,
        producer=ServiceIdentity(name="curation", instance="1", role=ServiceRole.CURATION),
        lineage=lineage,
    )
    first = await executor.execute(message)
    second = await executor.execute(message)
    assert first[0].payload.status.value == "succeeded"
    assert second[0].payload.status.value == "skipped"
    assert len(adapter.deliveries) == 1


@pytest.mark.asyncio
async def test_in_memory_bus_end_to_end() -> None:
    bus = InMemoryBus()
    curated_messages: list[CuratedMessage] = []

    async def on_retrieved(message):
        curator = ReferenceCurator(
            identity=ServiceIdentity(name="curation", instance="1", role=ServiceRole.CURATION)
        )
        curated = await curator.curate(message)
        await bus.publish(TOPIC_CURATED, curated)

    async def on_curated(message):
        curated_messages.append(message)

    await bus.subscribe(TOPIC_RETRIEVED, on_retrieved)
    await bus.subscribe(TOPIC_CURATED, on_curated)

    retriever = BaseRetriever(
        adapter=FakeSourceAdapter(),
        identity=ServiceIdentity(name="retriever", instance="1", role=ServiceRole.RETRIEVER),
    )
    retrieved = await retriever.retrieve(SourceRef(handle="fake", label="Fake"))
    await bus.publish(TOPIC_RETRIEVED, retrieved)

    assert len(curated_messages) == 1
    assert curated_messages[0].payload.title == "Metric Alert"
