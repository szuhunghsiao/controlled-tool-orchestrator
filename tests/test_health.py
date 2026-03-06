import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.asyncio
async def test_healthz_ok():
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/healthz", headers={"x-trace-id": "t-health-1"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}
        assert r.headers["x-trace-id"] == "t-health-1"


@pytest.mark.asyncio
async def test_readyz_ok():
    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/readyz")
        assert r.status_code == 200
        assert r.json() == {"ready": True}
        assert "x-trace-id" in r.headers
