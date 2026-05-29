from __future__ import annotations

from typing import Any, Protocol

from enlace_contracts.messages import RetrievedMessage
from enlace_core.refs import SourceRef
from pydantic import BaseModel, Field


class RawFetchResult(BaseModel):
    raw_format: str = Field(..., min_length=1)
    content: dict[str, Any] | list[Any] | str
    metadata: dict[str, str] = Field(default_factory=dict)


class SourceAdapter(Protocol):
    async def fetch(self, source: SourceRef) -> RawFetchResult: ...


class Retriever(Protocol):
    async def retrieve(self, source: SourceRef) -> RetrievedMessage: ...
