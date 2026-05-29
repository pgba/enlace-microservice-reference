from enum import StrEnum

from pydantic import BaseModel, Field


class ServiceRole(StrEnum):
    RETRIEVER = "retriever"
    CURATION = "curation"
    ACTION = "action"


class ServiceIdentity(BaseModel):
    name: str = Field(..., min_length=1, description="Logical service name")
    instance: str = Field(..., min_length=1, description="Unique instance identifier")
    role: ServiceRole
