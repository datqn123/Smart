from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.config.graph_settings import GraphSettings
from app.graph.business_scope import (
    build_last_data_answer_context,
    resolve_business_scope,
    scope_effective_question,
)
from app.graph.deps import GraphDeps
from app.graph.feedback import empty_feedback
from app.graph.nodes.sql_pipeline import make_validate_result_node, route_after_validate_result
from app.graph.sql_executor import StubSqlExecutor


def _deps() -> GraphDeps:
    return GraphDeps(
        llm_registry=None,
        sql_executor=StubSqlExecutor(),
        settings=GraphSettings(),
    )


def _seed_prev_total_context() -> tuple[dict, dict]:
    prev_scope = resolve_business_scope(
        "hãy cho tôi biết từ đầu năm tới giờ tổng tiền thu vào là bao nhiêu",
        intent="system_data_query",
        previous_scope=None,
    )
    assert prev_scope is not None
    prev_ctx = build_last_data_answer_context(
        intent="system_data_query",
        user_question="hãy cho tôi biết từ đầu năm tới giờ tổng tiền thu vào là bao nhiêu",
        effective_question=scope_effective_question(
            "hãy cho tôi biết từ đầu năm tới giờ tổng tiền thu vào là bao nhiêu",
            prev_scope,
        ),
        business_scope=prev_scope,
        query_result={"rows": [{"total_received_amount": 1103700}]},
        generated_sql="SELECT 1103700 AS total_received_amount LIMIT 1",
    )
    assert isinstance(prev_ctx, dict)
    return prev_scope, prev_ctx


def test_validate_result_reconcile_mismatch_triggers_retry_feedback() -> None:
    deps = _deps()
    node = make_validate_result_node(deps)
    prev_scope, prev_ctx = _seed_prev_total_context()
    follow_scope = resolve_business_scope(
        "liệt kê đi",
        intent="system_data_query",
        previous_scope=prev_scope,
        previous_data_answer=prev_ctx,
    )
    assert follow_scope is not None
    state = {
        "intent": "system_data_query",
        "messages": [HumanMessage(content="liệt kê đi")],
        "business_scope": follow_scope,
        "last_data_answer": prev_ctx,
        "generated_sql": "SELECT receipt_code, amount FROM cashtransactions LIMIT 100",
        "query_result": {"rows": [{"receipt_code": "PT-2026-0002", "amount": 250000}]},
        "validation_feedback": empty_feedback(),
        "sql_attempt_count": 1,
        "sql_repair_max_attempts": 3,
    }
    out = node(state)
    assert out["result_ok"] is False
    fb = out.get("validation_feedback") or {}
    result_bucket = list(fb.get("result") or [])
    assert any("reconcile mismatch" in item for item in result_bucket)
    nxt = route_after_validate_result({**state, **out})
    assert nxt == "gen_sql"


def test_validate_result_reconcile_passes_and_stores_last_data_answer() -> None:
    deps = _deps()
    node = make_validate_result_node(deps)
    prev_scope, prev_ctx = _seed_prev_total_context()
    follow_scope = resolve_business_scope(
        "liệt kê đi",
        intent="system_data_query",
        previous_scope=prev_scope,
        previous_data_answer=prev_ctx,
    )
    assert follow_scope is not None
    state = {
        "intent": "system_data_query",
        "messages": [HumanMessage(content="liệt kê đi")],
        "business_scope": follow_scope,
        "last_data_answer": prev_ctx,
        "generated_sql": "SELECT receipt_code, amount FROM cashtransactions LIMIT 100",
        "query_result": {
            "rows": [
                {"receipt_code": "PT-2026-0001", "amount": 500000},
                {"receipt_code": "PT-2026-0002", "amount": 250000},
                {"receipt_code": "PT-2026-0003", "amount": 353700},
            ]
        },
        "validation_feedback": empty_feedback(),
        "sql_attempt_count": 1,
        "sql_repair_max_attempts": 3,
    }
    out = node(state)
    assert out["result_ok"] is True
    assert out["result_empty"] is False
    merged_scope = out.get("business_scope") or {}
    follow = merged_scope.get("followup") if isinstance(merged_scope, dict) else {}
    assert isinstance(follow, dict)
    assert follow.get("detail_reconcile_required") is True
    assert follow.get("detail_reconcile_ok") is True
    ctx = out.get("last_data_answer")
    assert isinstance(ctx, dict)
    assert ctx.get("row_count") == 3
    rec = ctx.get("reconcile")
    assert isinstance(rec, dict)
    assert rec.get("ok") is True


def test_validate_result_fails_when_clarification_followup_lacks_reconcile_context() -> None:
    deps = _deps()
    node = make_validate_result_node(deps)
    scope = resolve_business_scope(
        "Liệt kê theo phiếu thu theo cùng mốc thời gian",
        intent="system_data_query",
        previous_scope=None,
    )
    assert scope is not None
    state = {
        "intent": "system_data_query",
        "messages": [HumanMessage(content="Liệt kê theo phiếu thu theo cùng mốc thời gian")],
        "business_scope": scope,
        "last_data_answer": None,
        "clarification_applied_context": {"clarify_kind": "data_followup_detail"},
        "generated_sql": "SELECT receipt_code, amount FROM cashtransactions LIMIT 100",
        "query_result": {"rows": [{"receipt_code": "PT-2026-0002", "amount": 250000}]},
        "validation_feedback": empty_feedback(),
        "sql_attempt_count": 1,
        "sql_repair_max_attempts": 3,
    }
    out = node(state)
    assert out["result_ok"] is False
    fb = out.get("validation_feedback") or {}
    result_bucket = list(fb.get("result") or [])
    assert any("missing reconcile context" in item for item in result_bucket)
