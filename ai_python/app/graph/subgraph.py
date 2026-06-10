from __future__ import annotations
from typing import Callable
from langgraph.graph import StateGraph, START, END
from app.graph.state import ToolState
from app.registry import registry as _registry

ExecuteFn = Callable[..., dict]
ValidateFn = Callable[[ToolState], "tuple[bool, str | None]"]
LoadSkillFn = Callable[[str], str]


def build_tool_subgraph(*, tool_name: str, execute: ExecuteFn,
                        self_validate: ValidateFn,
                        load_skill: LoadSkillFn | None = None):
    """Rap subgraph [load_skill -> execute -> self_validate] cho 1 tool.

    - load_skill LUON la node dau, doc .md moi lan (fact-tool-subgraph).
    - self_validate chay cuoi, kiem output truoc khi tra (fact-tool-subgraph).
    - Subgraph chay lai tu dau khi retry => .md doc lai (fact-retry-reload).
    Deps runtime (llm + executor...) truyen qua config['configurable'].
    """
    _load = load_skill or _registry.load_skill

    def load_skill_node(state: ToolState) -> dict:
        return {"skill": _load(tool_name), "attempt": state["attempt"] + 1}

    def execute_node(state: ToolState, config) -> dict:
        cfg = config.get("configurable", {})
        deps = {k: v for k, v in cfg.items() if k != "llm"}
        output = execute(state, llm=cfg.get("llm"), **deps)
        return {"output": output}

    def validate_node(state: ToolState) -> dict:
        ok, err = self_validate(state)
        return {"valid": ok, "validation_error": err}

    g = StateGraph(ToolState)
    g.add_node("load_skill", load_skill_node)
    g.add_node("execute", execute_node)
    g.add_node("self_validate", validate_node)
    g.add_edge(START, "load_skill")
    g.add_edge("load_skill", "execute")
    g.add_edge("execute", "self_validate")
    g.add_edge("self_validate", END)
    return g.compile()
