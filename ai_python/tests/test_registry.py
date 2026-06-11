import pytest
from app.registry.registry import (TOOL_NAMES, REGISTRY, load_skill,
                                    render_api_tools, get_args_model,
                                    is_dispatchable)
from app.registry.args import SqlExecuteArgs, FinishArgs


def test_tool_names_unchanged():  # fact-registry-static (load_skill dirs)
    assert set(TOOL_NAMES) == {
        "sql_execute", "data_validator", "answer_composer", "session_manager"}


def test_registry_has_5_api_tools_3_dispatch_2_control():
    assert set(REGISTRY) == {"sql_execute", "data_validator", "answer_composer",
                             "finish", "request_clarification"}
    kinds = {n: s.kind for n, s in REGISTRY.items()}
    assert kinds["sql_execute"] == "dispatch"
    assert kinds["finish"] == "control"
    assert kinds["request_clarification"] == "control"


def test_is_dispatchable():
    assert is_dispatchable("sql_execute")
    assert not is_dispatchable("finish")          # control: SM-level, khong dispatch
    assert not is_dispatchable("rm_rf_database")


def test_render_api_tools_openai_format():
    tools = render_api_tools()
    assert len(tools) == 5
    by_name = {t["function"]["name"]: t for t in tools}
    assert by_name["sql_execute"]["type"] == "function"
    params = by_name["sql_execute"]["function"]["parameters"]
    assert "require" in params["properties"]
    assert "reasoning" in params["properties"]
    assert by_name["finish"]["function"]["parameters"]["properties"]["message"]
    assert by_name["sql_execute"]["function"]["description"]


def test_get_args_model():
    assert get_args_model("sql_execute") is SqlExecuteArgs
    assert get_args_model("finish") is FinishArgs
    with pytest.raises(KeyError):
        get_args_model("nope")


def test_load_skill_reads_md_fresh_each_call():
    first = load_skill("sql_execute")
    assert isinstance(first, str) and len(first) > 0


def test_load_skill_unknown_raises():
    with pytest.raises(KeyError):
        load_skill("nope")
