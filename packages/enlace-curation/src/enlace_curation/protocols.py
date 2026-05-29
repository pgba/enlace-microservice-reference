from __future__ import annotations

from typing import Protocol

from enlace_contracts.messages import CuratedMessage, RetrievedMessage


class Curator(Protocol):
    async def curate(self, message: RetrievedMessage) -> CuratedMessage: ...
