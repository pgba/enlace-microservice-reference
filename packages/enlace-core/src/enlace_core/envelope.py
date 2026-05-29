from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from enlace_core.identity import ServiceIdentity
from enlace_core.lineage import Lineage, LineageHop
from enlace_core.reliability import DataReliabilitySnapshot
from enlace_core.versioning import CURRENT_SCHEMA_VERSION


class Envelope[T: BaseModel](BaseModel):
    message_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    schema_version: str = Field(default=CURRENT_SCHEMA_VERSION)
    produced_at: datetime
    producer: ServiceIdentity
    payload: T
    lineage: Lineage


def create_envelope[T: BaseModel](
    *,
    payload: T,
    producer: ServiceIdentity,
    lineage: Lineage,
    correlation_id: UUID | None = None,
    causation_id: UUID | None = None,
    schema_version: str = CURRENT_SCHEMA_VERSION,
) -> Envelope[T]:
    return Envelope(
        message_id=uuid4(),
        correlation_id=correlation_id or uuid4(),
        causation_id=causation_id,
        schema_version=schema_version,
        produced_at=datetime.now(tz=UTC),
        producer=producer,
        payload=payload,
        lineage=lineage,
    )


def extend_lineage[T: BaseModel](
    envelope: Envelope[T],
    *,
    producer: ServiceIdentity,
    hop_id: str,
    retrieval_id: str | None = None,
    curation_id: str | None = None,
    data_reliability: DataReliabilitySnapshot | None = None,
) -> Lineage:
    hop = LineageHop(
        service=producer.name,
        role=producer.role.value,
        hop_id=hop_id,
        occurred_at=datetime.now(tz=UTC).isoformat(),
        data_reliability=data_reliability,
    )
    return envelope.lineage.model_copy(
        update={
            "retrieval_id": retrieval_id or envelope.lineage.retrieval_id,
            "curation_id": curation_id or envelope.lineage.curation_id,
            "hops": [*envelope.lineage.hops, hop],
        }
    )
