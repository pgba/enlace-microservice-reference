from __future__ import annotations

import os

import httpx
import pytest

RUN_INTEGRATION = os.environ.get("ENLACE_INTEGRATION", "0") == "1"


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set ENLACE_INTEGRATION=1 with compose running")
@pytest.mark.asyncio
async def test_compose_end_to_end() -> None:
    retriever_url = os.environ.get("RETRIEVER_URL", "http://localhost:8001")
    async with httpx.AsyncClient(timeout=30.0) as client:
        for service in (retriever_url, "http://localhost:8002", "http://localhost:8003"):
            health = await client.get(f"{service}/health")
            health.raise_for_status()

        response = await client.post(
            f"{retriever_url}/retrieve",
            json={
                "adapter": "file",
                "source": {
                    "handle": "/fixtures/sample.json",
                    "label": "Sample Fixture",
                },
            },
        )
        response.raise_for_status()
        body = response.json()
        assert body["status"] == "published"
        assert "correlation_id" in body
