from typing import Any

from app.policy.rules import (
    PolicyDecision,
    rule_input_size_limit,
    rule_runtime_allowed,
    rule_tool_active,
)


def evaluate(tool, tool_input: dict[str, Any], *, max_input_bytes: int) -> PolicyDecision:
    for rule in (rule_tool_active, rule_runtime_allowed):
        d = rule(tool)
        if not d.allowed:
            return d

    d = rule_input_size_limit(tool_input, max_bytes=max_input_bytes)
    if not d.allowed:
        return d

    return PolicyDecision(allowed=True)
