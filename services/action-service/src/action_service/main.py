from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from enlace_action.base import BaseActionExecutor
from enlace_action.idempotency import InMemoryIdempotencyStore
from enlace_contracts.messages import ActionResultMessage, CuratedMessage
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_examples.logging_recipient import LoggingRecipientAdapter
from enlace_examples.webhook_recipient import WebhookRecipientAdapter
from enlace_transport.redis_bus import RedisBus
from enlace_transport.topics import TOPIC_ACTION_RESULT, TOPIC_CURATED
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def _build_adapter():
    adapter_type = os.environ.get("RECIPIENT_ADAPTER", "logging")
    if adapter_type == "webhook":
        return WebhookRecipientAdapter(default_url=os.environ.get("WEBHOOK_URL"))
    return LoggingRecipientAdapter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    bus = RedisBus(redis_url)
    bus.register_model(TOPIC_CURATED, CuratedMessage)
    bus.register_model(TOPIC_ACTION_RESULT, ActionResultMessage)
    await bus.connect()

    identity = ServiceIdentity(
        name="action-service",
        instance=os.environ.get("HOSTNAME", "local"),
        role=ServiceRole.ACTION,
    )
    executor = BaseActionExecutor(
        adapter=_build_adapter(),
        identity=identity,
        idempotency_store=InMemoryIdempotencyStore(),
    )

    async def handle_curated(message: CuratedMessage) -> None:
        results = await executor.execute(message)
        for result in results:
            await bus.publish(TOPIC_ACTION_RESULT, result)
            logger.info(
                "Published action result %s status=%s",
                result.message_id,
                result.payload.status.value,
            )

    await bus.subscribe(TOPIC_CURATED, handle_curated)
    app.state.bus = bus
    yield
    await bus.close()


app = FastAPI(title="Enlace Action Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", "8003"))
    uvicorn.run("action_service.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
