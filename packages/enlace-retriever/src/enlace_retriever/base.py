from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from enlace_contracts.messages import RetrievedMessage
from enlace_contracts.retrieved import RetrievedPayload
from enlace_core.envelope import create_envelope
from enlace_core.identity import ServiceIdentity
from enlace_core.lineage import Lineage
from enlace_core.refs import SourceRef
from enlace_core.reliability import PipelineStage, create_snapshot

from enlace_retriever.protocols import Retriever, SourceAdapter

DEFAULT_RELIABILITY = 0.5
DEFAULT_RELIABILITY_BASIS = "adapter-default"


class BaseRetriever(Retriever):
    def __init__(self, *, adapter: SourceAdapter, identity: ServiceIdentity) -> None:
        self._adapter = adapter
        self._identity = identity

    async def retrieve(self, source: SourceRef) -> RetrievedMessage:
        fetch_result = await self._adapter.fetch(source)
        retrieval_id = uuid4()
        retrieved_at = datetime.now(tz=UTC)
        data_observed_at = fetch_result.data_observed_at or retrieved_at
        reliability = (
            fetch_result.estimated_reliability
            if fetch_result.estimated_reliability is not None
            else DEFAULT_RELIABILITY
        )
        basis = fetch_result.metadata.get("reliability_basis", DEFAULT_RELIABILITY_BASIS)
        data_reliability = create_snapshot(
            source=source,
            estimated_reliability=reliability,
            data_observed_at=data_observed_at,
            stage=PipelineStage.RETRIEVED,
            snapshot_at=retrieved_at,
            reliability_basis=basis,
        )
        payload = RetrievedPayload(
            retrieval_id=retrieval_id,
            source=source,
            raw_format=fetch_result.raw_format,
            content=fetch_result.content,
            retrieved_at=retrieved_at,
            data_reliability=data_reliability,
            metadata=fetch_result.metadata,
        )
        lineage = Lineage(
            source=source,
            retrieval_id=str(retrieval_id),
            raw_format=fetch_result.raw_format,
        )
        return create_envelope(
            payload=payload,
            producer=self._identity,
            lineage=lineage,
        )
