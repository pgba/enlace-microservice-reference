from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from enlace_core.refs import SourceRef


class PipelineStage(StrEnum):
    RETRIEVED = "retrieved"
    CURATED = "curated"
    ACTION = "action"


class DataReliabilitySnapshot(BaseModel):
    """Source identity, reliability estimate, and data age at a pipeline stage."""

    source: SourceRef
    estimated_reliability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Estimated reliability of the source data, from 0 (unreliable) to 1 (fully trusted)"
        ),
    )
    data_observed_at: datetime = Field(
        ...,
        description="When the underlying source data was observed or last known to be valid",
    )
    snapshot_at: datetime = Field(
        ...,
        description="When this stage recorded the reliability and age reading",
    )
    data_age_seconds: float = Field(
        ...,
        ge=0.0,
        description="Age of the source data in seconds at snapshot_at",
    )
    stage: PipelineStage
    reliability_basis: str | None = Field(
        default=None,
        description="Human-readable explanation for the reliability estimate",
    )


def compute_data_age_seconds(data_observed_at: datetime, at: datetime) -> float:
    observed = _ensure_utc(data_observed_at)
    reference = _ensure_utc(at)
    return max(0.0, (reference - observed).total_seconds())


def create_snapshot(
    *,
    source: SourceRef,
    estimated_reliability: float,
    data_observed_at: datetime,
    stage: PipelineStage,
    snapshot_at: datetime | None = None,
    reliability_basis: str | None = None,
) -> DataReliabilitySnapshot:
    recorded_at = snapshot_at or datetime.now(tz=UTC)
    return DataReliabilitySnapshot(
        source=source,
        estimated_reliability=estimated_reliability,
        data_observed_at=_ensure_utc(data_observed_at),
        snapshot_at=_ensure_utc(recorded_at),
        data_age_seconds=compute_data_age_seconds(data_observed_at, recorded_at),
        stage=stage,
        reliability_basis=reliability_basis,
    )


def advance_snapshot(
    previous: DataReliabilitySnapshot,
    *,
    stage: PipelineStage,
    estimated_reliability: float | None = None,
    snapshot_at: datetime | None = None,
    reliability_basis: str | None = None,
) -> DataReliabilitySnapshot:
    """Carry source and observed time forward while refreshing age at the next stage."""
    return create_snapshot(
        source=previous.source,
        estimated_reliability=(
            previous.estimated_reliability
            if estimated_reliability is None
            else estimated_reliability
        ),
        data_observed_at=previous.data_observed_at,
        stage=stage,
        snapshot_at=snapshot_at,
        reliability_basis=reliability_basis or previous.reliability_basis,
    )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
