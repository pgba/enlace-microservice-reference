"""Curation service role abstractions."""

from enlace_curation.base import BaseCurator, ReferenceCurator
from enlace_curation.protocols import Curator

__all__ = ["BaseCurator", "Curator", "ReferenceCurator"]
