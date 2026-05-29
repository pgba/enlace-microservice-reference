from pydantic import BaseModel, Field, HttpUrl


class SourceRef(BaseModel):
    handle: str = Field(..., min_length=1, description="Opaque adapter-specific source handle")
    label: str = Field(..., min_length=1, description="Human-readable source label")
    uri: HttpUrl | None = Field(default=None, description="Optional URI for the source")


class RecipientRef(BaseModel):
    handle: str = Field(..., min_length=1, description="Opaque adapter-specific recipient handle")
    label: str = Field(..., min_length=1, description="Human-readable recipient label")
    uri: HttpUrl | None = Field(default=None, description="Optional URI for the recipient")
