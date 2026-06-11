import pytest
from app.graph.dispatcher import dispatch, DispatchError


def test_dispatch_always_includes_raw_require(monkeypatch):  # fact-dispatcher
    captured = {}

    def fake_invoke(tool_name, payload, *, llm, deps):
        captured["tool_name"] = tool_name
        captured["payload"] = payload
        return {"output": {"ok": True}, "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.dispatcher._invoke_subgraph", fake_invoke)
    out = dispatch("sql_execute", raw_require="REQ", upstream_data={"x": 1},
                   llm=None, deps={})
    assert captured["tool_name"] == "sql_execute"
    assert captured["payload"]["raw_require"] == "REQ"
    assert captured["payload"]["upstream_data"] == {"x": 1}
    assert out["valid"] is True


def test_dispatch_passes_memory_summary_into_payload(monkeypatch):
    captured = {}

    def fake_invoke(tool_name, payload, *, llm, deps):
        captured.update(payload)
        return {"output": {}, "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.dispatcher._invoke_subgraph", fake_invoke)
    dispatch("sql_execute", raw_require="r", upstream_data={}, llm=None, deps={},
             memory_summary="tom tat")
    assert captured["memory_summary"] == "tom tat"


def test_dispatch_memory_summary_default_none(monkeypatch):
    captured = {}

    def fake_invoke(tool_name, payload, *, llm, deps):
        captured.update(payload)
        return {"output": {}, "valid": True, "validation_error": None}

    monkeypatch.setattr("app.graph.dispatcher._invoke_subgraph", fake_invoke)
    dispatch("sql_execute", raw_require="r", upstream_data={}, llm=None, deps={})
    assert captured["memory_summary"] is None


def test_dispatch_rejects_unregistered_tool():  # fact-registry-static
    with pytest.raises(DispatchError):
        dispatch("rm_rf", raw_require="R", upstream_data={}, llm=None, deps={})


def test_dispatch_blocks_composer_before_validator_pass():  # fact-validator-before
    with pytest.raises(DispatchError):
        dispatch("answer_composer", raw_require="R", upstream_data={},
                 llm=None, deps={}, validator_passed=False)
