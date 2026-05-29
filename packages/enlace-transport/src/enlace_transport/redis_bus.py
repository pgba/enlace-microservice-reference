from __future__ import annotations

import asyncio
import json

from pydantic import BaseModel
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from enlace_transport.protocols import MessageHandler


class RedisBus:
    """Redis pub/sub transport for decoupled microservices."""

    def __init__(self, redis_url: str, *, channel_prefix: str = "enlace") -> None:
        self._redis_url = redis_url
        self._channel_prefix = channel_prefix
        self._redis: Redis | None = None
        self._pubsub: PubSub | None = None
        self._listener_task: asyncio.Task[None] | None = None
        self._handlers: dict[str, list[tuple[type[BaseModel], MessageHandler]]] = {}
        self._model_registry: dict[str, type[BaseModel]] = {}

    def register_model(self, topic: str, model: type[BaseModel]) -> None:
        self._model_registry[topic] = model

    async def connect(self) -> None:
        self._redis = Redis.from_url(self._redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        self._listener_task = asyncio.create_task(self._listen())

    async def close(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

    def _channel(self, topic: str) -> str:
        return f"{self._channel_prefix}:{topic}"

    async def publish(self, topic: str, message: BaseModel) -> None:
        if self._redis is None:
            raise RuntimeError("RedisBus is not connected")
        payload = message.model_dump_json()
        await self._redis.publish(self._channel(topic), payload)

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        if self._pubsub is None:
            raise RuntimeError("RedisBus is not connected")
        model = self._model_registry.get(topic)
        if model is None:
            raise ValueError(f"No model registered for topic {topic!r}")

        async def wrapped(message: BaseModel) -> None:
            await handler(message)

        self._handlers.setdefault(topic, []).append((model, handler))
        await self._pubsub.subscribe(self._channel(topic))

    async def _listen(self) -> None:
        if self._pubsub is None:
            return
        async for raw in self._pubsub.listen():
            if raw["type"] != "message":
                continue
            channel: str = raw["channel"]
            topic = channel.removeprefix(f"{self._channel_prefix}:")
            data = json.loads(raw["data"])
            for model, handler in self._handlers.get(topic, []):
                message = model.model_validate(data)
                await handler(message)
