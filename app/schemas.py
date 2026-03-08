from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

ALLOWED_RUNTIMES = {"subprocess-v1"}


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=32)
    description: str = Field(min_length=1)
    runtime: str
    entrypoint: str = Field(min_length=1, max_length=256)
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
    entrypoint: str
    timeout_ms: int
    input_schema: dict[str, Any]
    is_active: bool
    created_at: datetime


class ToolListResponse(BaseModel):
    items: list[ToolResponse]


class ExecutionCreate(BaseModel):
    tool_name: str = Field(min_length=1, max_length=128)
    tool_version: str = Field(min_length=1, max_length=32)
    input: dict[str, Any]


class ExecutionResponse(BaseModel):
    tool_name: str
    tool_version: str
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    output: dict[str, Any] | None
    trace_id: str
    latency_ms: int


class ExecutionRecordResponse(BaseModel):
    id: int
    tool_name: str
    tool_version: str
    runtime: str
    entrypoint: str
    status: str
    error_code: str | None
    input_json: dict[str, Any]
    output_json: dict[str, Any] | None
    stdout: str
    stderr: str
    exit_code: int | None
    latency_ms: int
    trace_id: str
    replay_of_execution_id: int | None
    replay_reason: str | None
    created_at: datetime


class ExecutionRecordListResponse(BaseModel):
    items: list[ExecutionRecordResponse]


class ErrorResponse(BaseModel):
    error: str
    message: str
    trace_id: str


class ReplayExecutionRequest(BaseModel):
    reason: str | None = None
