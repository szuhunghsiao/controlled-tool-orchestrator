import json


class PolicyViolation(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def rule_tool_must_be_active(tool):
    if not tool.is_active:
        raise PolicyViolation("tool is inactive")


def rule_runtime_allowed(tool):
    allowed = {"subprocess-v1"}

    if tool.runtime not in allowed:
        raise PolicyViolation(f"runtime not allowed: {tool.runtime}")


def rule_input_size_limit(tool_input):
    raw = json.dumps(tool_input)

    if len(raw) > 10_000:
        raise PolicyViolation("input too large")