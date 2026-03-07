import pytest

from app.db import get_engine
from app.main import create_app
from app.models import Base


@pytest.fixture
async def app():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    return create_app()

# # tests/conftest.py
# import pytest
# from httpx import ASGITransport, AsyncClient

# from app.main import create_app
# from app.models import Base
# import app.db as dbmod
# from app.settings import settings

# @pytest.fixture
# async def app(tmp_path):
#     # 1) Each test use it's own sqlite file, isolate completely 
#     db_path = tmp_path / "test.db"
#     settings.database_url = f"sqlite+aiosqlite:///{db_path}"

#     # 2) clear global engine/session factory
#     if dbmod._engine is not None:
#         await dbmod._engine.dispose()
#     dbmod._engine = None
#     dbmod._async_session_factory = None

#     # 3) Build schema (not relaying FastAPI lifespan)
#     engine = dbmod.get_engine()
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

#     # 4) recall app
#     yield create_app()

#     # 5) avoid warning / resource leak
#     if dbmod._engine is not None:
#         await dbmod._engine.dispose()
#     dbmod._engine = None
#     dbmod._async_session_factory = None


# @pytest.fixture
# async def client(app):
#     transport = ASGITransport(app=app) 
#     async with AsyncClient(transport=transport, base_url="http://test") as ac:
#         yield ac