from __future__ import annotations

import httpx
from enlace_core.refs import SourceRef
from enlace_retriever.protocols import RawFetchResult


class HttpSourceAdapter:
    """Fetches remote content via HTTP GET."""

    async def fetch(self, source: SourceRef) -> RawFetchResult:
        if source.uri is None:
            raise ValueError("HttpSourceAdapter requires source.uri")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(str(source.uri))
            response.raise_for_status()
            content_type = response.headers.get("content-type", "application/octet-stream")
            if "json" in content_type:
                content = response.json()
            else:
                content = response.text
            return RawFetchResult(
                raw_format=content_type,
                content=content,
                metadata={"url": str(source.uri), "status_code": str(response.status_code)},
            )
