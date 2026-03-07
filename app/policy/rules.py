import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("cto.policy")


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str | None = None


def deny(reason: str) -> PolicyDecision:
    return PolicyDecision(allowed=False, reason=reason)


def allow() -> PolicyDecision:
    return PolicyDecision(allowed=True)


def rule_tool_active(tool) -> PolicyDecision:
    if not tool.is_active:
        return deny("tool_inactive")
    return allow()


def rule_runtime_allowed(tool) -> PolicyDecision:
    allowed = {"subprocess-v1"}
    if tool.runtime not in allowed:
        return deny("runtime_not_allowed")
    return allow()


def rule_input_size_limit(tool_input: dict[str, Any], max_bytes: int) -> PolicyDecision:
    raw = json.dumps(tool_input, ensure_ascii=False).encode("utf-8")
    input_bytes = len(raw)

    if input_bytes > max_bytes:
        logger.info(
            "policy_deny",
            extra={"reason": "input_too_large",
                "input_bytes": input_bytes,
                "max_bytes": max_bytes,
                },
        )
        return deny("input_too_large")
    return allow()