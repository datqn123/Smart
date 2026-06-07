"""Harness data validator tool for business-semantic row checks."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.harness.tool_registry import ToolManifest, ToolResult, TurnContext


class DataValidatorOutput(BaseModel):
    ok: bool
    issues: list[str] = Field(default_factory=list)
    severity: str = "info"


class DataValidatorTool:
    manifest = ToolManifest(
        name="data_validator",
        description="Validate ERP rows against required data and basic business constraints.",
        args_schema='{"rows":"list","required_data":"list[str]"}',
    )

    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        _ = ctx
        rows = args.get("rows") or []
        required_data = [str(item) for item in (args.get("required_data") or [])]
        issues: list[str] = []
        if required_data:
            available = set()
            for row in rows if isinstance(rows, list) else []:
                if isinstance(row, dict):
                    available.update(str(key) for key in row)
            for key in required_data:
                if key not in available:
                    issues.append(f"missing_column:{key}")
        for row in rows if isinstance(rows, list) else []:
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
        return ToolResult(
            ok=output.ok,
            output=output.model_dump(mode="json"),
            observation_text=observation,
        )
