"""Observation contract (SRS-006 FR-12).

Every tool result returned to the Planner is converted into a bounded, sanitized
``ObservationEnvelope``: schema + counts + a small masked sample + an opaque
``result_ref`` handle. Full result sets, raw PII, raw SQL, stack traces, and
provider errors must never reach the Planner prompt.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from pydantic import BaseModel, Field

SAMPLE_LIMIT_DEFAULT = 20
_MESSAGE_MAX_CHARS = 600

# Column names whose values must be masked before entering an observation.
_SENSITIVE_KEY = re.compile(
    r"(password|passwd|token|secret|bearer|api[_-]?key|phone|mobile|email|"
    r"ssn|tax[_-]?id|salary|bank|card|cccd|cmnd)",
    re.IGNORECASE,
)
# Signals that an error string is leaking SQL / stack internals.
_SQL_LEAK = re.compile(r"\b(select|insert|update|delete|drop|from\s+\w|where\s+\w|join)\b", re.IGNORECASE)
_STACK_LEAK = re.compile(r"(traceback|file \"|line \d+|\.py\b|at 0x[0-9a-f]+)", re.IGNORECASE)


class ObservationEnvelope(BaseModel):
    """Safe planner-facing view of a tool result."""

    tool_name: str
    ok: bool
    error_kind: str | None = None
    message: str = ""
    schema_fields: list[dict[str, str]] = Field(default_factory=list)
    row_count: int | None = None
    aggregate_stats: dict[str, Any] = Field(default_factory=dict)
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    masked: bool = False
    truncated: bool = False
    result_ref: str | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    replan_required: bool = False
    failure_fingerprint: str | None = None

    def to_planner_text(self) -> str:
        if not self.ok:
            return f"{self.tool_name} (error/{self.error_kind or 'tool_error'}): {self.message}"
        head = f"{self.tool_name} (ok)"
        if self.row_count is not None:
            cols = ", ".join(f["name"] for f in self.schema_fields) or "-"
            flags = []
            if self.truncated:
                flags.append("truncated")
            if self.masked:
                flags.append("masked")
            flag_text = f" [{', '.join(flags)}]" if flags else ""
            ref = f" result_ref={self.result_ref}" if self.result_ref else ""
            return (
                f"{head}: row_count={self.row_count} columns=[{cols}]{flag_text}{ref} "
                f"sample={self.sample_rows[:3]}"
            )
        return f"{head}: {self.message}"


def _extract_rows(output: dict[str, Any]) -> list[dict[str, Any]] | None:
    if not isinstance(output, dict):
        return None
    rows = output.get("rows")
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    query_result = output.get("query_result")
    if isinstance(query_result, dict):
        nested = query_result.get("rows")
        if isinstance(nested, list):
            return [r for r in nested if isinstance(r, dict)]
    return None


def _mask_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    masked_any = False
    out: list[dict[str, Any]] = []
    for row in rows:
        new_row: dict[str, Any] = {}
        for key, value in row.items():
            if _SENSITIVE_KEY.search(str(key)):
                new_row[key] = "***"
                masked_any = True
            else:
                new_row[key] = value
        out.append(new_row)
    return out, masked_any


def _infer_schema(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not rows:
        return []
    first = rows[0]
    return [{"name": str(k), "type": type(v).__name__} for k, v in first.items()]


def _truncate(text: str) -> str:
    text = text or ""
    if len(text) > _MESSAGE_MAX_CHARS:
        return text[:_MESSAGE_MAX_CHARS] + "[truncated]"
    return text


def _classify_error(raw: str) -> str:
    low = (raw or "").lower()
    if "permission" in low or "quyền" in low or "policy" in low or "rbac" in low:
        return "policy_blocked"
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if "không có quyền" in low:
        return "policy_blocked"
    return "tool_error"


def _safe_error_message(kind: str) -> str:
    return {
        "policy_blocked": "Yêu cầu bị chặn bởi chính sách quyền truy cập.",
        "timeout": "Công cụ xử lý quá thời gian cho phép.",
        "tool_error": "Công cụ gặp lỗi khi xử lý yêu cầu.",
    }.get(kind, "Công cụ gặp lỗi khi xử lý yêu cầu.")


def failure_fingerprint(tool_name: str, raw_error: str) -> str:
    """Opaque, stable fingerprint of a failure for dedup (no raw content exposed)."""
    raw = f"{tool_name}|{(raw_error or '').strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def sanitize_error_text(raw: str) -> str:
    """Strip SQL/stack leaks from an error string; never echo raw internals."""
    if _SQL_LEAK.search(raw or "") or _STACK_LEAK.search(raw or ""):
        return _safe_error_message(_classify_error(raw))
    return _truncate(raw)


def build_observation(
    *,
    tool_name: str,
    tool_result: Any,
    ctx: Any,
    result_store: Any | None = None,
    sample_limit: int = SAMPLE_LIMIT_DEFAULT,
    output_meets_expect: bool = True,
) -> ObservationEnvelope:
    """Convert a ``ToolResult`` into a safe :class:`ObservationEnvelope`."""
    ok = bool(getattr(tool_result, "ok", False))
    raw_error = str(getattr(tool_result, "error_message", "") or getattr(tool_result, "observation_text", "") or "")

    if not ok:
        kind = _classify_error(raw_error)
        return ObservationEnvelope(
            tool_name=tool_name,
            ok=False,
            error_kind=kind,
            message=_safe_error_message(kind),
            replan_required=True,
            failure_fingerprint=failure_fingerprint(tool_name, raw_error),
        )

    output = getattr(tool_result, "output", None) or {}
    rows = _extract_rows(output)

    if rows is None:
        # Non-tabular result (e.g. answer text, guidance): no full data to hold.
        return ObservationEnvelope(
            tool_name=tool_name,
            ok=True,
            message=_truncate(str(getattr(tool_result, "observation_text", "") or "")),
            replan_required=not output_meets_expect,
        )

    row_count = len(rows)
    sample = rows[:sample_limit]
    masked_sample, masked = _mask_rows(sample)
    truncated = row_count > len(sample)

    result_ref: str | None = None
    if result_store is not None and rows:
        result_ref = result_store.put(tool_name=tool_name, data={"rows": rows}, ctx=ctx)

    return ObservationEnvelope(
        tool_name=tool_name,
        ok=True,
        schema_fields=_infer_schema(rows),
        row_count=row_count,
        sample_rows=masked_sample,
        masked=masked,
        truncated=truncated,
        result_ref=result_ref,
        message=_truncate(str(getattr(tool_result, "observation_text", "") or "")),
        replan_required=not output_meets_expect,
    )
