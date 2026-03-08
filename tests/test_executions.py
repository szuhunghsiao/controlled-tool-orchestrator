import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_execute_echo_tool_success(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create_payload = {
            "name": "echo_exec",
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

        r1 = await ac.post("/tools", json=create_payload)
        assert r1.status_code == 201, r1.text

        exec_payload = {
            "tool_name": "echo_exec",
            "tool_version": "v1",
            "input": {"text": "hello"},
        }

        r2 = await ac.post(
            "/executions",
            json=exec_payload,
            headers={"x-trace-id": "t-exec-1"},
        )
        assert r2.status_code == 200, r2.text

        body = r2.json()
        assert body["status"] == "succeeded"
        assert body["exit_code"] == 0
        assert body["output"] == {"echoed": "hello"}
        assert body["trace_id"] == "t-exec-1"


@pytest.mark.asyncio
async def test_execute_tool_not_found(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        exec_payload = {
            "tool_name": "missing_tool",
            "tool_version": "v1",
            "input": {"text": "hello"},
        }

        r = await ac.post("/executions", json=exec_payload)
        assert r.status_code == 404
        body = r.json()
        assert body["error"] == "tool_not_found"
