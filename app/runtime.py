import asyncio
import json
import sys
from dataclasses import dataclass


@dataclass
class RuntimeResult:
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    output: dict | None


async def run_subprocess_tool(
    *,
    entrypoint: str,
    tool_input: dict,
    timeout_ms: int,
) -> RuntimeResult:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        entrypoint,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdin_bytes = json.dumps(tool_input).encode("utf-8")
    timeout_sec = timeout_ms / 1000

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(stdin_bytes),
            timeout=timeout_sec,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return RuntimeResult(
            status="timeout",
            exit_code=None,
            stdout="",
            stderr="process timed out",
            output=None,
        )

    stdout = stdout_bytes.decode("utf-8")
    stderr = stderr_bytes.decode("utf-8")

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
        )

    return RuntimeResult(
        status="failed",
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        output=None,
    )