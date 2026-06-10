from __future__ import annotations
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"

# Static registry. SM chi duoc goi tool co trong DISPATCHABLE.
TOOL_NAMES = ("session_manager", "sql_execute", "data_validator", "answer_composer")

# Mo ta nhet vao context SM (khong gom session_manager — SM khong tu goi minh).
DISPATCHABLE: dict[str, str] = {
    "sql_execute": "Sinh SQL read-only tu raw_require va chay tren DB de lay data.",
    "data_validator": "Kiem tra data cuoi co phu hop raw_require khong. BAT BUOC chay truoc answer_composer.",
    "answer_composer": "Soan cau tra loi cuoi cho user (lich su, du thong tin, goi y buoc tiep). Chi chay sau validator pass.",
}


def is_registered(tool_name: str) -> bool:
    return tool_name in DISPATCHABLE


def load_skill(tool_name: str) -> str:
    """Doc skill.md MOI LAN goi (khong cache) — nen tang cho reload-on-retry."""
    if tool_name not in TOOL_NAMES:
        raise KeyError(f"unknown tool: {tool_name}")
    path = _TOOLS_DIR / tool_name / "skill.md"
    return path.read_text(encoding="utf-8")


def render_tool_catalog() -> str:
    """Bang tool + mo ta de nhet vao prompt SM."""
    lines = ["Cac tool kha dung (chi duoc goi tool trong danh sach nay):"]
    for name, desc in DISPATCHABLE.items():
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)
