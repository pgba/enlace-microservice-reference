from __future__ import annotations

import logging

from enlace_action.protocols import DeliveryBody, DeliveryOutcome
from enlace_core.refs import RecipientRef

logger = logging.getLogger(__name__)


class LoggingRecipientAdapter:
    """Prints formatted messages to stdout for demo purposes."""

    async def deliver(self, recipient: RecipientRef, body: DeliveryBody) -> DeliveryOutcome:
        logger.info(
            "Delivering message to %s (%s): subject=%r body=%r metadata=%s",
            recipient.label,
            recipient.handle,
            body.subject,
            body.body,
            body.metadata,
        )
        return DeliveryOutcome(success=True, outcome=f"Logged to {recipient.handle}")
