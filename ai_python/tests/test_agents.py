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
from app.graph.logging_policy import safe_log_query_result
from app.graph.validate_sql import validate_sql_deterministic
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


def test_safe_log_query_result_includes_row_preview() -> None:
    text = safe_log_query_result(
        {
            "rows": [{"total_inventory_value": 30554000}],
            "meta": {"row_count": 1, "columns": ["total_inventory_value"]},
        }
    )
    assert "30554000" in text
    assert "rows_preview" in text


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


def test_render_for_prompt_max_items_per_bucket() -> None:
    fb = empty_feedback()
    fb["intent_review"] = ["a", "b", "c", "d"]
    out = render_for_prompt(fb, max_items_per_bucket=2)
    assert "[intent_review] c; d" in out
    assert "a" not in out


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


def test_validate_sql_multiline_limit_not_double_injected() -> None:
    """LIMIT on its own line must be detected so we do not append LIMIT twice."""
    s = GraphSettings(sql_limit_max=1000)
    sql = "SELECT name\nFROM products\nLIMIT 1;"
    ok, _, out, notes = validate_sql_deterministic(sql, s)
    assert ok is True, out
    assert out is not None
    assert out.upper().count("LIMIT") == 1, out
    assert not any("injected" in n.lower() for n in notes), notes


def test_validate_sql_strips_trailing_semicolon() -> None:
    """Spring readonly API rejects a trailing ';' in the SQL string."""
    s = GraphSettings(sql_limit_max=1000)
    ok, _, out, _ = validate_sql_deterministic(
        "SELECT SUM(total) FROM orders WHERE DATE(created_at) = CURRENT_DATE LIMIT 1000;",
        s,
    )
    assert ok and out is not None
    assert not out.rstrip().endswith(";")


def test_validate_sql_allowlist_blocks_other_tables() -> None:
    s = GraphSettings()
    al = {"customers"}
    ok, detail, _, _ = validate_sql_deterministic(
        "SELECT * FROM secret_table LIMIT 10",
        s,
        allowlist_tables=al,
    )
    assert ok is False and "allowlist" in (detail or "").lower()


def test_validate_sql_allowlist_ignores_extract_from_in_where() -> None:
    """EXTRACT(YEAR FROM col) must not be parsed as a FROM-clause table (regex false positive)."""
    s = GraphSettings(sql_limit_max=1000)
    sql = """
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS month,
               COUNT(*) AS number_of_orders
        FROM salesorders
        WHERE EXTRACT(YEAR FROM created_at) = 2026
          AND EXTRACT(MONTH FROM created_at) BETWEEN 1 AND 9
        GROUP BY TO_CHAR(created_at, 'YYYY-MM')
        ORDER BY month
    """
    allow = {
        "customers",
        "orderdetails",
        "productpricehistory",
        "products",
        "productunits",
        "salesorders",
        "stockdispatches",
        "storeprofiles",
    }
    ok, detail, sanitized, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables=allow,
    )
    assert ok is True, detail
    assert sanitized and "salesorders" in sanitized.lower()


def test_validate_sql_rejects_sale_price_on_products_table() -> None:
    """sqlparse must validate columns inside SUM(...) — not only the outer aggregate."""
    s = GraphSettings()
    tc = {
        "inventory": {"id", "product_id", "quantity", "unit_id"},
        "products": {"id", "category_id", "sku_code", "name"},
        "productpricehistory": {"product_id", "unit_id", "cost_price", "sale_price", "effective_date"},
    }
    sql = (
        "SELECT SUM(i.quantity * p.sale_price) AS total_inventory_value "
        "FROM inventory i JOIN products p ON i.product_id = p.id WHERE i.quantity > 0 LIMIT 1000"
    )
    ok, detail, _, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables=set(tc.keys()),
        table_columns=tc,
    )
    assert ok is False and detail and "sale_price" in detail


def test_validate_sql_rejects_productunits_unit_id_column() -> None:
    """productunits PK is id; unit_id exists on FK tables only (pph, inventory, …)."""
    s = GraphSettings()
    tc = {
        "inventory": {"id", "product_id", "quantity", "unit_id"},
        "products": {"id", "name"},
        "productpricehistory": {"id", "product_id", "unit_id", "cost_price", "effective_date"},
        "productunits": {"id", "product_id", "unit_name", "is_base_unit"},
    }
    sql = """
        WITH base_units AS (
            SELECT pu.product_id, pu.unit_id
            FROM productunits pu
            WHERE pu.is_base_unit = TRUE
        )
        SELECT SUM(i.quantity) AS total_qty
        FROM inventory i
        JOIN base_units bu ON bu.product_id = i.product_id
        LIMIT 1000
    """
    ok, detail, _, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables=set(tc.keys()),
        table_columns=tc,
    )
    assert ok is False, detail
    assert detail and "productunits.unit_id" in detail
    assert "pu.id" in detail or "no unit_id column" in detail


def test_validate_sql_inventory_value_with_pu_id_passes() -> None:
    """Canonical stock value: pph.unit_id = pu.id (base unit), not pu.unit_id."""
    s = GraphSettings()
    tc = {
        "inventory": {"id", "product_id", "quantity"},
        "products": {"id", "name"},
        "productpricehistory": {"id", "product_id", "unit_id", "cost_price", "effective_date"},
        "productunits": {"id", "product_id", "is_base_unit"},
    }
    sql = """
        SELECT COALESCE(SUM(i.quantity * pph.cost_price), 0) AS total_inventory_value
        FROM inventory i
        JOIN products p ON p.id = i.product_id
        JOIN productunits pu ON pu.product_id = p.id AND pu.is_base_unit = TRUE
        JOIN productpricehistory pph
          ON pph.product_id = p.id AND pph.unit_id = pu.id
         AND pph.effective_date <= CURRENT_DATE
        WHERE i.quantity > 0
    """
    ok, detail, sanitized, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables=set(tc.keys()),
        table_columns=tc,
    )
    assert ok is True, detail
    assert sanitized and "total_inventory_value" in sanitized.lower()


