from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session