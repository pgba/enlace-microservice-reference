from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from enlace_contracts.action import ActionResult, ActionStatus
from enlace_contracts.curation import CuratedPayload, Priority
from enlace_contracts.messages import RetrievedMessage
from enlace_contracts.retrieved import RetrievedPayload
from enlace_core.envelope import create_envelope
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_core.lineage import Lineage
from enlace_core.refs import RecipientRef, SourceRef
from enlace_core.reliability import (
    DataReliabilitySnapshot,
    PipelineStage,
    advance_snapshot,
    create_snapshot,
)
from enlace_core.versioning import CURRENT_SCHEMA_VERSION, SchemaVersion, check_schema_compatible


@pytest.fixture
def source_ref() -> SourceRef:
    return SourceRef(handle="/fixtures/sample.json", label="Sample Fixture")


@pytest.fixture
def service_identity() -> ServiceIdentity:
    return ServiceIdentity(name="test-service", instance="test-1", role=ServiceRole.RETRIEVER)


@pytest.fixture
def sample_reliability(source_ref: SourceRef) -> DataReliabilitySnapshot:
    return create_snapshot(
        source=source_ref,
        estimated_reliability=0.8,
        data_observed_at=datetime(2026, 5, 29, 9, 0, tzinfo=UTC),
        stage=PipelineStage.RETRIEVED,
        snapshot_at=datetime(2026, 5, 29, 9, 5, tzinfo=UTC),
        reliability_basis="test-fixture",
    )


@pytest.fixture
def retrieved_message(
    source_ref: SourceRef,
    service_identity: ServiceIdentity,
    sample_reliability: DataReliabilitySnapshot,
) -> RetrievedMessage:
    retrieval_id = uuid4()
    payload = RetrievedPayload(
        retrieval_id=retrieval_id,
        source=source_ref,
        raw_format="application/json",
        content={"title": "Test", "summary": "Test summary"},
        retrieved_at=datetime.now(tz=UTC),
        data_reliability=sample_reliability,
        metadata={"title": "Test Alert", "priority": "high"},
    )
    lineage = Lineage(
        source=source_ref,
        retrieval_id=str(retrieval_id),
        raw_format="application/json",
    )
    return create_envelope(payload=payload, producer=service_identity, lineage=lineage)


def test_schema_version_parse() -> None:
    version = SchemaVersion.parse("1.2.3")
    assert str(version) == "1.2.3"


def test_schema_version_incompatible_major() -> None:
    with pytest.raises(ValueError, match="Incompatible schema major"):
        check_schema_compatible("1.0.0", "2.0.0")


def test_schema_version_compatible_minor() -> None:
    check_schema_compatible("1.0.0", "1.1.0")


def test_data_reliability_snapshot_age(sample_reliability: DataReliabilitySnapshot) -> None:
    assert sample_reliability.data_age_seconds == 300.0
    assert sample_reliability.stage == PipelineStage.RETRIEVED


def test_advance_snapshot_updates_stage_and_age(
    sample_reliability: DataReliabilitySnapshot,
) -> None:
    curated = advance_snapshot(
        sample_reliability,
        stage=PipelineStage.CURATED,
        snapshot_at=datetime(2026, 5, 29, 9, 10, tzinfo=UTC),
    )
    assert curated.stage == PipelineStage.CURATED
    assert curated.data_age_seconds == 600.0
    assert curated.source == sample_reliability.source


def test_retrieved_message_round_trip(retrieved_message: RetrievedMessage) -> None:
    data = retrieved_message.model_dump(mode="json")
    restored = RetrievedMessage.model_validate(data)
    assert restored.payload.retrieval_id == retrieved_message.payload.retrieval_id
    assert restored.schema_version == CURRENT_SCHEMA_VERSION
    assert restored.payload.data_reliability.source.handle == "/fixtures/sample.json"


def test_golden_retrieved_fixture(retrieved_message: RetrievedMessage) -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "retrieved_message.json"
    expected = json.loads(fixture_path.read_text(encoding="utf-8"))
    actual = retrieved_message.model_dump(mode="json")
    for key in ("schema_version", "producer", "lineage", "payload"):
        assert key in actual
    assert actual["payload"]["raw_format"] == expected["payload"]["raw_format"]
    assert actual["payload"]["metadata"] == expected["payload"]["metadata"]
    assert "data_reliability" in actual["payload"]


def test_curated_payload_validation(sample_reliability: DataReliabilitySnapshot) -> None:
    curated = advance_snapshot(sample_reliability, stage=PipelineStage.CURATED)
    payload = CuratedPayload(
        curation_id=uuid4(),
        title="Alert",
        summary="Something happened",
        priority=Priority.HIGH,
        data_reliability=curated,
    )
    assert payload.priority == Priority.HIGH
    assert payload.data_reliability.stage == PipelineStage.CURATED


def test_action_result_with_error(sample_reliability: DataReliabilitySnapshot) -> None:
    from enlace_core.errors import EnlaceError

    action_snapshot = advance_snapshot(sample_reliability, stage=PipelineStage.ACTION)
    result = ActionResult(
        action_id=uuid4(),
        idempotency_key="abc",
        status=ActionStatus.FAILED,
        recipient=RecipientRef(handle="ops", label="Ops Team"),
        data_reliability=action_snapshot,
        error=EnlaceError(code="delivery_failed", message="timeout", retryable=True),
    )
    data = result.model_dump(mode="json")
    assert data["status"] == "failed"
    assert data["error"]["retryable"] is True
    assert data["data_reliability"]["stage"] == "action"
