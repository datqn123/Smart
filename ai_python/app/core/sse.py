def sse_event(event: str, data: str) -> str:
    """Format one Server-Sent Event block (event + one or more data lines + trailing blank line)."""
    lines = data.splitlines() or [""]
    payload = [f"event: {event}"]
    payload.extend([f"data: {line}" for line in lines])
    payload.append("")
    return "\n".join(payload) + "\n"
