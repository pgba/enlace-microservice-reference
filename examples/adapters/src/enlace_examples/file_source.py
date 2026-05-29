from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path

from enlace_core.refs import SourceRef
from enlace_retriever.protocols import RawFetchResult


class FileSourceAdapter:
    """Reads JSON or CSV files from a mounted volume."""

    async def fetch(self, source: SourceRef) -> RawFetchResult:
        path = Path(source.handle)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")

        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8")

        if suffix == ".json":
            content = json.loads(text)
            raw_format = "application/json"
        elif suffix == ".csv":
            reader = csv.DictReader(StringIO(text))
            content = list(reader)
            raw_format = "text/csv"
        else:
            content = text
            raw_format = "text/plain"

        return RawFetchResult(
            raw_format=raw_format,
            content=content,
            metadata={"path": str(path), "label": source.label},
        )
