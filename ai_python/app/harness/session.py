from __future__ import annotations
import hashlib


def resolve_thread_id(user_id: str) -> str:
    """Map User_ID -> Thread_ID on dinh (stateless: hash, khong luu DB).
    Vong sau (memory) se thay bang lookup ben vung."""
    digest = hashlib.sha1(user_id.encode("utf-8")).hexdigest()[:16]
    return f"thread-{digest}"
