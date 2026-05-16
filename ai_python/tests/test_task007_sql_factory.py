"""Task007 — SQL-Factory-lite helpers (selection, similarity, prompts)."""

from __future__ import annotations

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import ColumnMeta, FileSchemaLoader, SchemaArtifact, TableMeta
from app.graph.sql_prompts import _truncate_col_desc, build_gen_sql_user_prompt, format_schema_block
from app.graph.sql_similarity import hybrid_similarity, max_pool_similarity, sim_tok
from app.graph.sql_table_selection import expand_fk_neighbors, heuristic_select_tables, select_tables_for_question
from app.graph.validate_sql import normalize_llm_sql_output, validate_sql_deterministic
from app.graph.deps import GraphDeps
from app.graph.sql_executor import StubSqlExecutor
from app.llm.registry import LlmRegistry
from tests.fake_llm import FakeLlmClient


def _v1() -> SchemaArtifact:
    return FileSchemaLoader(None).load("v1")


def test_build_gen_sql_user_prompt_includes_dialog_tail() -> None:
    p = build_gen_sql_user_prompt(
        mode="explore",
        schema_block="t(a)",
        feedback_render="(none)",
        user_q="số tiền đơn đó",
        seed_sql=None,
        sql_limit_max=10,
        dialog_tail="User: hôm nay bao nhiêu đơn\n\nAssistant: 1 đơn.",
    )
    assert "Recent conversation" in p
    assert "1 đơn" in p
    assert "số tiền đơn đó" in p


def test_build_gen_sql_user_prompt_includes_planner_json() -> None:
    p = build_gen_sql_user_prompt(
        mode="explore",
        schema_block="t(a)",
        feedback_render="(none)",
        user_q="q",
        seed_sql=None,
        sql_limit_max=10,
        dialog_tail=None,
        planner_data_request_json='{"metric":"revenue"}',
    )
    assert "Chart/data planning brief" in p
    assert "revenue" in p


def test_expand_fk_neighbors_adds_referenced_table() -> None:
    art = _v1()
    out = expand_fk_neighbors(art, ["orders"])
    names = {x.lower() for x in out}
    assert "orders" in names and "customers" in names


def test_heuristic_prefers_orders_keyword() -> None:
    art = _v1()
    picked = heuristic_select_tables("list all orders", art, max_tables=2)
    assert "orders" in [p.lower() for p in picked]


def test_format_schema_enriched_includes_pk_and_fk() -> None:
    art = _v1()
    block = format_schema_block(art, selected_tables=["orders"], enriched=True)
    assert "orders" in block.lower()
    assert "PK:" in block or "pk:" in block.lower()
    assert "customer_id" in block.lower()


def test_format_schema_enriched_includes_column_descriptions_and_truncation() -> None:
    long_desc = "x" * 400
    art = SchemaArtifact(
        schema_version="test",
        tables=[
            TableMeta(
                name="orders",
                description="Đơn hàng",
                pk=["id"],
                fks=[],
                columns=[
                    ColumnMeta(name="id", type="integer"),
                    ColumnMeta(name="status", type="varchar", description="Trạng thái đơn."),
                    ColumnMeta(name="note", type="varchar", description=long_desc),
                ],
            )
        ],
    )
    block = format_schema_block(art, selected_tables=["orders"], enriched=True)
    assert "status" in block.lower()
    assert "Trạng thái đơn" in block
    assert "Columns:" in block
    assert "…" in block
    assert len(_truncate_col_desc(long_desc)) <= 320


def test_hybrid_similarity_identical_high() -> None:
    sql = "SELECT id FROM orders WHERE tenant_id = 1 LIMIT 10"
    s = hybrid_similarity(sql, sql, token_weight=0.5)
    assert s >= 0.99


def test_max_pool_similarity() -> None:
    pool = ["SELECT a FROM t LIMIT 1", "SELECT b FROM t LIMIT 1"]
    mx = max_pool_similarity("SELECT a FROM t LIMIT 1", pool, token_weight=0.6)
    assert mx >= 0.9


def test_sim_tok_disjoint_low() -> None:
    a = sim_tok("SELECT id FROM customers LIMIT 1", "SELECT total FROM products LIMIT 1")
    assert a < 0.85


def test_pg_rank_tables_prefers_inventory_description() -> None:
    from app.graph.pg_schema_context import rank_tables_for_question

    rows = [
        ("customers", "Khách hàng mua hàng"),
        ("inventory", "Tồn kho theo sản phẩm, lô, vị trí kho"),
        ("products", "Sản phẩm master SKU giá"),
    ]
    out = rank_tables_for_question("sản phẩm nào còn nhiều trong kho", rows, max_tables=3)
    assert "inventory" in [x.lower() for x in out]


def test_normalize_llm_sql_fence_then_validate() -> None:
    raw = "```sql\nSELECT count(*) FROM products LIMIT 10;\n```"
    s = normalize_llm_sql_output(raw)
    assert "```" not in s and "SELECT" in s.upper()
    ok, detail, _, _ = validate_sql_deterministic(s, GraphSettings())
    assert ok is True, detail


def test_validate_count_star_against_allowlist_columns() -> None:
    """COUNT(*) must not treat aggregate name as a column (sqlparse Function)."""
    from app.graph.dbmeta import FileSchemaLoader

    art = FileSchemaLoader(None).load("v1")
    allow = art.allowlist_table_names()
    cols = art.allowlist_columns_map()
    ok, detail, _, _ = validate_sql_deterministic(
        "SELECT COUNT(*) FROM products LIMIT 10",
        GraphSettings(),
        allowlist_tables=allow,
        table_columns=cols,
    )
    assert ok is True, detail


def test_llm_table_pick_intersection() -> None:
    art = _v1()
    reg = LlmRegistry()
    reg.register("default", FakeLlmClient())
    reg.register("sql_table_pick", FakeLlmClient(table_pick=["nope_table", "orders", "extra"]))
    deps = GraphDeps(
        llm_registry=reg,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(
            sql_table_selection_enabled=True,
            sql_table_pick_use_llm=True,
            sql_table_pick_min_tables_for_llm=1,
            sql_max_selected_tables=4,
        ),
    )
    out = select_tables_for_question(
        deps=deps,
        user_q="orders revenue",
        artifact=art,
        max_tables=4,
        use_llm=True,
        min_tables_for_llm=1,
    )
    assert "orders" in [x.lower() for x in out]
    assert "nope_table" not in [x.lower() for x in out]
