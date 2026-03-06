from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


ALLOWED_RUNTIMES = {"subprocess-v1"}


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=32)
    description: str = Field(min_length=1)
    runtime: str
    timeout_ms: int = Field(gt=0, le=300000)
    input_schema: dict[str, Any]

    @field_validator("runtime")
    @classmethod
    def validate_runtime(cls, v: str) -> str:
        if v not in ALLOWED_RUNTIMES:
            raise ValueError(f"unsupported runtime: {v}")
        return v


class ToolResponse(BaseModel):
    id: int
    name: str
    version: str
    description: str
    runtime: str
    timeout_ms: int
    input_schema: dict[str, Any]
    is_active: bool
    created_at: datetime


class ToolListResponse(BaseModel):
    items: list[ToolResponse]