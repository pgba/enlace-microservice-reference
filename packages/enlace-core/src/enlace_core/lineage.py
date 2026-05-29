from pydantic import BaseModel, Field

from enlace_core.refs import SourceRef
from enlace_core.reliability import DataReliabilitySnapshot


class LineageHop(BaseModel):
    service: str
    role: str
    hop_id: str
    occurred_at: str
    data_reliability: DataReliabilitySnapshot | None = None


class Lineage(BaseModel):
    source: SourceRef
    retrieval_id: str | None = None
    curation_id: str | None = None
    raw_format: str | None = None
    hops: list[LineageHop] = Field(default_factory=list)
