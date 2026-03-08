import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import create_execution_record
from app.deps import get_db_session
from app.errors import (
    ExecutionNotFoundError,
    PolicyDeniedError,
    ToolNotFoundError,
    ToolOutputTooLargeError,
    ToolTimeoutError,
)
from app.models import ExecutionRecord, Tool
from app.policy.engine import evaluate
from app.runtime import run_subprocess_tool
from app.schemas import (
    ExecutionCreate,
    ExecutionRecordListResponse,
    ExecutionRecordResponse,
    ExecutionResponse,
    ReplayExecutionRequest,
)
from app.settings import settings

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("", response_model=ExecutionResponse)
async def execute_tool(
    payload: ExecutionCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionResponse:
    result = await session.execute(
        select(Tool).where(
            Tool.name == payload.tool_name,
            Tool.version == payload.tool_version,
        )
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        raise ToolNotFoundError()

    trace_id = request.headers.get("x-trace-id", "")

    return await _execute_with_tool(
        tool=tool,
        tool_input=payload.input,
        trace_id=trace_id,
        session=session,
    )


def to_execution_record_response(record: ExecutionRecord) -> ExecutionRecordResponse:
    return ExecutionRecordResponse(
        id=record.id,
        tool_name=record.tool_name,
        tool_version=record.tool_version,
        runtime=record.runtime,
        entrypoint=record.entrypoint,
        status=record.status,
        error_code=record.error_code,
        input_json=json.loads(record.input_json),
        output_json=json.loads(record.output_json) if record.output_json else None,
        stdout=record.stdout,
        stderr=record.stderr,
        exit_code=record.exit_code,
        latency_ms=record.latency_ms,
        trace_id=record.trace_id,
        replay_of_execution_id=record.replay_of_execution_id,
        replay_reason=record.replay_reason,
        created_at=record.created_at,
    )


@router.get("/{execution_id}", response_model=ExecutionRecordResponse)
async def get_execution(
    execution_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionRecordResponse:
    result = await session.execute(
        select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise ExecutionNotFoundError()

    return to_execution_record_response(record)


@router.get("", response_model=ExecutionRecordListResponse)
async def list_executions(
    trace_id: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionRecordListResponse:
    stmt = select(ExecutionRecord).order_by(ExecutionRecord.id)

    if trace_id:
        stmt = stmt.where(ExecutionRecord.trace_id == trace_id)

    result = await session.execute(stmt)
    records = result.scalars().all()

    return ExecutionRecordListResponse(
        items=[to_execution_record_response(record) for record in records]
    )


async def _execute_with_tool(
    *,
    tool: Tool,
    tool_input: dict,
    trace_id: str,
    session: AsyncSession,
    replay_of_execution_id: int | None = None,
    replay_reason: str | None = None,
) -> ExecutionResponse:
    decision = evaluate(tool, tool_input, max_input_bytes=settings.max_input_bytes)
    if not decision.allowed:
        await create_execution_record(
            session=session,
            tool=tool,
            status="policy_denied",
            error_code=decision.reason,
            tool_input=tool_input,
            output_json=None,
            stdout="",
            stderr="",
            exit_code=None,
            latency_ms=0,
            trace_id=trace_id,
            replay_of_execution_id=replay_of_execution_id,
            replay_reason=replay_reason,
        )
        raise PolicyDeniedError(decision.reason or "policy_denied")

    runtime_result = await run_subprocess_tool(
        entrypoint=tool.entrypoint,
        tool_input=tool_input,
        timeout_ms=tool.timeout_ms,
        max_stdout_bytes=settings.max_stdout_bytes,
        max_stderr_bytes=settings.max_stderr_bytes,
    )

    if runtime_result.status == "timeout":
        await create_execution_record(
            session=session,
            tool=tool,
            status="timeout",
            error_code="tool_timeout",
            tool_input=tool_input,
            output_json=None,
            stdout=runtime_result.stdout,
            stderr=runtime_result.stderr,
            exit_code=runtime_result.exit_code,
            latency_ms=runtime_result.latency_ms,
            trace_id=trace_id,
            replay_of_execution_id=replay_of_execution_id,
            replay_reason=replay_reason,
        )
        raise ToolTimeoutError()

    if runtime_result.status == "output_too_large":
        await create_execution_record(
            session=session,
            tool=tool,
            status="failed",
            error_code="tool_output_too_large",
            tool_input=tool_input,
            output_json=None,
            stdout=runtime_result.stdout,
            stderr=runtime_result.stderr,
            exit_code=runtime_result.exit_code,
            latency_ms=runtime_result.latency_ms,
            trace_id=trace_id,
            replay_of_execution_id=replay_of_execution_id,
            replay_reason=replay_reason,
        )
        raise ToolOutputTooLargeError()

    error_code = None if runtime_result.status == "succeeded" else "tool_nonzero_exit"

    await create_execution_record(
        session=session,
        tool=tool,
        status=runtime_result.status,
        error_code=error_code,
        tool_input=tool_input,
        output_json=runtime_result.output,
        stdout=runtime_result.stdout,
        stderr=runtime_result.stderr,
        exit_code=runtime_result.exit_code,
        latency_ms=runtime_result.latency_ms,
        trace_id=trace_id,
        replay_of_execution_id=replay_of_execution_id,
        replay_reason=replay_reason,
    )

    return ExecutionResponse(
        tool_name=tool.name,
        tool_version=tool.version,
        status=runtime_result.status,
        exit_code=runtime_result.exit_code,
        stdout=runtime_result.stdout,
        stderr=runtime_result.stderr,
        output=runtime_result.output,
        trace_id=trace_id,
        latency_ms=runtime_result.latency_ms,
    )


@router.post("/{execution_id}/replay", response_model=ExecutionResponse)
async def replay_execution(
    execution_id: int,
    payload: ReplayExecutionRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionResponse:
    result = await session.execute(
        select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
    )
    original = result.scalar_one_or_none()

    if original is None:
        raise ExecutionNotFoundError()

    tool_result = await session.execute(
        select(Tool).where(
            Tool.name == original.tool_name,
            Tool.version == original.tool_version,
        )
    )
    tool = tool_result.scalar_one_or_none()

    if tool is None:
        raise ToolNotFoundError()

    tool_input = json.loads(original.input_json)
    trace_id = request.headers.get("x-trace-id", "")

    return await _execute_with_tool(
        tool=tool,
        tool_input=tool_input,
        trace_id=trace_id,
        session=session,
        replay_of_execution_id=original.id,
        replay_reason=payload.reason or "manual_replay",
    )
