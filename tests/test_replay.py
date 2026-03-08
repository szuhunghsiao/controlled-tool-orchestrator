import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_replay_execution_creates_new_record_with_lineage(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        tool_payload = {
            "name": "echo_replay",
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
            "tool_name": "echo_replay",
            "tool_version": "v1",
            "input": {"text": "hello replay"},
        }

        r2 = await ac.post(
            "/executions",
            json=exec_payload,
            headers={"x-trace-id": "trace-original-1"},
        )
        assert r2.status_code == 200, r2.text

        original_list = await ac.get("/executions?trace_id=trace-original-1")
        assert original_list.status_code == 200, original_list.text
        original_items = original_list.json()["items"]
        assert len(original_items) == 1

        original_id = original_items[0]["id"]

        replay_payload = {"reason": "manual_debug"}
        r3 = await ac.post(
            f"/executions/{original_id}/replay",
            json=replay_payload,
            headers={"x-trace-id": "trace-replay-1"},
        )
        assert r3.status_code == 200, r3.text
        replay_body = r3.json()
        assert replay_body["status"] == "succeeded"
        assert replay_body["output"] == {"echoed": "hello replay"}

        replay_list = await ac.get("/executions?trace_id=trace-replay-1")
        assert replay_list.status_code == 200, replay_list.text
        replay_items = replay_list.json()["items"]
        assert len(replay_items) == 1

        replay_record = replay_items[0]
        assert replay_record["replay_of_execution_id"] == original_id
        assert replay_record["replay_reason"] == "manual_debug"
        assert replay_record["input_json"] == {"text": "hello replay"}
        assert replay_record["output_json"] == {"echoed": "hello replay"}


@pytest.mark.asyncio
async def test_replay_missing_execution_returns_404(app):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(
            "/executions/999/replay",
            json={"reason": "manual_debug"},
            headers={"x-trace-id": "trace-missing-replay"},
        )
        assert r.status_code == 404
        body = r.json()
        assert body["error"] == "execution_not_found"
