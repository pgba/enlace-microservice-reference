from pydantic import BaseModel, Field


class EnlaceError(BaseModel):
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    retryable: bool = False
    details: dict[str, str] = Field(default_factory=dict)
