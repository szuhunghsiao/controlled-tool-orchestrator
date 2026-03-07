from app.policy.rules import (
    PolicyViolation,
    rule_input_size_limit,
    rule_runtime_allowed,
    rule_tool_must_be_active,
)


def evaluate(tool, tool_input):
    rules = [
        rule_tool_must_be_active,
        rule_runtime_allowed,
    ]

    for rule in rules:
        rule(tool)

    rule_input_size_limit(tool_input)