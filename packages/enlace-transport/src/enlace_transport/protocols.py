from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from pydantic import BaseModel


class Publisher(Protocol):
    async def publish(self, topic: str, message: BaseModel) -> None: ...


class MessageHandler(Protocol):
    async def __call__(self, message: BaseModel) -> None: ...


class Subscriber(Protocol):
    async def subscribe(self, topic: str, handler: MessageHandler) -> None: ...


Handler = Callable[[BaseModel], Awaitable[None]]
