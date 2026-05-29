from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from enlace_contracts.messages import RetrievedMessage
from enlace_contracts.retrieved import RetrievedPayload
from enlace_core.envelope import create_envelope
from enlace_core.identity import ServiceIdentity
from enlace_core.lineage import Lineage
from enlace_core.refs import SourceRef

from enlace_retriever.protocols import Retriever, SourceAdapter


class BaseRetriever(Retriever):
    def __init__(self, *, adapter: SourceAdapter, identity: ServiceIdentity) -> None:
        self._adapter = adapter
        self._identity = identity

    async def retrieve(self, source: SourceRef) -> RetrievedMessage:
        fetch_result = await self._adapter.fetch(source)
        retrieval_id = uuid4()
        payload = RetrievedPayload(
            retrieval_id=retrieval_id,
            source=source,
            raw_format=fetch_result.raw_format,
            content=fetch_result.content,
            retrieved_at=datetime.now(tz=UTC),
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
