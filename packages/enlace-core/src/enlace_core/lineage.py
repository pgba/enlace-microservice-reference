from pydantic import BaseModel, Field

from enlace_core.refs import SourceRef


class LineageHop(BaseModel):
    service: str
    role: str
    hop_id: str
    occurred_at: str


class Lineage(BaseModel):
    source: SourceRef
    retrieval_id: str | None = None
    curation_id: str | None = None
    raw_format: str | None = None
    hops: list[LineageHop] = Field(default_factory=list)
