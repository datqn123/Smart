"""Tests for ledger-first metrics, reference joins, schema explorer helpers."""

from __future__ import annotations

import httpx

from app.config.graph_settings import GraphSettings
from app.graph.ledger_metrics import ledger_sql_hints, resolve_metric
from app.graph.reference_joins import join_hints_for_plan, salesorders_join_requires_reference_type
from app.graph.spring_describe_client import SpringDescribeClient, derive_spring_describe_url
from app.graph.sql_prompts import build_gen_sql_user_prompt
from app.graph.validate_sql import check_ledger_metric_policy


def test_resolve_metric_revenue() -> None:
    assert resolve_metric("Tính doanh thu tháng 5") == "ledger_revenue"


def test_resolve_metric_expense() -> None:
    assert resolve_metric("Tổng chi phí mua hàng") == "ledger_expense"


def test_ledger_sql_hints_revenue() -> None:
    hints = ledger_sql_hints("ledger_revenue")
    assert any("financeledger" in h for h in hints)
    assert any("SalesRevenue" in h for h in hints)


def test_join_hints_salesorder() -> None:
    hints = join_hints_for_plan(tables=["financeledger", "salesorders"], dimensions=["order_channel"])
    assert any("SalesOrder" in h for h in hints)


def test_derive_spring_describe_url() -> None:
    url = derive_spring_describe_url("http://127.0.0.1:8080/api/v1/ai/db/sql/query-readonly-raw")
    assert url is not None
    assert url.endswith("/sql/describe")


def test_check_ledger_metric_policy_requires_financeledger() -> None:
    ok, detail = check_ledger_metric_policy(
        "SELECT SUM(final_amount) FROM salesorders LIMIT 10",
        metric_id="ledger_revenue",
        user_q="doanh thu",
        enabled=True,
    )
    assert not ok
    assert detail is not None


def test_check_ledger_metric_policy_ok() -> None:
    sql = (
        "SELECT SUM(amount) FROM financeledger "
        "WHERE transaction_type = 'SalesRevenue' LIMIT 10"
    )
    ok, _ = check_ledger_metric_policy(
        sql,
        metric_id="ledger_revenue",
        user_q="doanh thu",
        enabled=True,
    )
    assert ok


def test_salesorders_join_policy_violation() -> None:
    sql = "SELECT * FROM financeledger fl JOIN salesorders so ON fl.reference_id = so.id LIMIT 5"
    assert salesorders_join_requires_reference_type(sql)


def test_build_gen_sql_prompt_ledger_first() -> None:
    prompt = build_gen_sql_user_prompt(
        mode="explore",
        schema_block="- financeledger(id, amount)",
        feedback_render="(none)",
        user_q="doanh thu",
        seed_sql=None,
        sql_limit_max=100,
        ledger_first=True,
        schema_plan={
            "metric_id": "ledger_revenue",
            "tables": ["financeledger"],
            "sql_hints": ledger_sql_hints("ledger_revenue"),
            "join_hints": [],
        },
    )
    assert "financeledger" in prompt
    assert "SalesRevenue" in prompt


def test_graph_settings_schema_explorer_flags() -> None:
    s = GraphSettings(sql_schema_explorer_enabled=True, sql_ledger_first_prompts=True)
    assert s.sql_schema_explorer_enabled is True


def test_spring_describe_prefers_request_bearer_token() -> None:
    received: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"columns": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = GraphSettings(
        sql_executor_mode="http_spring",
        spring_sql_url="http://example.test/api/v1/ai/db/sql/query-readonly-raw",
        spring_sql_bearer_token="static-token",
    )
    describe = SpringDescribeClient(settings, client=client)
    describe.describe("financeledger", bearer_token="dynamic-token")
    assert received.get("authorization") == "Bearer dynamic-token"


def test_spring_describe_falls_back_to_static_bearer_token() -> None:
    received: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"columns": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = GraphSettings(
        sql_executor_mode="http_spring",
        spring_sql_url="http://example.test/api/v1/ai/db/sql/query-readonly-raw",
        spring_sql_bearer_token="static-token",
    )
    describe = SpringDescribeClient(settings, client=client)
    describe.describe("financeledger")
    assert received.get("authorization") == "Bearer static-token"
