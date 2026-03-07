from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session
from app.models import Tool
from app.runtime import run_subprocess_tool
from app.schemas import ExecutionCreate, ExecutionResponse

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

    if not tool.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tool is inactive")

    if tool.runtime != "subprocess-v1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported runtime: {tool.runtime}",
        )

    runtime_result = await run_subprocess_tool(
        entrypoint=tool.entrypoint,
        tool_input=payload.input,
        timeout_ms=tool.timeout_ms,
    )

    trace_id = request.headers.get("x-trace-id", "")

    if runtime_result.status == "timeout":
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="tool timeout",
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
    )