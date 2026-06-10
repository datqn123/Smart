from app.graph.subgraph import build_tool_subgraph
from app.graph.state import new_tool_state


def test_subgraph_runs_nodes_in_order_load_execute_validate(monkeypatch):
    order = []

    def fake_load(tool_name):
        order.append("load")
        return "SKILL-CONTENT"

    def fake_execute(state, *, llm, **kw):
        order.append("execute")
        assert state["skill"] == "SKILL-CONTENT"   # load chay truoc execute
        return {"value": 42}

    def fake_validate(state):
        order.append("validate")
        assert state["output"] == {"value": 42}     # execute chay truoc validate
        return True, None

    graph = build_tool_subgraph(
        tool_name="dummy", execute=fake_execute, self_validate=fake_validate,
        load_skill=fake_load)
    out = graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"),
                       config={"configurable": {"llm": None}})
    assert order == ["load", "execute", "validate"]
    assert out["output"] == {"value": 42}
    assert out["valid"] is True
    assert out["attempt"] == 1


def test_subgraph_reloads_skill_on_reinvoke():  # fact-retry-reload
    loads = []
    graph = build_tool_subgraph(
        tool_name="dummy",
        execute=lambda s, *, llm, **k: {"v": 1},
        self_validate=lambda s: (True, None),
        load_skill=lambda tn: loads.append(tn) or "MD")
    cfg = {"configurable": {"llm": None}}
    graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"), config=cfg)
    graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"), config=cfg)
    assert loads == ["dummy", "dummy"]   # doc .md lai moi lan invoke


def test_self_validate_failure_marks_invalid():
    graph = build_tool_subgraph(
        tool_name="dummy",
        execute=lambda s, *, llm, **k: {"bad": True},
        self_validate=lambda s: (False, "output sai schema"),
        load_skill=lambda tn: "MD")
    out = graph.invoke(new_tool_state(tool_name="dummy", raw_require="R"),
                       config={"configurable": {"llm": None}})
    assert out["valid"] is False
    assert out["validation_error"] == "output sai schema"
