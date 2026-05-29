from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

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
            observed_at = _parse_observed_at(response) or datetime.now(tz=UTC)
            return RawFetchResult(
                raw_format=content_type,
                content=content,
                metadata={
                    "url": str(source.uri),
                    "status_code": str(response.status_code),
                    "reliability_basis": "http-response-headers",
                },
                estimated_reliability=0.7,
                data_observed_at=observed_at,
            )


def _parse_observed_at(response: httpx.Response) -> datetime | None:
    for header in ("last-modified", "date"):
        raw = response.headers.get(header)
        if not raw:
            continue
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None
