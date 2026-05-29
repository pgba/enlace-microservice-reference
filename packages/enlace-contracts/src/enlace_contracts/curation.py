from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class PresentationBlockType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    LINK = "link"
    METRIC = "metric"


class PresentationBlock(BaseModel):
    block_type: PresentationBlockType
    title: str | None = None
    body: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ActionHint(BaseModel):
    hint_id: str = Field(..., min_length=1)
    action_type: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    params: dict[str, str] = Field(default_factory=dict)


class CuratedPayload(BaseModel):
    curation_id: UUID
    title: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    presentation: list[PresentationBlock] = Field(default_factory=list)
    action_hints: list[ActionHint] = Field(default_factory=list)
    priority: Priority = Priority.NORMAL
    expires_at: datetime | None = None
