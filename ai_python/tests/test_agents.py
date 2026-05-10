"""Task 3 / Agents v1 — unit tests."""

from __future__ import annotations

import logging

import pytest
from langchain_core.messages import HumanMessage

from app.config.graph_settings import GraphSettings
from app.graph import compile_agent_graph, default_initial_state
from app.graph.correlation import correlation_scope, setup_correlation_logging
from app.graph.dbmeta import FileSchemaLoader, SchemaArtifact
from app.graph.deps import GraphDeps
from app.graph.feedback import append_feedback, empty_feedback, render_for_prompt
from app.graph.registry import normalize_intent
from app.graph.sql_executor import StubSqlExecutor
from app.graph.validate_sql import validate_sql_deterministic
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


# --- DBM loader ---


def test_file_schema_loader_default_dir_loads_v1() -> None:
    loader = FileSchemaLoader(None)
    art = loader.load("v1")
    assert isinstance(art, SchemaArtifact)
    assert art.schema_version == "v1"
    names = {t.name.lower() for t in art.tables}
    assert {"customers", "orders", "products"} <= names


def test_file_schema_loader_missing_version_raises() -> None:
    loader = FileSchemaLoader(None)
    with pytest.raises(FileNotFoundError):
        loader.load("does-not-exist-xyz")


def test_allowlist_table_names_lowercase() -> None:
    loader = FileSchemaLoader(None)
    art = loader.load("v1")
    al = art.allowlist_table_names()
    assert "customers" in al and all(x == x.lower() for x in al)


# --- feedback ---


def test_append_feedback_isolated_buckets() -> None:
    state: dict = {"validation_feedback": empty_feedback()}
    fb1 = append_feedback(state, "policy", "missing LIMIT")
    state["validation_feedback"] = fb1
    fb2 = append_feedback(state, "exec", "timeout")
    assert fb2["policy"] == ["missing LIMIT"]
    assert fb2["exec"] == ["timeout"]
    assert fb2["intent_review"] == [] and fb2["result"] == []


def test_render_for_prompt_skips_empty_buckets() -> None:
    fb = empty_feedback()
    fb["policy"] = ["x"]
    fb["attempts"] = 2
    out = render_for_prompt(fb)
    assert "[policy] x" in out and "attempts=2" in out
    assert "[intent_review]" not in out and "[exec]" not in out


# --- validate_sql ---


def test_validate_sql_select_only_blocks_drop() -> None:
    s = GraphSettings()
    ok, detail, _, _ = validate_sql_deterministic("DROP TABLE t", s)
    assert ok is False and detail


def test_validate_sql_blocks_multi_statement() -> None:
    s = GraphSettings()
    ok, detail, _, _ = validate_sql_deterministic("SELECT 1; SELECT 2;", s)
    assert ok is False and "single" in (detail or "").lower()


def test_validate_sql_limit_inject_hybrid() -> None:
    s = GraphSettings(sql_limit_max=42)
    ok, detail, sanitized, notes = validate_sql_deterministic("SELECT id FROM customers", s)
    assert ok is True
    assert "LIMIT 42" in (sanitized or "").upper()
    assert any("limit" in n.lower() for n in notes)


def test_validate_sql_allowlist_blocks_other_tables() -> None:
    s = GraphSettings()
    al = {"customers"}
    ok, detail, _, _ = validate_sql_deterministic(
        "SELECT * FROM secret_table LIMIT 10",
        s,
        allowlist_tables=al,
    )
    assert ok is False and "allowlist" in (detail or "").lower()


def test_validate_sql_blocks_unknown_column() -> None:
    s = GraphSettings()
    tc = {"customers": {"id", "name", "tenant_id"}}
    ok, detail, _, _ = validate_sql_deterministic(
        "SELECT bad_col FROM customers LIMIT 10",
        s,
        allowlist_tables={"customers"},
        table_columns=tc,
    )
    assert ok is False and detail and "column" in detail.lower()


def test_validate_sql_allows_known_column() -> None:
    s = GraphSettings()
    tc = {"customers": {"id", "name", "tenant_id"}}
    ok, _, sanitized, _ = validate_sql_deterministic(
        "SELECT id FROM customers LIMIT 10",
        s,
        allowlist_tables={"customers"},
        table_columns=tc,
    )
    assert ok is True and sanitized


def test_validate_sql_allows_star_select() -> None:
    s = GraphSettings()
    tc = {"customers": {"id", "name", "tenant_id"}}
    ok, _, _, _ = validate_sql_deterministic(
        "SELECT * FROM customers LIMIT 10",
        s,
        allowlist_tables={"customers"},
        table_columns=tc,
    )
    assert ok is True


