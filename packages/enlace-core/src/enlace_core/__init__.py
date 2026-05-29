"""Shared envelope, metadata, and error types for Enlace microservices."""

from enlace_core.envelope import Envelope, create_envelope, extend_lineage
from enlace_core.errors import EnlaceError
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_core.lineage import Lineage, LineageHop
from enlace_core.refs import RecipientRef, SourceRef
from enlace_core.reliability import (
    DataReliabilitySnapshot,
    PipelineStage,
    advance_snapshot,
    compute_data_age_seconds,
    create_snapshot,
)
from enlace_core.versioning import (
    CURRENT_SCHEMA_VERSION,
    SchemaVersion,
    check_schema_compatible,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "DataReliabilitySnapshot",
    "EnlaceError",
    "Envelope",
    "Lineage",
    "LineageHop",
    "PipelineStage",
    "RecipientRef",
    "SchemaVersion",
    "ServiceIdentity",
    "ServiceRole",
    "SourceRef",
    "advance_snapshot",
    "check_schema_compatible",
    "compute_data_age_seconds",
    "create_envelope",
    "create_snapshot",
    "extend_lineage",
]
