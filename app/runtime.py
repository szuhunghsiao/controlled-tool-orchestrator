import asyncio
import json
import sys
import time
from dataclasses import dataclass


@dataclass
class RuntimeResult:
    status: str  # succeeded | failed | timeout | output_too_large
    exit_code: int | None
    stdout: str
    stderr: str
    output: dict | None
    latency_ms: int


async def run_subprocess_tool(
    *,
    entrypoint: str,
    tool_input: dict,
    timeout_ms: int,
    max_stdout_bytes: int,
    max_stderr_bytes: int,
) -> RuntimeResult:
    start = time.perf_counter()

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        entrypoint,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdin_bytes = json.dumps(tool_input, ensure_ascii=False).encode("utf-8")
    timeout_sec = timeout_ms / 1000

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(stdin_bytes),
            timeout=timeout_sec,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return RuntimeResult(
            status="timeout",
            exit_code=None,
            stdout="",
            stderr="process timed out",
            output=None,
            latency_ms=latency_ms,
        )

    # hard limit: output size
    if len(stdout_bytes) > max_stdout_bytes or len(stderr_bytes) > max_stderr_bytes:
        process.kill()
        await process.wait()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return RuntimeResult(
            status="output_too_large",
            exit_code=None,
            stdout="",
            stderr="stdout/stderr exceeded limit",
            output=None,
            latency_ms=latency_ms,
        )

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    latency_ms = int((time.perf_counter() - start) * 1000)

    if process.returncode == 0:
        parsed_output = None
        if stdout.strip():
            try:
                parsed_output = json.loads(stdout)
            except json.JSONDecodeError:
                parsed_output = None

        return RuntimeResult(
            status="succeeded",
            exit_code=process.returncode,
            stdout=stdout,
            stderr=stderr,
            output=parsed_output,
            latency_ms=latency_ms,
        )

    return RuntimeResult(
        status="failed",
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        output=None,
        latency_ms=latency_ms,
    )