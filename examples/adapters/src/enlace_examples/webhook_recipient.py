from __future__ import annotations

import httpx
from enlace_action.protocols import DeliveryBody, DeliveryOutcome
from enlace_core.refs import RecipientRef


class WebhookRecipientAdapter:
    """POST curated content to a configurable webhook URL."""

    def __init__(self, default_url: str | None = None) -> None:
        self._default_url = default_url

    async def deliver(self, recipient: RecipientRef, body: DeliveryBody) -> DeliveryOutcome:
        url = str(recipient.uri) if recipient.uri else self._default_url
        if not url:
            return DeliveryOutcome(
                success=False,
                error_message="No recipient URI or default webhook URL configured",
            )
        payload = {
            "recipient": recipient.model_dump(mode="json"),
            "subject": body.subject,
            "body": body.body,
            "metadata": body.metadata,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            if response.is_success:
                return DeliveryOutcome(
                    success=True,
                    outcome=f"Webhook accepted with status {response.status_code}",
                )
            return DeliveryOutcome(
                success=False,
                error_message=f"Webhook failed with status {response.status_code}",
            )
