from __future__ import annotations

from typing import Protocol


class IdempotencyStore(Protocol):
    async def seen(self, key: str) -> bool: ...

    async def mark(self, key: str) -> None: ...


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._keys: set[str] = set()

    async def seen(self, key: str) -> bool:
        return key in self._keys

    async def mark(self, key: str) -> None:
        self._keys.add(key)
