from enum import StrEnum
from uuid import UUID

from enlace_core.errors import EnlaceError
from enlace_core.refs import RecipientRef
from pydantic import BaseModel, Field


class ActionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionResult(BaseModel):
    action_id: UUID
    idempotency_key: str = Field(..., min_length=1)
    status: ActionStatus
    recipient: RecipientRef
    outcome: str | None = None
    error: EnlaceError | None = None
