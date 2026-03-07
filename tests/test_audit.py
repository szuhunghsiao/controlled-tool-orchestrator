import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_execution_record_created_for_success(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        tool_payload = {
            "name": "echo_audit",
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

        r1 = await ac.post("/tools", json=tool_payload)
        assert r1.status_code == 201, r1.text

        exec_payload = {
            "tool_name": "echo_audit",
            "tool_version": "v1",
            "input": {"text": "hello audit"},
        }

        r2 = await ac.post(
            "/executions",
            json=exec_payload,
            headers={"x-trace-id": "trace-audit-1"},
        )
        assert r2.status_code == 200, r2.text

        r3 = await ac.get("/executions?trace_id=trace-audit-1")
        assert r3.status_code == 200, r3.text

        body = r3.json()
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["tool_name"] == "echo_audit"
        assert item["tool_version"] == "v1"
        assert item["status"] == "succeeded"
        assert item["error_code"] is None
        assert item["input_json"] == {"text": "hello audit"}
        assert item["output_json"] == {"echoed": "hello audit"}
        assert item["trace_id"] == "trace-audit-1"

@pytest.mark.asyncio
async def test_execution_record_created_for_policy_denied(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        tool_payload = {
            "name": "echo_deny",
            "version": "v1",
            "description": "echo tool",
            "runtime": "subprocess-v1",
            "entrypoint": "tool_impls/echo.py",
            "timeout_ms": 1000,
            "input_schema": {"type": "object"},
        }

        r1 = await ac.post("/tools", json=tool_payload)
        assert r1.status_code == 201, r1.text

        big = {"text": "x" * 20000}
        exec_payload = {
            "tool_name": "echo_deny",
            "tool_version": "v1",
            "input": big,
        }

        r2 = await ac.post(
            "/executions",
            json=exec_payload,
            headers={"x-trace-id": "trace-deny-1"},
        )
        assert r2.status_code == 403, r2.text

        r3 = await ac.get("/executions?trace_id=trace-deny-1")
        assert r3.status_code == 200, r3.text

        body = r3.json()
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["status"] == "policy_denied"
        assert item["error_code"] == "input_too_large"
        assert item["trace_id"] == "trace-deny-1"