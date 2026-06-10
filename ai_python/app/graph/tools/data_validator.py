"""Harness data validator tool for business-semantic row checks."""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from app.graph.tools._result_ref import rows_from_args_or_ref
from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext

logger = logging.getLogger(__name__)


class DataValidatorOutput(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)
    severity: str = "info"


class DataValidatorTool:
    manifest = ToolManifest(
        name="data_validator",
        description="Validate ERP rows against required data and basic business constraints.",
        args_schema='{"rows":"list","required_data":"list[str]"}',
        capability="data_validate",
        output_schema='{"ok": "bool", "issues": "list[str]", "severity": "string"}',
        when_to_use="After a data query, before composing an answer or artifact, to confirm rows satisfy the question.",
        when_not_to_use="No rows have been fetched yet.",
        risk_level="low",
        side_effect_class="read_only",
        consumes=("rows",),
        produces=("validation",),
        examples=("kiểm tra dữ liệu doanh thu có đủ kỳ", "xác nhận rows khớp yêu cầu"),
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        logger.info("tool_invoke_start tool=data_validator rows=%s required=%s",
                    len(args.get("rows", [])), args.get("required_data"))
        _start = time.monotonic()
        rows, error = rows_from_args_or_ref(args, ctx)
        if error:
            _result = ToolResult(ok=False, output={}, observation_text=error, error_message=error)
            logger.info("tool_invoke_end tool=data_validator ok=%s latency_ms=%.0f issues=%s",
                        _result.ok, (time.monotonic() - _start) * 1000, len(_result.output.get("issues", [])))
            return _result
        required_data = [str(item) for item in (args.get("required_data") or [])]
        issues: list[str] = []
        if required_data:
            available = set()
            for row in rows:
                if isinstance(row, dict):
                    available.update(str(key) for key in row)
            for key in required_data:
                if key not in available:
                    issues.append(f"missing_column:{key}")
        for row in rows:
            if not isinstance(row, dict):
                continue
            for value in row.values():
                if isinstance(value, (int, float)) and value < 0:
                    issues.append("negative_value")
                    break
        severity = "fail" if issues else "info"
        output = DataValidatorOutput(ok=not issues, issues=issues, severity=severity)
        observation = (
            "Dữ liệu không đạt kiểm tra nghiệp vụ: " + ", ".join(issues)
            if issues
            else "Dữ liệu đạt kiểm tra nghiệp vụ."
        )
        result = ToolResult(
            ok=output.ok,
            output=output.model_dump(mode="json"),
            observation_text=observation,
        )
        logger.info("tool_invoke_end tool=data_validator ok=%s latency_ms=%.0f issues=%s",
                    result.ok, (time.monotonic() - _start) * 1000, len(result.output.get("issues", [])))
        return result
