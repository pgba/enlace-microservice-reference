from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from enlace_contracts.messages import CuratedMessage, RetrievedMessage
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_curation.base import ReferenceCurator
from enlace_transport.redis_bus import RedisBus
from enlace_transport.topics import TOPIC_CURATED, TOPIC_RETRIEVED
from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    bus = RedisBus(redis_url)
    bus.register_model(TOPIC_RETRIEVED, RetrievedMessage)
    bus.register_model(TOPIC_CURATED, CuratedMessage)
    await bus.connect()

    identity = ServiceIdentity(
        name="curation-service",
        instance=os.environ.get("HOSTNAME", "local"),
        role=ServiceRole.CURATION,
    )
    curator = ReferenceCurator(identity=identity)

    async def handle_retrieved(message: RetrievedMessage) -> None:
        curated = await curator.curate(message)
        await bus.publish(TOPIC_CURATED, curated)
        logger.info("Published curated message %s", curated.message_id)

    await bus.subscribe(TOPIC_RETRIEVED, handle_retrieved)
    app.state.bus = bus
    yield
    await bus.close()


app = FastAPI(title="Enlace Curation Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", "8002"))
    uvicorn.run("curation_service.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
