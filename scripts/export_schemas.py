#!/usr/bin/env python3
"""Export JSON Schema for all Enlace contract models."""

from __future__ import annotations

import json
from pathlib import Path

from enlace_contracts.action import ActionResult
from enlace_contracts.curation import CuratedPayload
from enlace_contracts.messages import ActionResultMessage, CuratedMessage, RetrievedMessage
from enlace_contracts.retrieved import RetrievedPayload
from enlace_core.envelope import Envelope
from enlace_core.reliability import DataReliabilitySnapshot

MODELS: dict[str, type] = {
    "DataReliabilitySnapshot": DataReliabilitySnapshot,
    "RetrievedPayload": RetrievedPayload,
    "CuratedPayload": CuratedPayload,
    "ActionResult": ActionResult,
    "RetrievedMessage": RetrievedMessage,
    "CuratedMessage": CuratedMessage,
    "ActionResultMessage": ActionResultMessage,
    "Envelope": Envelope,
}


def main() -> None:
    output_dir = Path("schemas/json")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = model.model_json_schema()
        path = output_dir / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
