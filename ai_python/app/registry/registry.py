from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from pydantic import BaseModel
from app.registry.args import (ClarifyArgs, ComposerArgs, FinishArgs,
                               SqlExecuteArgs, ValidatorArgs)

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"

# Thu muc tool co skill.md (load_skill). session_manager khong phai API tool.
TOOL_NAMES = ("session_manager", "sql_execute", "data_validator", "answer_composer")


@dataclass(frozen=True)
class ToolSpec:
    """Nguon chan ly duy nhat cho 1 tool: mo ta cho LLM + schema args + loai."""
    description: str
    args_model: type[BaseModel]
    kind: str  # "dispatch" (co subgraph) | "control" (SM-level)


REGISTRY: dict[str, ToolSpec] = {
    "sql_execute": ToolSpec(
        "Sinh SQL read-only tu yeu cau va chay tren DB de lay du lieu ERP.",
        SqlExecuteArgs, kind="dispatch"),
    "data_validator": ToolSpec(
        "Kiem tra data vua lay co du/dung de tra loi yeu cau khong. "
        "BAT BUOC chay va pass truoc answer_composer.",
        ValidatorArgs, kind="dispatch"),
    "answer_composer": ToolSpec(
        "Soan cau tra loi cuoi cho user (lich su, du thong tin, co 'Gợi ý:'). "
        "Chi goi sau khi data_validator pass.",
        ComposerArgs, kind="dispatch"),
    "finish": ToolSpec(
        "Ket thuc phien va gui message cuoi (chao hoi/ngoai pham vi/da co answer).",
        FinishArgs, kind="control"),
    "request_clarification": ToolSpec(
        "Hoi lai user khi yeu cau mo ho, thieu thong tin de truy van.",
        ClarifyArgs, kind="control"),
}


def is_dispatchable(tool_name: str) -> bool:
    spec = REGISTRY.get(tool_name)
    return spec is not None and spec.kind == "dispatch"


def get_args_model(tool_name: str) -> type[BaseModel]:
    return REGISTRY[tool_name].args_model     # KeyError neu tool la


def render_api_tools() -> list[dict]:
    """OpenAI tools format tu REGISTRY — nguon duy nhat SM nhin thay."""
    return [{"type": "function",
             "function": {"name": name, "description": spec.description,
                          "parameters": spec.args_model.model_json_schema()}}
            for name, spec in REGISTRY.items()]


def load_skill(tool_name: str) -> str:
    """Doc skill.md MOI LAN goi (khong cache) — nen tang cho reload-on-retry.
    Neu co schema.md cung thu muc, tu dong concat vao sau skill.md."""
    if tool_name not in TOOL_NAMES:
        raise KeyError(f"unknown tool: {tool_name}")
    tool_dir = _TOOLS_DIR / tool_name
    content = (tool_dir / "skill.md").read_text(encoding="utf-8")
    schema_path = tool_dir / "schema.md"
    if schema_path.exists():
        content = content + "\n\n" + schema_path.read_text(encoding="utf-8")
    return content