def test_validate_sql_join_on_qualified_column_not_table() -> None:
    """JOIN ON pu.is_base_unit = TRUE must not be parsed as table is_base_unit."""
    s = GraphSettings()
    allow = {"inventory", "productunits"}
    ok, detail, _, _ = validate_sql_deterministic(
        "SELECT i.id FROM inventory i "
        "JOIN productunits pu ON pu.product_id = i.product_id AND pu.is_base_unit = TRUE "
        "LIMIT 10",
        s,
        allowlist_tables=allow,
        table_columns={
            "inventory": {"id", "product_id"},
            "productunits": {"id", "product_id", "is_base_unit"},
        },
    )
    assert ok is True, detail


def test_validate_sql_not_exists_subquery_table_not_misread_as_column() -> None:
    """FROM table inside NOT EXISTS must not fail as unqualified column ``tablename``."""
    s = GraphSettings()
    tc = {
        "inventory": {"quantity", "product_id", "unit_id"},
        "products": {"id", "cost_price"},
        "productpricehistory": {"product_id", "unit_id", "cost_price", "effective_date"},
    }
    sql = """
        SELECT SUM(i.quantity * pp.cost_price) AS total_inventory_value
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        JOIN productpricehistory pp ON p.id = pp.product_id AND pp.unit_id = i.unit_id
        WHERE pp.effective_date <= CURRENT_DATE
        AND NOT EXISTS (
            SELECT 1
            FROM productpricehistory pp2
            WHERE pp2.product_id = pp.product_id
            AND pp2.unit_id = pp.unit_id
            AND pp2.effective_date > pp.effective_date
            AND pp2.effective_date <= CURRENT_DATE
        )
        LIMIT 1000
    """
    ok, detail, _, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables=set(tc.keys()),
        table_columns=tc,
    )
    assert ok is True, detail


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


def test_validate_sql_allows_sum_with_column_allowlist() -> None:
    """sqlparse may emit SUM as Identifier; must not treat as a physical column."""
    s = GraphSettings()
    tc = {
        "cashtransactions": {"amount", "direction", "status", "transaction_date", "id"},
    }
    sql = (
        "SELECT SUM(amount) AS total_revenue FROM cashtransactions WHERE "
        "direction = 'Income' AND status = 'Completed' AND "
        "transaction_date >= DATE_TRUNC('month', CURRENT_DATE) AND "
        "transaction_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' "
        "LIMIT 1000"
    )
    ok, detail, _, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables={"cashtransactions"},
        table_columns=tc,
    )
    assert ok is True, detail


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


def test_validate_sql_allows_group_by_order_by_select_alias() -> None:
    """GROUP BY / ORDER BY may reference SELECT-list aliases (e.g. AS thang)."""
    s = GraphSettings()
    tc = {"salesorders": {"created_at", "order_channel", "id"}}
    sql = (
        "SELECT EXTRACT(MONTH FROM created_at) AS thang, COUNT(*) AS so_luong "
        "FROM salesorders WHERE order_channel = 'Retail' AND EXTRACT(YEAR FROM created_at) = 2026 "
        "GROUP BY thang ORDER BY thang LIMIT 1000"
    )
    ok, detail, _, _ = validate_sql_deterministic(
        sql,
        s,
        allowlist_tables={"salesorders"},
        table_columns=tc,
    )
    assert ok is True, detail


def test_validate_sql_rejects_group_by_not_in_select_or_table() -> None:
    s = GraphSettings()
    tc = {"customers": {"id", "name"}}
    ok, detail, _, _ = validate_sql_deterministic(
        "SELECT id AS x FROM customers GROUP BY mystery LIMIT 10",
        s,
        allowlist_tables={"customers"},
        table_columns=tc,
    )
    assert ok is False and detail and "mystery" in detail.lower()


# --- registry hardening / unknown intent ---


def test_normalize_intent_unknown_to_general_chat() -> None:
    assert normalize_intent("garbage") == "general_chat"
    assert normalize_intent(None) == "general_chat"


# --- empty result D4: no retry, summarize "no data" ---


class _EmptyExecutor:
    def execute(
        self,
        sql: str,
        *,
        tenant_id: str | None,
        correlation_id: str | None = None,
        schema_version: str | None = None,
    ) -> dict:
        _ = correlation_id, schema_version
        return {"rows": [], "meta": {"mode": "empty"}}


def test_empty_result_does_not_retry_and_summarizes(patch_pg_schema_v1: None) -> None:
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


def test_max_attempts_with_validate_sql_failure_3_times(patch_pg_schema_v1: None) -> None:
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


def test_gen_sql_early_fails_on_schema_load_error(monkeypatch: pytest.MonkeyPatch) -> None:
    sql_gen = FakeLlmClient(reply="SELECT id FROM customers LIMIT 10")
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient())
    reg.register("intent", FakeLlmClient(intent="system_data_query"))
    reg.register("sql_gen", sql_gen)
    reg.register("sql_review", FakeLlmClient())
    reg.register("chat", FakeLlmClient())
    reg.register("summarize", FakeLlmClient(reply="err"))
    monkeypatch.setattr(
        "app.graph.pg_schema_context.build_schema_artifact_from_postgres",
        lambda _settings, _user_q: (None, "forced schema unavailable"),
    )
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
