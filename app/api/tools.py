import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session
from app.models import Tool
from app.schemas import ToolCreate, ToolListResponse, ToolResponse

router = APIRouter(prefix="/tools", tags=["tools"])


def to_tool_response(tool: Tool) -> ToolResponse:
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        version=tool.version,
        description=tool.description,
        runtime=tool.runtime,
        entrypoint=tool.entrypoint,
        timeout_ms=tool.timeout_ms,
        input_schema=json.loads(tool.input_schema),
        is_active=tool.is_active,
        created_at=tool.created_at,
    )


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    payload: ToolCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ToolResponse:
    tool = Tool(
        name=payload.name,
        version=payload.version,
        description=payload.description,
        runtime=payload.runtime,
        entrypoint=payload.entrypoint,
        timeout_ms=payload.timeout_ms,
        input_schema=json.dumps(payload.input_schema),
        is_active=True,
    )

    session.add(tool)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="tool version already exists",
        )

    await session.refresh(tool)
    return to_tool_response(tool)


@router.get("", response_model=ToolListResponse)
async def list_tools(
    session: AsyncSession = Depends(get_db_session),
) -> ToolListResponse:
    result = await session.execute(select(Tool).order_by(Tool.name, Tool.version))
    tools = result.scalars().all()
    return ToolListResponse(items=[to_tool_response(tool) for tool in tools])


@router.get("/{name}/{version}", response_model=ToolResponse)
async def get_tool(
    name: str,
    version: str,
    session: AsyncSession = Depends(get_db_session),
) -> ToolResponse:
    result = await session.execute(
        select(Tool).where(Tool.name == name, Tool.version == version)
    )
    tool = result.scalar_one_or_none()

    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tool not found")

    return to_tool_response(tool)