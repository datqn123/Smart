from app.graph.state import new_tool_state, new_session_state


def test_new_tool_state_defaults():
    st = new_tool_state(tool_name="sql_execute", raw_require="R",
                        upstream_data={"x": 1})
    assert st["tool_name"] == "sql_execute"
    assert st["raw_require"] == "R"
    assert st["upstream_data"] == {"x": 1}
    assert st["skill"] == ""
    assert st["output"] is None
    assert st["valid"] is False
    assert st["attempt"] == 0


def test_new_session_state_defaults():
    st = new_session_state(raw_require="R", thread_id="t1")
    assert st["raw_require"] == "R"
    assert st["thread_id"] == "t1"
    assert st["step_count"] == 0
    assert st["status"] == "running"
    assert st["tool_results"] == {}
    assert st["retry_counts"] == {}
    assert st["final_answer"] is None
    assert st["pending_clarification"] is None
