from __future__ import annotations

from uuid import uuid4

from enlace_contracts.action import ActionResult, ActionStatus
from enlace_contracts.messages import ActionResultMessage, CuratedMessage
from enlace_core.envelope import create_envelope, extend_lineage
from enlace_core.errors import EnlaceError
from enlace_core.identity import ServiceIdentity
from enlace_core.refs import RecipientRef

from enlace_action.idempotency import IdempotencyStore
from enlace_action.protocols import ActionExecutor, DeliveryBody, RecipientAdapter


class BaseActionExecutor(ActionExecutor):
    def __init__(
        self,
        *,
        adapter: RecipientAdapter,
        identity: ServiceIdentity,
        idempotency_store: IdempotencyStore,
    ) -> None:
        self._adapter = adapter
        self._identity = identity
        self._idempotency_store = idempotency_store

    async def execute(self, message: CuratedMessage) -> list[ActionResultMessage]:
        results: list[ActionResultMessage] = []
        for hint in message.payload.action_hints:
            idempotency_key = f"{message.correlation_id}:{hint.hint_id}"
            if await self._idempotency_store.seen(idempotency_key):
                result = ActionResult(
                    action_id=uuid4(),
                    idempotency_key=idempotency_key,
                    status=ActionStatus.SKIPPED,
                    recipient=RecipientRef(
                        handle=hint.params.get("recipient_handle", "default"),
                        label=hint.params.get("recipient_handle", "default"),
                    ),
                    outcome="Duplicate action skipped",
                )
            else:
                recipient = RecipientRef(
                    handle=hint.params.get("recipient_handle", "default"),
                    label=hint.params.get("recipient_handle", "default"),
                )
                delivery = DeliveryBody(
                    subject=hint.params.get("subject", message.payload.title),
                    body=message.payload.summary,
                    metadata={"action_type": hint.action_type, "hint_id": hint.hint_id},
                )
                outcome = await self._adapter.deliver(recipient, delivery)
                await self._idempotency_store.mark(idempotency_key)
                if outcome.success:
                    result = ActionResult(
                        action_id=uuid4(),
                        idempotency_key=idempotency_key,
                        status=ActionStatus.SUCCEEDED,
                        recipient=recipient,
                        outcome=outcome.outcome,
                    )
                else:
                    result = ActionResult(
                        action_id=uuid4(),
                        idempotency_key=idempotency_key,
                        status=ActionStatus.FAILED,
                        recipient=recipient,
                        error=EnlaceError(
                            code="delivery_failed",
                            message=outcome.error_message or "Delivery failed",
                            retryable=True,
                        ),
                    )

            lineage = extend_lineage(
                message,
                producer=self._identity,
                hop_id=str(result.action_id),
            )
            results.append(
                create_envelope(
                    payload=result,
                    producer=self._identity,
                    lineage=lineage,
                    correlation_id=message.correlation_id,
                    causation_id=message.message_id,
                )
            )
        return results
