"""Retriever service role abstractions."""

from enlace_retriever.base import BaseRetriever
from enlace_retriever.protocols import RawFetchResult, Retriever, SourceAdapter

__all__ = ["BaseRetriever", "RawFetchResult", "Retriever", "SourceAdapter"]
