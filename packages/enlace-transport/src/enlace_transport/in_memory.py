from __future__ import annotations

import asyncio
from collections import defaultdict

from pydantic import BaseModel

from enlace_transport.protocols import MessageHandler


class InMemoryBus:
    """In-process pub/sub for tests and local development."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[MessageHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, message: BaseModel) -> None:
        handlers = list(self._handlers.get(topic, []))
        for handler in handlers:
            await handler(message)

    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        async with self._lock:
            self._handlers[topic].append(handler)
