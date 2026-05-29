from datetime import datetime
from typing import Any
from uuid import UUID

from enlace_core.refs import SourceRef
from pydantic import BaseModel, Field


class RetrievedPayload(BaseModel):
    retrieval_id: UUID
    source: SourceRef
    raw_format: str = Field(..., min_length=1, description="MIME type or format label")
    content: dict[str, Any] | list[Any] | str = Field(
        ..., description="JSON-safe content or raw string payload"
    )
    retrieved_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)
