"""Shared envelope, metadata, and error types for Enlace microservices."""

from enlace_core.envelope import Envelope, create_envelope, extend_lineage
from enlace_core.errors import EnlaceError
from enlace_core.identity import ServiceIdentity, ServiceRole
from enlace_core.lineage import Lineage, LineageHop
from enlace_core.refs import RecipientRef, SourceRef
from enlace_core.versioning import (
    CURRENT_SCHEMA_VERSION,
    SchemaVersion,
    check_schema_compatible,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "EnlaceError",
    "Envelope",
    "Lineage",
    "LineageHop",
    "RecipientRef",
    "SchemaVersion",
    "ServiceIdentity",
    "ServiceRole",
    "SourceRef",
    "check_schema_compatible",
    "create_envelope",
    "extend_lineage",
]
