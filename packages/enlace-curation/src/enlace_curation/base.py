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

from enlace_curation.protocols import Curator


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
        )

        lineage = extend_lineage(
            message,
            producer=self._identity,
            hop_id=str(curation_id),
            curation_id=str(curation_id),
        )

        return create_envelope(
            payload=curated_payload,
            producer=self._identity,
            lineage=lineage,
            correlation_id=message.correlation_id,
            causation_id=message.message_id,
        )


def _summarize_content(content: dict[str, Any] | list[Any] | str) -> str:
    if isinstance(content, str):
        return content[:500]
    return json.dumps(content, default=str)[:500]
