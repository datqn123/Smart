"""LangGraph Task002 routing & retry (offline)."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from app.config.graph_settings import GraphSettings, load_graph_settings
from app.graph import compile_agent_graph, default_initial_state
from app.graph.deps import GraphDeps
from app.graph.nodes.sql_pipeline import _benign_sql_review_issue
from app.graph.retry import can_regen_sql
from app.graph.sql_executor import StubSqlExecutor
from app.graph.state import AgentState
from app.graph.streaming import iter_graph_stream
from app.graph.validate_sql import validate_sql_deterministic
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


def _deps_chat() -> GraphDeps:
    reg = LlmRegistry()
    fake = FakeLlmClient()
    reg.register("default", fake)
    reg.register("intent", fake)
    reg.register("chat", fake)
    return GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
    )


def test_route_general_chat() -> None:
    deps = _deps_chat()
    g = compile_agent_graph(deps, use_checkpointer=False)
    base = default_initial_state()
    base["messages"] = [HumanMessage(content="xin chào")]
    out = g.invoke(base)
    assert out.get("final_answer")


def test_route_sql_happy_path(monkeypatch: pytest.MonkeyPatch, patch_pg_schema_v1: None) -> None:
    monkeypatch.delenv("SQL_ALLOWED_TABLES", raising=False)
    reg = LlmRegistry()
    reg.register(
        "default",
        FakeLlmClient(reply="SELECT id FROM customers LIMIT 10"),
    )
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", FakeLlmClient(reply="SELECT id FROM customers LIMIT 10"))
    reg.register("sql_review", FakeLlmClient())
    reg.register("chat", FakeLlmClient())
    reg.register("summarize", FakeLlmClient(reply="stub row _stub=1 returned."))
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(sql_allowed_tables=None),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    base = default_initial_state()
    base["messages"] = [HumanMessage(content="đếm đơn")]
    out = g.invoke(base)
    assert out.get("final_answer")
    assert "stub" in out["final_answer"].lower() or "_stub" in out["final_answer"]


def test_benign_sql_review_issue_limit_with_aggregate() -> None:
    msg = (
        "The LIMIT clause is redundant and logically incorrect when used with an aggregate "
        "function like SUM(), as it will always return a single row."
    )
    assert _benign_sql_review_issue(msg) is True
    assert _benign_sql_review_issue("Missing column revenue in schema") is False


def test_sql_review_retries_then_pass(monkeypatch: pytest.MonkeyPatch, patch_pg_schema_v1: None) -> None:
    monkeypatch.delenv("SQL_ALLOWED_TABLES", raising=False)
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient(reply="SELECT 1 LIMIT 10"))
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", FakeLlmClient(reply="SELECT 1 LIMIT 10"))
    reg.register(
        "sql_review",
        FakeLlmClient(sql_review_failures=2),
    )
    reg.register("chat", FakeLlmClient())
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    base = default_initial_state()
    base["messages"] = [HumanMessage(content="q")]
    out = g.invoke(base)
    assert out.get("final_answer")
    assert int(out.get("sql_attempt_count") or 0) >= 3


def test_max_attempts_sql_review(monkeypatch: pytest.MonkeyPatch, patch_pg_schema_v1: None) -> None:
    monkeypatch.delenv("SQL_ALLOWED_TABLES", raising=False)
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient(reply="SELECT 1 LIMIT 10"))
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", FakeLlmClient(reply="SELECT 1 LIMIT 10"))
    reg.register("sql_review", FakeLlmClient(sql_review_failures=99))
    reg.register("chat", FakeLlmClient())
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    out = g.invoke(
        {
            **default_initial_state(),
            "messages": [HumanMessage(content="q")],
        },
    )
    assert out.get("error_payload", {}).get("error") == "max_sql_attempts"
    assert int(out.get("sql_attempt_count") or 0) == 3


def test_validate_sql_blocks_insert() -> None:
    settings = GraphSettings()
    ok, detail, _, _ = validate_sql_deterministic("INSERT INTO t VALUES (1)", settings)
    assert ok is False
    assert detail


@pytest.mark.parametrize(
    "sql_snippet",
    [
        "UPDATE t SET x = 1",
        "DELETE FROM t",
        "ALTER TABLE t ADD COLUMN x INT",
        "TRUNCATE TABLE t",
    ],
)
def test_validate_sql_blocks_update_delete_alter_truncate(sql_snippet: str) -> None:
    settings = GraphSettings()
    ok, detail, _, _ = validate_sql_deterministic(sql_snippet, settings)
    assert ok is False and detail


def test_can_regen_sql_cap() -> None:
    s: AgentState = {"sql_attempt_count": 3}
    assert can_regen_sql(s) is False


def test_checkpoint_sqlite_smoke() -> None:
    settings = GraphSettings(checkpoint_sqlite_path=":memory:")
    deps = GraphDeps(
        llm_registry=_deps_chat().llm_registry,
        sql_executor=StubSqlExecutor(),
        settings=settings,
    )
    g = compile_agent_graph(deps, use_checkpointer=True)
    cfg = {"configurable": {"thread_id": "t1"}}
    g.invoke({**default_initial_state(), "messages": [HumanMessage(content="a")]}, cfg)
    g.invoke({**default_initial_state(), "messages": [HumanMessage(content="b")]}, cfg)


def test_graph_stream_yields() -> None:
    deps = _deps_chat()
    g = compile_agent_graph(deps, use_checkpointer=False)
    ev = list(
        iter_graph_stream(
            g,
            {**default_initial_state(), "messages": [HumanMessage(content="hi")]},
            correlation_id="cid",
        ),
    )
    assert len(ev) >= 1


def test_mask_sql_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MASK_SQL", "1")
    s = load_graph_settings()
    assert s.mask_sql is True
