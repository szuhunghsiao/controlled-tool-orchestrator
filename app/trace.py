import uuid


def ensure_trace_id(incoming: str | None) -> str:
    if incoming and incoming.strip():
        return incoming.strip()
    return uuid.uuid4().hex
