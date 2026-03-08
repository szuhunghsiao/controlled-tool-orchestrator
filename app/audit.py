import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExecutionRecord, Tool


async def create_execution_record(
    *,
    session: AsyncSession,
    tool: Tool,
    status: str,
    error_code: str | None,
    tool_input: dict[str, Any],
    output_json: dict[str, Any] | None,
    stdout: str,
    stderr: str,
    exit_code: int | None,
    latency_ms: int,
    trace_id: str,
    replay_of_execution_id: int | None = None,
    replay_reason: str | None = None,
) -> ExecutionRecord:
    record = ExecutionRecord(
        tool_name=tool.name,
        tool_version=tool.version,
        runtime=tool.runtime,
        entrypoint=tool.entrypoint,
        status=status,
        error_code=error_code,
        input_json=json.dumps(tool_input, ensure_ascii=False),
        output_json=json.dumps(output_json, ensure_ascii=False) if output_json is not None else None,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        latency_ms=latency_ms,
        trace_id=trace_id,
        replay_of_execution_id=replay_of_execution_id,
        replay_reason=replay_reason,
    )

    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record