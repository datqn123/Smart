"""Intent verification node for SQL subgraph — checks generated SQL against user intent."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.feedback import append_feedback
from app.graph.state import AgentState
from app.graph.validate_sql import is_llm_select_sql_shape

logger = logging.getLogger(__name__)

_INTENT_VERIFICATION_ENABLED = True

_DOMAIN_FACT_TABLES: dict[str, str] = {
    "inventory": "inventory",
    "receipt": "stockreceipts",
    "dispatch": "stockdispatches",
    "ledger": "financeledger",
    "catalog_price": "products",
}


def _detect_fact_table(sql: str) -> str | None:
    m = re.search(r'\b(?:FROM|JOIN)\s+(\w+)', sql, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _is_simple_sql(sql: str) -> bool:
    if re.search(r'\bWITH\b', sql, re.IGNORECASE):
        return False
    joins = re.findall(r'\bJOIN\b', sql, re.IGNORECASE)
    return len(joins) <= 1


def _fallback_verify(sql: str, domain: str) -> dict[str, Any]:
    fact = _detect_fact_table(sql)
    expected = _DOMAIN_FACT_TABLES.get(domain)

    if expected and fact and fact != expected:
        return {
            "intent_match": False,
            "confidence": "high",
            "action": "regen",
            "reason": f"Wrong fact table: expected '{expected}' but SQL uses '{fact}'",
            "feedback": f"Replace FROM {fact} with FROM {expected} for domain {domain}",
        }

    if _is_simple_sql(sql) and not expected:
        return {
            "intent_match": True,
            "confidence": "high",
            "action": "bypass_review",
            "reason": "Simple SQL query passed intent check",
        }

    return {
        "intent_match": True,
        "confidence": "medium",
        "action": "proceed",
        "reason": "Heuristic check passed",
    }


def _load_agent_prompt(name: str) -> str:
    import os
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "agents", f"{name}.md"
    )
    try:
        with open(prompt_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Prompt file not found: %s", prompt_path)
        return ""


def _build_verify_prompt(sql: str, domain: str, user_q: str) -> str:
    return (
        f"User question: {user_q}\n"
        f"Domain: {domain}\n"
        f"SQL: {sql}\n\n"
        "Verify intent alignment. Return JSON with keys: intent_match, confidence, action, reason, feedback"
    )


def make_verify_sql_intent_node(deps: GraphDeps):
    def verify_sql_intent(state: AgentState) -> dict[str, Any]:
        logger.info("node=verify_sql_intent action=start")
        sql = str(state.get("generated_sql") or "")
        domain = str(state.get("sql_query_domain") or "generic")

        last_msg = state.get("messages", [])
        user_q = ""
        if isinstance(last_msg, list) and last_msg:
            from langchain_core.messages import HumanMessage
            for m in reversed(last_msg):
                if isinstance(m, HumanMessage):
                    user_q = m.content if isinstance(m.content, str) else ""
                    break

        if not sql or not is_llm_select_sql_shape(sql):
            fb = append_feedback(state, "sql_fix", "Generated SQL is empty or not a SELECT statement")
            return {
                "verify_intent_ok": False,
                "verify_intent_action": "regen",
                "verify_intent_reason": "Empty or non-SELECT SQL",
                "validation_feedback": fb,
            }

        result = _fallback_verify(sql, domain)

        reg = getattr(deps, "llm_registry", None)
        if reg is not None and _INTENT_VERIFICATION_ENABLED:
            client = None
            try:
                client = reg.get("verify_sql_intent")
            except KeyError:
                try:
                    client = reg.get("default")
                except KeyError:
                    client = None
            if client is not None:
                prompt = _build_verify_prompt(sql, domain, user_q or "")
                system = _load_agent_prompt("verify_sql_intent")
                try:
                    raw = client.invoke_text(prompt, system=system)
                    parsed = json.loads(raw)
                    result = parsed
                except Exception as exc:
                    logger.warning("verify_sql_intent LLM failed, using fallback: %s", exc)

        action = result.get("action", "proceed")
        out: dict[str, Any] = {
            "verify_intent_ok": result.get("intent_match", True),
            "verify_intent_action": action,
            "verify_intent_reason": result.get("reason", ""),
        }

        if action == "regen":
            feedback = str(result.get("feedback", "SQL does not match user intent"))
            fb = append_feedback(state, "sql_fix", feedback)
            out["validation_feedback"] = fb

        return out

    return verify_sql_intent
