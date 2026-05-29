from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_core.refs import SourceRef
from enlace_examples.file_source import FileSourceAdapter
from enlace_examples.http_source import HttpSourceAdapter
from enlace_retriever.base import BaseRetriever
from enlace_transport.redis_bus import RedisBus
from enlace_transport.topics import TOPIC_RETRIEVED
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RetrieveRequest(BaseModel):
    source: SourceRef
    adapter: str = "file"


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    bus = RedisBus(redis_url)
    from enlace_contracts.messages import RetrievedMessage

    bus.register_model(TOPIC_RETRIEVED, RetrievedMessage)
    await bus.connect()
    app.state.bus = bus
    yield
    await bus.close()


app = FastAPI(title="Enlace Retriever Service", lifespan=lifespan)


def _build_retriever(adapter_name: str) -> BaseRetriever:
    identity = ServiceIdentity(
        name="retriever-service",
        instance=os.environ.get("HOSTNAME", "local"),
        role=ServiceRole.RETRIEVER,
    )
    if adapter_name == "http":
        adapter = HttpSourceAdapter()
    else:
        adapter = FileSourceAdapter()
    return BaseRetriever(adapter=adapter, identity=identity)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/retrieve")
async def retrieve(request: RetrieveRequest) -> dict[str, str]:
    retriever = _build_retriever(request.adapter)
    message = await retriever.retrieve(request.source)
    bus: RedisBus = app.state.bus
    await bus.publish(TOPIC_RETRIEVED, message)
    logger.info("Published retrieved message %s", message.message_id)
    return {
        "status": "published",
        "message_id": str(message.message_id),
        "correlation_id": str(message.correlation_id),
    }


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run("retriever_service.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
