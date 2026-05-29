from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class HttpTransport:
    """HTTP client for publishing messages to service endpoints."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def publish(self, topic: str, message: BaseModel) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/messages/{topic}",
                json=message.model_dump(mode="json"),
            )
            response.raise_for_status()


def create_message_router[T: BaseModel](
    *,
    topic: str,
    model: type[T],
    handler: Callable[[T], Awaitable[None]],
) -> APIRouter:
    router = APIRouter()

    async def receive_message(payload: dict[str, Any]) -> dict[str, str]:
        try:
            message = model.model_validate(payload)
            await handler(message)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"status": "accepted"}

    router.add_api_route(
        f"/messages/{topic}",
        receive_message,
        methods=["POST"],
        response_model=dict[str, str],
    )
    return router
