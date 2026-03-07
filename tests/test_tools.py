import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_create_and_get_tool(app):
    # app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "name": "echo",
            "version": "v1",
            "description": "echo tool",
            "runtime": "subprocess-v1",
            "entrypoint": "tool_impls/echo.py",
            "timeout_ms": 1000,
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
        }

        r = await ac.post("/tools", json=payload, headers={"x-trace-id": "t-tool-1"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "echo"
        assert body["version"] == "v1"
        assert body["runtime"] == "subprocess-v1"
        assert body["input_schema"]["type"] == "object"
        assert r.headers["x-trace-id"] == "t-tool-1"

        r2 = await ac.get("/tools/echo/v1")
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["name"] == "echo"
        assert body2["version"] == "v1"


@pytest.mark.asyncio
async def test_list_tools(app):
    # app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "name": "adder",
            "version": "v1",
            "description": "adder tool",
            "runtime": "subprocess-v1",
            "entrypoint": "tool_impls/echo.py",
            "timeout_ms": 2000,
            "input_schema": {
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            },
        }

        r = await ac.post("/tools", json=payload)
        assert r.status_code == 201, r.text

        r2 = await ac.get("/tools")
        assert r2.status_code == 200
        body = r2.json()
        assert "items" in body
        assert len(body["items"]) >= 1


@pytest.mark.asyncio
async def test_duplicate_tool_version_returns_409(app):
    # app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "name": "echo_dup",
            "version": "v1",
            "description": "echo tool",
            "runtime": "subprocess-v1",
            "entrypoint": "tool_impls/echo.py",
            "timeout_ms": 1000,
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
            },
        }

        r1 = await ac.post("/tools", json=payload)
        assert r1.status_code == 201, r1.text

        r2 = await ac.post("/tools", json=payload)
        assert r2.status_code == 409, r2.text
        assert r2.json()["detail"] == "tool version already exists"