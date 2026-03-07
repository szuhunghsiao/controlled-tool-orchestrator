from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session
from app.models import Tool
from app.runtime import run_subprocess_tool
from app.schemas import ExecutionCreate, ExecutionResponse
from app.policy.engine import evaluate
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tool not found")

    decision = evaluate(tool, payload.input, max_input_bytes=settings.max_input_bytes)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=decision.reason,
        )

    runtime_result = await run_subprocess_tool(
        entrypoint=tool.entrypoint,
        tool_input=payload.input,
        timeout_ms=tool.timeout_ms,
        max_stdout_bytes=settings.max_stdout_bytes,
        max_stderr_bytes=settings.max_stderr_bytes,
    )

    trace_id = request.headers.get("x-trace-id", "")

    if runtime_result.status == "timeout":
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT, 
            detail="tool_timeout"
            )

    if runtime_result.status == "output_too_large":
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 
            detail="tool_output_too_large"
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