from dataclasses import dataclass


@dataclass
class AppError(Exception):
    error: str
    message: str
    status_code: int


class ToolNotFoundError(AppError):
    def __init__(self):
        super().__init__(
            error="tool_not_found",
            message="requested tool does not exist",
            status_code=404,
        )


class ToolVersionConflictError(AppError):
    def __init__(self):
        super().__init__(
            error="tool_version_conflict",
            message="tool version already exists",
            status_code=409,
        )


class PolicyDeniedError(AppError):
    def __init__(self, reason: str):
        super().__init__(
            error=reason,
            message=f"request denied by policy: {reason}",
            status_code=403,
        )


class ToolTimeoutError(AppError):
    def __init__(self):
        super().__init__(
            error="tool_timeout",
            message="tool execution exceeded timeout",
            status_code=408,
        )


class ToolOutputTooLargeError(AppError):
    def __init__(self):
        super().__init__(
            error="tool_output_too_large",
            message="tool stdout/stderr exceeded platform limit",
            status_code=413,
        )


class ExecutionNotFoundError(AppError):
    def __init__(self):
        super().__init__(
            error="execution_not_found",
            message="requested execution record does not exist",
            status_code=404,
        )