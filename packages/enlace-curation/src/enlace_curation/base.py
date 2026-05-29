from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from enlace_contracts.curation import (
    ActionHint,
    CuratedPayload,
    PresentationBlock,
    PresentationBlockType,
    Priority,
)
from enlace_contracts.messages import CuratedMessage, RetrievedMessage
from enlace_core.envelope import create_envelope, extend_lineage
from enlace_core.identity import ServiceIdentity
from enlace_core.reliability import DataReliabilitySnapshot, PipelineStage, advance_snapshot

from enlace_curation.protocols import Curator

STALENESS_DECAY_PER_HOUR = 0.05
MIN_RELIABILITY = 0.1


class BaseCurator(Curator):
    def __init__(self, *, identity: ServiceIdentity) -> None:
        self._identity = identity

    async def curate(self, message: RetrievedMessage) -> CuratedMessage:
        raise NotImplementedError


class ReferenceCurator(BaseCurator):
    """Maps retrieved metadata and content into presentation blocks and action hints."""

    async def curate(self, message: RetrievedMessage) -> CuratedMessage:
        payload = message.payload
        title = payload.metadata.get("title") or payload.source.label
        summary = payload.metadata.get("summary") or _summarize_content(payload.content)
        curation_id = uuid4()
        data_reliability = _curated_reliability(payload.data_reliability)

        presentation = [
            PresentationBlock(
                block_type=PresentationBlockType.TEXT,
                title="Summary",
                body=summary,
            ),
            PresentationBlock(
                block_type=PresentationBlockType.METRIC,
                title="Format",
                data={"raw_format": payload.raw_format},
            ),
            PresentationBlock(
                block_type=PresentationBlockType.METRIC,
                title="Data Reliability",
                data={
                    "estimated_reliability": data_reliability.estimated_reliability,
                    "data_age_seconds": data_reliability.data_age_seconds,
                    "source_handle": data_reliability.source.handle,
                },
            ),
        ]

        action_hints = [
            ActionHint(
                hint_id="notify-default",
                action_type="notify",
                label="Send notification",
                params={
                    "recipient_handle": payload.metadata.get("recipient_handle", "default"),
                    "subject": title,
                },
            )
        ]

        curated_payload = CuratedPayload(
            curation_id=curation_id,
            title=title,
            summary=summary,
            presentation=presentation,
            action_hints=action_hints,
            priority=Priority(payload.metadata.get("priority", Priority.NORMAL.value)),
            data_reliability=data_reliability,
        )

        lineage = extend_lineage(
            message,
            producer=self._identity,
            hop_id=str(curation_id),
            curation_id=str(curation_id),
            data_reliability=data_reliability,
        )

        return create_envelope(
            payload=curated_payload,
            producer=self._identity,
            lineage=lineage,
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
        )


def _curated_reliability(retrieved: DataReliabilitySnapshot) -> DataReliabilitySnapshot:
    at_curation = advance_snapshot(
        retrieved,
        stage=PipelineStage.CURATED,
        reliability_basis="curator-staleness-adjustment",
    )
    adjusted_score = _adjust_reliability_for_staleness(
        at_curation.estimated_reliability,
        at_curation,
    )
    if adjusted_score == at_curation.estimated_reliability:
        return at_curation
    return at_curation.model_copy(update={"estimated_reliability": adjusted_score})


def _adjust_reliability_for_staleness(
    reliability: float,
    snapshot: DataReliabilitySnapshot,
) -> float:
    hours = snapshot.data_age_seconds / 3600
    decay = min(0.5, hours * STALENESS_DECAY_PER_HOUR)
    return max(MIN_RELIABILITY, reliability - decay)


def _summarize_content(content: dict[str, Any] | list[Any] | str) -> str:
    if isinstance(content, str):
        return content[:500]
    return json.dumps(content, default=str)[:500]
