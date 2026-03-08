import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_policy_input_size_limit(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        tool_payload = {
            "name": "echo_policy",
            "version": "v1",
            "description": "echo tool",
            "runtime": "subprocess-v1",
            "entrypoint": "tool_impls/echo.py",
            "timeout_ms": 1000,
            "input_schema": {"type": "object"},
        }
        r1 = await ac.post("/tools", json=tool_payload)
        assert r1.status_code == 201, r1.text

        big = {"text": "x" * 20000}  # > 10KB
        exec_payload = {"tool_name": "echo_policy", "tool_version": "v1", "input": big}
        r2 = await ac.post("/executions", json=exec_payload)
        assert r2.status_code == 403
        body = r2.json()
        assert body["error"] == "input_too_large"
