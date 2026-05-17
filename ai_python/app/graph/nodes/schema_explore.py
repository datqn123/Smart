"""Schema explorer node: metrics + list_tables + LLM schema_plan + describe + artifact."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.agent_trace import emit_agent_trace
from app.graph.deps import GraphDeps
from app.graph.ledger_metrics import (
    detect_dimensions,
    default_tables_for_metric,
    ledger_sql_hints,
    resolve_metric,
)
from app.graph.message_utils import latest_human_question
from app.graph.reference_joins import join_hints_for_plan, tables_for_dimensions
from app.graph.schema_tools import (
    build_artifact_for_tables,
    format_catalog_for_prompt,
    list_tables,
)
from app.graph.spring_describe_client import build_spring_describe_client
from app.graph.state import AgentState
from app.llm.schemas import SchemaPlanOutput
from app.prompts.load import load_agent_json_contract, load_agent_prompt

logger = logging.getLogger(__name__)

_SCHEMA_PLAN_SYSTEM = load_agent_prompt("schema_explore")
_SCHEMA_PLAN_JSON_CONTRACT = load_agent_json_contract("schema_explore") or ""


def _merge_plan_tables(
    llm_tables: list[str],
    metric_id: str,
    dimensions: list[str],
    *,
    max_tables: int,
    force_financeledger: bool = True,
) -> list[str]:
    seed = default_tables_for_metric(metric_id, dimensions)  # type: ignore[arg-type]
    for t in tables_for_dimensions(dimensions):
        if t not in seed:
            seed.append(t)
    for t in llm_tables:
        if t and t not in seed:
            seed.append(t)
    if force_financeledger and "financeledger" not in {x.lower() for x in seed}:
        seed.insert(0, "financeledger")
    return seed[:max_tables]


def make_schema_explore_node(deps: GraphDeps):
    def schema_explore(state: AgentState) -> dict:
        logger.info("node=schema_explore action=start")
        if not deps.settings.sql_schema_explorer_enabled:
            return {}

        user_q = latest_human_question(state.get("messages"))
        metric_id = resolve_metric(user_q)
        dimensions = detect_dimensions(user_q)
        catalog, cerr = list_tables(deps.settings)
        if cerr:
            logger.warning("list_tables failed: %s", cerr)
            emit_agent_trace(
                logger,
                deps.settings,
                agent="schema_explore",
                phase="Lỗi catalog",
                detail=cerr,
            )
            return {
                "error_payload": {
                    "error": "schema_catalog_failed",
                    "detail": cerr,
                },
            }

        catalog_text = format_catalog_for_prompt(catalog)
        metric_hints = "\n".join(ledger_sql_hints(metric_id))
        reg = deps.llm_registry
        llm_tables: list[str] = []
        llm_dims = list(dimensions)
        ambiguity: str | None = None

        if reg is not None:
            human = (
                f"Resolved metric (hint): {metric_id}\n"
                f"Detected dimensions (hint): {', '.join(dimensions) or '(none)'}\n\n"
                f"Metric SQL hints:\n{metric_hints}\n\n"
                f"Table catalog:\n{catalog_text}\n\n"
                f"User question:\n{user_q}\n\n"
                f"Return at most {deps.settings.sql_max_selected_tables} tables."
            )
            messages = [SystemMessage(content=_SCHEMA_PLAN_SYSTEM), HumanMessage(content=human)]
            client = reg.get("schema_plan")
            try:
                out = client.structured_predict(
                    messages,
                    SchemaPlanOutput,
                    json_output_contract=_SCHEMA_PLAN_JSON_CONTRACT,
                )
                metric_id = out.metric_id
                llm_tables = list(out.tables or [])
                llm_dims = list(out.dimensions or dimensions)
                ambiguity = out.ambiguity_note
            except Exception:
                logger.warning("schema_plan structured_predict failed; using defaults", exc_info=True)

        is_chart = state.get("intent") == "system_data_chart"
        tables = _merge_plan_tables(
            llm_tables,
            metric_id,
            llm_dims,
            max_tables=int(deps.settings.sql_max_selected_tables),
            force_financeledger=not is_chart,
        )
        join_hints = join_hints_for_plan(tables=tables, dimensions=llm_dims)

        describe_client = build_spring_describe_client(deps.settings)
        cid = state.get("correlation_id")
        art, aerr = build_artifact_for_tables(
            deps.settings,
            tables,
            describe_client=describe_client,
            correlation_id=str(cid) if cid else None,
            describe_max=int(deps.settings.sql_schema_explorer_describe_max_tables),
        )
        if describe_client is not None:
            try:
                describe_client.close()
            except Exception:
                pass

        if art is None:
            logger.warning("build_artifact_for_tables failed: %s", aerr)
            emit_agent_trace(
                logger,
                deps.settings,
                agent="schema_explore",
                phase="Không build được artifact",
                detail=aerr or "unknown",
            )
            return {
                "error_payload": {
                    "error": "schema_load_failed",
                    "detail": aerr or "artifact build failed",
                },
            }

        plan_dict = {
            "metric_id": metric_id,
            "tables": tables,
            "dimensions": llm_dims,
            "ambiguity_note": ambiguity,
            "sql_hints": ledger_sql_hints(metric_id),
            "join_hints": join_hints,
        }
        emit_agent_trace(
            logger,
            deps.settings,
            agent="schema_explore",
            phase="Schema plan",
            detail=json.dumps(plan_dict, ensure_ascii=False)[:1200],
        )
        return {
            "schema_plan": plan_dict,
            "ledger_metric_id": metric_id,
            "schema_join_hints": join_hints,
            "selected_tables": tables,
            "runtime_schema_artifact": art.model_dump(mode="json"),
        }

    return schema_explore


def route_sql_subgraph_start(deps: GraphDeps):
    def router(_state: AgentState) -> str:
        if deps.settings.sql_schema_explorer_enabled:
            return "schema_explore"
        return "gen_sql"

    return router
