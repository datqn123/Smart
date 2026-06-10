from __future__ import annotations
from typing import Any
from app.registry.registry import is_registered
from app.graph.subgraph import build_tool_subgraph
from app.graph.state import new_tool_state


class DispatchError(Exception):
    pass


def _load_tool_funcs(tool_name: str):
    import importlib
    mod = importlib.import_module(f"app.tools.{tool_name}")
    return mod.execute, mod.self_validate


def _invoke_subgraph(tool_name: str, payload: dict, *, llm, deps: dict) -> dict:
    execute, self_validate = _load_tool_funcs(tool_name)
    graph = build_tool_subgraph(tool_name=tool_name, execute=execute,
                                self_validate=self_validate)
    state = new_tool_state(tool_name=tool_name, raw_require=payload["raw_require"],
                           upstream_data=payload["upstream_data"])
    cfg = {"configurable": {"llm": llm, **deps}}
    final = graph.invoke(state, config=cfg)
    return {"output": final["output"], "valid": final["valid"],
            "validation_error": final["validation_error"]}


def dispatch(tool_name: str, *, raw_require: str, upstream_data: dict[str, Any],
             llm, deps: dict, validator_passed: bool = True) -> dict:
    """Map tool_name -> subgraph; payload LUON {raw_require, upstream_data}
    (fact-dispatcher). Chan answer_composer neu validator chua pass
    (fact-validator-before)."""
    if not is_registered(tool_name):
        raise DispatchError(f"tool chua dang ky: {tool_name}")
    if tool_name == "answer_composer" and not validator_passed:
        raise DispatchError("answer_composer khong duoc chay truoc data_validator pass")
    payload = {"raw_require": raw_require, "upstream_data": upstream_data}
    return _invoke_subgraph(tool_name, payload, llm=llm, deps=deps)
