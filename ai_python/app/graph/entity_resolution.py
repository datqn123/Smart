from __future__ import annotations

import logging
import re
from typing import Any

from app.graph.deps import GraphDeps
from app.graph.sql_executor import SqlExecutor
from app.graph.sql_query_domain import SqlQueryDomain

logger = logging.getLogger(__name__)

_STOPWORDS = frozenset({
    "của", "và", "các", "những", "cho", "trong", "tại", "từ", "đến", "với",
    "có", "không", "đã", "đang", "sẽ", "này", "kia", "đó", "một", "hai", "ba",
    "bốn", "năm", "tháng", "ngày", "năm", "quý", "tuần", "liệt", "kê", "danh",
    "sách", "xem", "tìm", "kiếm", "bao", "nhiêu", "nào", "số", "lượng", "giá",
    "trị", "tổng", "cộng", "tất", "cả", "đơn", "hàng", "mới", "cũ", "còn",
})

_DOMAIN_PHRASES: dict[str, tuple[str, ...]] = {
    "inventory": ("tồn kho", "hết hàng", "còn bao nhiêu", "sắp hết"),
    "receipt": ("phiếu nhập", "nhập kho", "stockreceipt"),
    "dispatch": ("phiếu xuất", "xuất kho", "giao hàng", "stockdispatch"),
    "ledger": ("doanh thu", "chi phí", "dòng tiền", "sổ cái"),
    "catalog_price": ("giá vốn", "giá bán", "giá niêm yết", "đơn giá"),
}

_ENTITY_MAP: dict[str, list[dict[str, str]]] = {
    "inventory": [{"table": "products", "column": "name"}],
    "receipt": [
        {"table": "products", "column": "name"},
        {"table": "suppliers", "column": "name"},
    ],
    "dispatch": [{"table": "products", "column": "name"}],
    "ledger": [{"table": "financeledger", "column": "transaction_type"}],
    "catalog_price": [
        {"table": "products", "column": "name"},
        {"table": "categories", "column": "name"},
    ],
}

_ALLOWED_TABLES: frozenset[str] = frozenset(
    e["table"] for entries in _ENTITY_MAP.values() for e in entries
)

_ALLOWED_COLUMNS: frozenset[str] = frozenset(
    e["column"] for entries in _ENTITY_MAP.values() for e in entries
)


def _extract_keywords(question: str, domain: str) -> list[str]:
    if domain == "generic":
        return []
    lower = question.lower()
    lower = re.sub(r"[^\w\s]", "", lower, flags=re.UNICODE)
    tokens = lower.split()
    domain_phrases = _DOMAIN_PHRASES.get(domain, ())
    result: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if len(token) < 2:
            continue
        if token in _STOPWORDS:
            continue
        if token in domain_phrases:
            continue
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result


async def _load_names_batch(
    executor: SqlExecutor,
    tenant_id: str | None,
    table: str,
    column: str,
    offset: int,
    limit: int,
    bearer_token: str | None = None,
) -> list[str]:
    if not tenant_id:
        return []
    if table not in _ALLOWED_TABLES or column not in _ALLOWED_COLUMNS:
        logger.warning("entity resolution blocked: table=%s col=%s not in allowlist", table, column)
        return []
    sql = f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY "{column}" LIMIT {int(limit)} OFFSET {int(offset)}'
    try:
        result = await executor.aexecute(sql, tenant_id=tenant_id, bearer_token=bearer_token)
        rows = result.get("rows", [])
        return [str(r[column]) for r in rows if column in r]
    except Exception as exc:
        logger.warning("Failed to load names batch from %s.%s: %s", table, column, exc)
        return []


def _match_keywords(names: list[str], keywords: list[str]) -> dict[str, Any]:
    exact_matches: list[str] = []
    fuzzy_matches: list[str] = []
    seen_exact: set[str] = set()
    seen_fuzzy: set[str] = set()

    names_lower = {n: n.lower() for n in names}
    name_word_sets: dict[str, set[str]] = {
        n: set(n.lower().split()) for n in names
    }

    for kw in keywords:
        kw_lower = kw.lower()
        for name in names:
            if name in seen_exact:
                continue
            if names_lower[name] == kw_lower:
                exact_matches.append(name)
                seen_exact.add(name)
                break

    for kw in keywords:
        kw_lower = kw.lower()
        for name in names:
            if name in seen_exact or name in seen_fuzzy:
                continue
            if kw_lower in name_word_sets[name]:
                fuzzy_matches.append(name)
                seen_fuzzy.add(name)
                break

    return {
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
        "found_exact": len(exact_matches) > 0,
    }


async def load_entity_names(
    executor: SqlExecutor,
    tenant_id: str | None,
    table: str,
    column: str,
    keywords: list[str],
    batch_size: int = 500,
    max_batches: int = 3,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    if not keywords:
        return {
            "exact_matches": [],
            "fuzzy_matches": [],
            "loaded_names": [],
            "truncated": True,
        }

    loaded_names: list[str] = []
    for batch_idx in range(max_batches):
        offset = batch_idx * batch_size
        batch = await _load_names_batch(
            executor, tenant_id, table, column, offset, batch_size, bearer_token=bearer_token,
        )
        if not batch:
            matched = _match_keywords(loaded_names, keywords)
            return {
                "exact_matches": matched["exact_matches"],
                "fuzzy_matches": matched["fuzzy_matches"],
                "loaded_names": loaded_names,
                "truncated": True,
            }
        loaded_names.extend(batch)
        matched = _match_keywords(loaded_names, keywords)
        if matched["found_exact"]:
            return {
                "exact_matches": matched["exact_matches"],
                "fuzzy_matches": matched["fuzzy_matches"],
                "loaded_names": loaded_names,
                "truncated": False,
            }

    matched = _match_keywords(loaded_names, keywords)
    return {
        "exact_matches": matched["exact_matches"],
        "fuzzy_matches": matched["fuzzy_matches"],
        "loaded_names": loaded_names,
        "truncated": True,
    }


async def resolve_entities_for_domain(
    deps: GraphDeps,
    tenant_id: str | None,
    question: str,
    domain: SqlQueryDomain,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    if not tenant_id:
        return {}
    if not deps.settings.entity_resolution_enabled:
        return {}
    if domain == "generic":
        return {}
    keywords = _extract_keywords(question, domain)
    entities = _ENTITY_MAP.get(domain, [])
    result: dict[str, Any] = {}
    for entity in entities:
        table = entity["table"]
        column = entity["column"]
        batch_size = deps.settings.entity_resolution_batch_size
        max_batches = deps.settings.entity_resolution_max_batches
        resolved = await load_entity_names(
            deps.sql_executor,
            tenant_id,
            table,
            column,
            keywords,
            batch_size=batch_size,
            max_batches=max_batches,
            bearer_token=bearer_token,
        )
        result[table] = resolved
    return result
