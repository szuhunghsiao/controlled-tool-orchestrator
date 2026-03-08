# Controlled Tool Orchestrator
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-green)
![Database](https://img.shields.io/badge/database-SQLite-lightgrey)
![Testing](https://img.shields.io/badge/tests-pytest-yellow)

A production-style tool execution platform built with **Python + FastAPI + SQLite**, designed to demonstrate core AI platform / backend infrastructure concepts without relying on LLMs or Docker.

## Overview

Controlled Tool Orchestrator is a minimal but structured execution platform that supports:

- Tool registry
- Policy enforcement
- Subprocess-based execution runtime
- Timeout control
- Structured audit logging
- Trace ID propagation
- Error taxonomy
- Replay capability

The project is intentionally designed to be:

- **Fully understandable**
- **Locally runnable**
- **Incrementally extensible**
- **Production-inspired but lightweight**

This project focuses on execution governance and platform design rather than model orchestration.

---

## Why this project exists

In many AI platform or agent platform systems, execution is not just about "running code." A production system also needs to answer:

- What tools are registered?
- Which versions are active?
- Is a request allowed to run?
- What happened during execution?
- How do we trace a failure?
- Can we replay a historical execution?

This project implements those concerns in a simple but structured architecture.

---

## Features

### 1. Tool Registry
Tools are registered with:

- name
- version
- runtime
- entrypoint
- timeout
- input schema
- active status

This separates **tool definition** from **tool execution**.

### 2. Runtime Execution
Tools are executed as isolated local subprocesses using a simple contract:

- input passed through `stdin` as JSON
- output returned through `stdout`
- non-zero exit codes treated as failures
- timeout enforced by the orchestrator

### 3. Policy Enforcement
Requests are checked before execution:

- tool must be active
- runtime must be allowed
- input size must stay within platform limits

### 4. Structured Audit Logging
Every execution is recorded with:

- tool identity and version
- runtime metadata
- structured input/output
- stdout/stderr
- latency
- trace ID
- status and error code
- timestamp

### 5. Error Taxonomy
The API exposes stable, machine-readable errors such as:

- `tool_not_found`
- `tool_timeout`
- `tool_output_too_large`
- `input_too_large`
- `tool_version_conflict`
- `execution_not_found`

### 6. Replay Capability
Historical executions can be replayed using:

- original tool name/version
- original input payload
- replay lineage via `replay_of_execution_id`
- replay reason metadata

---

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy (async)
- SQLite
- pytest
- httpx
- Ruff

---

## Architecture

```text
Client
  ↓
FastAPI API Layer
  ↓
Tool Lookup (Registry)
  ↓
Policy Engine
  ↓
Runtime Executor
  ↓
Subprocess Tool
  ↓
Audit Logging (SQLite)
```

Core modules:

- app/api/tools.py — tool registry APIs
- app/api/executions.py — execution and replay APIs
- app/runtime.py — subprocess runtime
- app/policy/ — policy engine and rules
- app/audit.py — execution record creation
- app/errors.py — unified error taxonomy
- app/models.py — database schema

```
.
├── app
│   ├── api
│   │   ├── executions.py
│   │   ├── health.py
│   │   └── tools.py
│   ├── policy
│   │   ├── engine.py
│   │   └── rules.py
│   ├── audit.py
│   ├── db.py
│   ├── deps.py
│   ├── errors.py
│   ├── logging.py
│   ├── main.py
│   ├── migrations.py
│   ├── models.py
│   ├── runtime.py
│   ├── schemas.py
│   ├── settings.py
│   └── trace.py
├── tool_impls
│   ├── adder.py
│   └── echo.py
├── tests
│   ├── conftest.py
│   ├── test_audit.py
│   ├── test_executions.py
│   ├── test_health.py
│   ├── test_policy.py
│   ├── test_replay.py
│   └── test_tools.py
└── pyproject.toml
```

## Getting Start
1. Create environment
```Bash
conda create -n cto python=3.12 -y
conda activate cto
```
2. Install dependencies
```Bash
pip install -U pip
pip install -e ".[dev]"
```
3. Run the server
```Bash
uvicorn app.main:app --reload --port 8000
```
4. Run tests
```Bash
pytest -q
```
## Example API Flow
### Register a tool
```Bash
curl -X POST http://127.0.0.1:8000/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "echo",
    "version": "v1",
    "description": "echo tool",
    "runtime": "subprocess-v1",
    "entrypoint": "tool_impls/echo.py",
    "timeout_ms": 1000,
    "input_schema": {
      "type": "object",
      "properties": {
        "text": {"type": "string"}
      }
    }
  }'
```
Execute a tool
```Bash
curl -X POST http://127.0.0.1:8000/executions \
  -H "Content-Type: application/json" \
  -H "x-trace-id: trace-123" \
  -d '{
    "tool_name": "echo",
    "tool_version": "v1",
    "input": {
      "text": "hello world"
    }
  }'
```
Replay an execution
```Bash
curl -X POST http://127.0.0.1:8000/executions/1/replay \
  -H "Content-Type: application/json" \
  -H "x-trace-id: trace-replay-1" \
  -d '{
    "reason": "manual_debug"
  }'
```
Example Error Response
```json
{
  "error": "tool_not_found",
  "message": "requested tool does not exist",
  "trace_id": "trace-123"
}
```

## Design Highlights
### Separation of concerns
The project separates:
- registry
- policy
- runtime
- audit
- error handling
- replay

This keeps the execution path understandable and extensible.
### Explicit execution boundary
Tools are executed as subprocesses instead of in-process funciton calls, which makes timeout handling, isolation, and replay semantics celarer.
### Self-contained audit records
Execution records intentionally denormalize runtime metadata suh as runtime and entrypoint so historical records remain useful even if the registry changes later.
### Stable machine-readable errors
The platform defines explicit application error codes rather than returning ad hoc error strings.

## Tradeoffs
### Why SQLite?
SQLite keeps the project simple and fully local, while still demonstrating relational modeling, audit persistence, and queryable execution history.
### Why no Docker?
The goal is clarity and portability. Subprocess execution provides a simpler isolation boundary for learning and demonstration purposes.
### Why no LLM?
This project is focused on execution governance and platform mechanics, not prompt orchestration.

## Future Improvements
- Replace create_all() with Alembic migrations

- Add actor/user identity and authorization context

- Add per-tool concurrency limits

- Add stdout/stderr truncation strategy

- Add batch replay workflows

- Add metrics dashboard and aggregated execution stats

- Add stricter sandboxing beyond subprocess isolation

- Replace SQLite with Postgres for multi-user or higher-scale scenarios