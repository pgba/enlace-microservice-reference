from __future__ import annotations

from typing import Protocol

from enlace_contracts.messages import ActionResultMessage, CuratedMessage
from enlace_core.refs import RecipientRef
from pydantic import BaseModel, Field


class DeliveryBody(BaseModel):
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)


class DeliveryOutcome(BaseModel):
    success: bool
    outcome: str | None = None
    error_message: str | None = None


class RecipientAdapter(Protocol):
    async def deliver(self, recipient: RecipientRef, body: DeliveryBody) -> DeliveryOutcome: ...


class ActionExecutor(Protocol):
    async def execute(self, message: CuratedMessage) -> list[ActionResultMessage]: ...