def test_validate_sql_qualified_column() -> None:
    s = GraphSettings()
    tc = {"customers": {"id", "name", "tenant_id"}}
    ok_good, _, _, _ = validate_sql_deterministic(
        "SELECT customers.id FROM customers LIMIT 10",
        s,
        allowlist_tables={"customers"},
        table_columns=tc,
    )
    ok_bad, detail, _, _ = validate_sql_deterministic(
        "SELECT customers.bad FROM customers LIMIT 10",
        s,
        allowlist_tables={"customers"},
        table_columns=tc,
    )
    assert ok_good is True
    assert ok_bad is False and detail and "column" in detail.lower()


# --- registry hardening / unknown intent ---


def test_normalize_intent_unknown_to_general_chat() -> None:
    assert normalize_intent("garbage") == "general_chat"
    assert normalize_intent(None) == "general_chat"


# --- empty result D4: no retry, summarize "no data" ---


class _EmptyExecutor:
    def execute(self, sql: str, *, tenant_id: str | None) -> dict:
        return {"rows": [], "meta": {"mode": "empty"}}


def test_empty_result_does_not_retry_and_summarizes() -> None:
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient(reply="Không có dữ liệu phù hợp."))
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", FakeLlmClient(reply="SELECT id FROM customers LIMIT 10"))
    reg.register("sql_review", FakeLlmClient())
    reg.register("chat", FakeLlmClient())
    reg.register("summarize", FakeLlmClient(reply="Không tìm thấy dữ liệu phù hợp với câu hỏi của bạn."))
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=_EmptyExecutor(),
        settings=GraphSettings(),
        schema_loader=FileSchemaLoader(None),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    out = g.invoke(
        {
            **default_initial_state(),
            "messages": [HumanMessage(content="thống kê")],
            "schema_version": "v1",
        },
    )
    assert int(out.get("sql_attempt_count") or 0) == 1
    ans = (out.get("final_answer") or "").lower()
    assert "không" in ans or "no data" in ans or "không tìm thấy" in ans


# --- max retries (3 lần) ---


def test_max_attempts_with_validate_sql_failure_3_times() -> None:
    """Force validate_sql to fail by making sql_gen produce DDL — should retry up to 3."""
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient(reply="DROP TABLE t"))
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", FakeLlmClient(reply="DROP TABLE t"))
    reg.register("sql_review", FakeLlmClient())
    reg.register("chat", FakeLlmClient())
    reg.register("summarize", FakeLlmClient(reply="error"))
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
        schema_loader=FileSchemaLoader(None),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    out = g.invoke(
        {
            **default_initial_state(),
            "messages": [HumanMessage(content="q")],
            "schema_version": "v1",
        },
    )
    assert int(out.get("sql_attempt_count") or 0) == 3
    assert (out.get("error_payload") or {}).get("error") == "max_sql_attempts"


# --- schema load fail — no sql_gen LLM (FR-DBM-02) ---


def test_gen_sql_early_fails_on_schema_load_error() -> None:
    sql_gen = FakeLlmClient(reply="SELECT id FROM customers LIMIT 10")
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient())
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", sql_gen)
    reg.register("sql_review", FakeLlmClient())
    reg.register("chat", FakeLlmClient())
    reg.register("summarize", FakeLlmClient(reply="err"))
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
        schema_loader=FileSchemaLoader(None),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    out = g.invoke(
        {
            **default_initial_state(),
            "messages": [HumanMessage(content="q")],
            "schema_version": "bad-version",
        },
    )
    assert sql_gen.invoke_count == 0
    assert (out.get("error_payload") or {}).get("error") == "schema_load_failed"


# --- correlation id on logs (NFR-OBS-01) ---


def test_node_logs_include_correlation_id(caplog: pytest.LogCaptureFixture) -> None:
    setup_correlation_logging()
    caplog.set_level(logging.INFO)
    reg = LlmRegistry()
    fake = FakeLlmClient()
    reg.register("default", fake)
    reg.register("intent", fake)
    reg.register("chat", fake)
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
    )
    g = compile_agent_graph(deps, use_checkpointer=False)
    with correlation_scope("test-cid"):
        g.invoke({**default_initial_state(), "messages": [HumanMessage(content="hi")]})
    graph_logs = [r for r in caplog.records if r.name.startswith("app.graph")]
    assert graph_logs
    for r in graph_logs:
        assert getattr(r, "correlation_id", None) == "test-cid"
