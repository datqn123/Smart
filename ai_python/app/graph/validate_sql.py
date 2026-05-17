"""Deterministic SQL validation (TASK-LG-08 / FR-07 / Task 3 upgrade)."""

from __future__ import annotations

import re

import sqlparse
from sqlparse.sql import Comparison, Function, Identifier, IdentifierList, Parenthesis, Statement, Where

from app.config.graph_settings import GraphSettings
from app.graph.enum_literals import fix_enum_literals_in_sql
from app.graph.name_filters import fix_name_equality_to_ilike

_DDL_DML = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

_SQL_KEYWORDS = frozenset(
    """
    select distinct from where and or not null true false as on in is like
    left right inner outer join cross natural full group by order having limit
    offset union all case when then else end between exists asc desc
    current_date current_time current_timestamp localtime localtimestamp
    """.split(),
)

# sqlparse often emits aggregate / builtin names as Identifier, not Function — do not treat as columns.
_SQL_BUILTIN_IDENTIFIERS = frozenset(
    """
    sum count avg min max stddev stddev_pop stddev_samp variance var_pop var_samp
    bool_and bool_or every string_agg array_agg json_agg json_object_agg json_build_array json_build_object
    coalesce nullif greatest least
    abs round floor ceil sign mod power sqrt exp ln log random
    concat concat_ws trim ltrim rtrim upper lower replace substring overlay position length left right split_part
    cast extract date_trunc date_part age make_date make_time
    clock_timestamp statement_timestamp transaction_timestamp now
    row_number rank dense_rank percent_rank cume_dist ntile lead lag first_value last_value nth_value
    generate_series unnest cardinality array_length array_position
    to_char to_date to_timestamp to_number
    """.split(),
)

# Names after "AS" in CAST(... AS type) etc. — not SELECT output aliases for GROUP BY.
_SQL_AS_ALIAS_SKIP_NAMES = frozenset(
    """
    int integer bigint smallint serial float real double precision varchar char text boolean
    date timestamp timestamptz time interval record decimal numeric
    """.split(),
)

_AS_PROJECTION_ALIAS = re.compile(r"(?is)\bAS\s+([a-zA-Z_][\w]*)")


def extract_cte_names(sql: str) -> set[str]:
    """
    Lowercase names declared in WITH ... AS (...), including WITH RECURSIVE.
    Used to exclude CTEs from physical-table allowlist checks.
    """
    text = (sql or "").strip()
    if not re.match(r"(?is)^\s*with\s", text):
        return set()
    body = re.sub(r"(?is)^\s*with\s+", "", text, count=1)
    if re.match(r"(?is)^\s*recursive\s+", body):
        body = re.sub(r"(?is)^\s*recursive\s+", "", body, count=1)
    names: set[str] = set()
    while body:
        body = body.lstrip()
        m = re.match(r'(?is)^"?([a-zA-Z_][\w]*)"?\s+as\s*\(', body)
        if not m:
            break
        names.add(m.group(1).lower())
        body = body[m.end() :]
        depth = 1
        i = 0
        while i < len(body) and depth > 0:
            ch = body[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        body = body[i:].lstrip()
        if body.startswith(","):
            body = body[1:]
            continue
        break
    return names


def _join_clause_tokens(stmt: Statement) -> list:
    """Tokens strictly between the top-level FROM keyword and WHERE / GROUP / ORDER / HAVING."""
    tks = stmt.tokens
    fi = _from_keyword_index(tks)
    if fi < 0:
        return []
    ej = _end_join_region(tks, fi)
    return list(tks[fi + 1 : ej])


def _strip_outer_parentheses(s: str) -> str:
    s = (s or "").strip()
    if len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        return s[1:-1].strip()
    return s


def _physical_tables_from_join_token(token: object) -> set[str]:
    """Table names referenced in FROM/JOIN (not EXTRACT/WHERE false positives)."""
    if isinstance(token, IdentifierList):
        out: set[str] = set()
        for x in token.get_identifiers():
            out |= _physical_tables_from_join_token(x)
        return out
    if isinstance(token, Identifier):
        # Qualified refs in JOIN ON (pu.col) are columns, not tables.
        if token.get_parent_name():
            return set()
        for sub in token.tokens:
            if isinstance(sub, Parenthesis):
                inner = _strip_outer_parentheses(str(sub))
                if inner.upper().startswith("SELECT"):
                    inner_parsed = sqlparse.parse(inner)
                    if len(inner_parsed) == 1 and (inner_parsed[0].get_type() or "").upper() == "SELECT":
                        return _extract_from_join_tables_stmt(inner_parsed[0])
                return set()
        real = token.get_real_name()
        if real:
            return {real.split(".")[-1].lower()}
        return set()
    if isinstance(token, Parenthesis):
        inner = _strip_outer_parentheses(str(token))
        if inner.upper().startswith("SELECT"):
            inner_parsed = sqlparse.parse(inner)
            if len(inner_parsed) == 1 and (inner_parsed[0].get_type() or "").upper() == "SELECT":
                return _extract_from_join_tables_stmt(inner_parsed[0])
        return set()
    return set()


def _extract_from_join_tables_stmt(stmt: Statement) -> set[str]:
    names: set[str] = set()
    for t in _join_clause_tokens(stmt):
        names |= _physical_tables_from_join_token(t)
    return names


def _merge_alias_map_from_join_token(token: object, out: dict[str, str]) -> None:
    """Populate alias map from FROM/JOIN region only (avoids EXTRACT(... FROM col) in SELECT/WHERE)."""
    if isinstance(token, IdentifierList):
        for x in token.get_identifiers():
            _merge_alias_map_from_join_token(x, out)
        return
    if isinstance(token, Identifier):
        if token.get_parent_name():
            return
        for sub in token.tokens:
            if isinstance(sub, Parenthesis):
                inner = _strip_outer_parentheses(str(sub))
                if inner.upper().startswith("SELECT"):
                    inner_parsed = sqlparse.parse(inner)
                    if len(inner_parsed) == 1 and (inner_parsed[0].get_type() or "").upper() == "SELECT":
                        out.update(_from_join_alias_map_stmt(inner_parsed[0]))
                return
        real = token.get_real_name()
        if not real:
            return
        raw_t = real.split(".")[-1].lower()
        out[raw_t] = raw_t
        al = token.get_alias()
        if al:
            out[al.lower()] = raw_t
        return
    if isinstance(token, Parenthesis):
        inner = _strip_outer_parentheses(str(token))
        if inner.upper().startswith("SELECT"):
            inner_parsed = sqlparse.parse(inner)
            if len(inner_parsed) == 1 and (inner_parsed[0].get_type() or "").upper() == "SELECT":
                out.update(_from_join_alias_map_stmt(inner_parsed[0]))


def _from_join_alias_map_stmt(stmt: Statement) -> dict[str, str]:
    """Map alias or table token → canonical table name (last path segment, lower)."""
    out: dict[str, str] = {}
    for t in _join_clause_tokens(stmt):
        _merge_alias_map_from_join_token(t, out)
    return out


def _from_keyword_index(tokens: list) -> int:
    for i, t in enumerate(tokens):
        if str(t).upper().strip() == "FROM":
            return i
    return -1


def _select_list_text(stmt: Statement) -> str:
    """Raw text of the SELECT projection (between SELECT and FROM), for alias detection."""
    tks = stmt.tokens
    fi = _from_keyword_index(tks)
    if fi < 0:
        return ""
    parts: list[str] = []
    for t in tks[0:fi]:
        if str(t).upper().strip() == "SELECT":
            continue
        parts.append(str(t))
    return " ".join(parts)


def _select_projection_aliases(select_text: str) -> set[str]:
    """Lowercase output column names from ``... AS alias`` in the SELECT list (not CAST types)."""
    out: set[str] = set()
    for m in _AS_PROJECTION_ALIAS.finditer(select_text or ""):
        name = m.group(1).lower()
        if name in _SQL_AS_ALIAS_SKIP_NAMES or name in _SQL_KEYWORDS:
            continue
        out.add(name)
    return out


def _end_join_region(tokens: list, fi: int) -> int:
    """First index at or after FROM clause where main filters start (WHERE / GROUP / …)."""
    for i in range(fi + 1, len(tokens)):
        t = tokens[i]
        if isinstance(t, Where):
            return i
        su = str(t).upper().strip()
        if su.startswith(("GROUP BY", "ORDER BY", "LIMIT", "HAVING")):
            return i
    return len(tokens)


def _rec_ids(token: object, *, skip_subselects: bool = False) -> list[Identifier]:
    out: list[Identifier] = []
    if skip_subselects and isinstance(token, Parenthesis):
        inner = _strip_outer_parentheses(str(token))
        if inner.upper().startswith("SELECT"):
            return []
    if isinstance(token, Function):
        for x in token.tokens:
            out.extend(_rec_ids(x, skip_subselects=skip_subselects))
        return out
    if isinstance(token, Identifier):
        nested: list[Identifier] = []
        for sub in token.tokens:
            nested.extend(_rec_ids(sub, skip_subselects=skip_subselects))
        if nested:
            return nested
        return [token]
    if isinstance(token, IdentifierList):
        for x in token.get_identifiers():
            if str(x).strip() == "*":
                continue
            out.extend(_rec_ids(x, skip_subselects=skip_subselects))
        return out
    if isinstance(token, Comparison):
        for x in token.tokens:
            out.extend(_rec_ids(x, skip_subselects=skip_subselects))
        return out
    if hasattr(token, "tokens"):
        for x in token.tokens:
            out.extend(_rec_ids(x, skip_subselects=skip_subselects))
    return out


def _collect_column_identifiers(stmt: Statement, *, skip_subselects: bool = False) -> list[Identifier]:
    """Identifiers used as columns (excludes FROM table names; includes JOIN ON / WHERE / GROUP / ORDER)."""
    tks = stmt.tokens
    fi = _from_keyword_index(tks)
    ids: list[Identifier] = []
    if fi < 0:
        return ids
    rec = lambda t: _rec_ids(t, skip_subselects=skip_subselects)
    for t in tks[0:fi]:
        if str(t).upper().strip() == "SELECT":
            continue
        ids.extend(rec(t))
    ej = _end_join_region(tks, fi)
    for t in tks[fi + 1 : ej]:
        if isinstance(t, Comparison):
            ids.extend(rec(t))
    wi = next((i for i, t in enumerate(tks) if isinstance(t, Where)), None)
    if wi is not None:
        ids.extend(rec(tks[wi]))
    start_post = (wi + 1) if wi is not None else ej
    i = start_post
    while i < len(tks):
        su = str(tks[i]).upper().strip()
        if su.startswith("GROUP BY"):
            i += 1
            while i < len(tks):
                ns = str(tks[i]).upper().strip()
                if ns.startswith(("ORDER BY", "LIMIT", "HAVING")):
                    break
                ids.extend(rec(tks[i]))
                i += 1
            continue
        if su.startswith("ORDER BY"):
            i += 1
            while i < len(tks):
                ns = str(tks[i]).upper().strip()
                if ns.startswith("LIMIT"):
                    break
                ids.extend(rec(tks[i]))
                i += 1
            continue
        if su.startswith("HAVING"):
            i += 1
            while i < len(tks):
                if isinstance(tks[i], Comparison):
                    ids.extend(rec(tks[i]))
                ns = str(tks[i]).upper().strip()
                if ns.startswith(("ORDER BY", "LIMIT")):
                    break
                i += 1
            continue
        i += 1
    return ids


def _nested_select_statements(stmt: Statement) -> list[Statement]:
    """Inner SELECT statements (NOT EXISTS, IN subquery, scalar subselect, …)."""
    found: list[Statement] = []

    def walk(tok: object) -> None:
        if isinstance(tok, Parenthesis):
            inner = _strip_outer_parentheses(str(tok))
            if inner.upper().startswith("SELECT"):
                parsed = sqlparse.parse(inner)
                if len(parsed) == 1 and (parsed[0].get_type() or "").upper() == "SELECT":
                    inner_stmt = parsed[0]
                    found.append(inner_stmt)
                    for t in inner_stmt.tokens:
                        walk(t)
            return
        if hasattr(tok, "tokens"):
            for sub in tok.tokens:
                walk(sub)

    for t in stmt.tokens:
        walk(t)
    return found


def _resolve_canonical_table(ref: str, alias_map: dict[str, str]) -> str:
    r = ref.lower()
    return alias_map.get(r, r)


def _column_allowlist_error(
    *,
    table: str | None,
    column: str,
    allowed: set[str] | None,
) -> str:
    """Human- and LLM-readable column policy error (includes table when known)."""
    col = column.lower()
    if table:
        base = f"column not in allowlist: {table}.{col}"
    else:
        base = f"column not in allowlist: {col}"
    hints: list[str] = []
    if table == "productunits" and col == "unit_id":
        hints.append(
            "productunits has no unit_id column; use alias.id (PK) when joining "
            "productpricehistory.unit_id or inventory.unit_id"
        )
    elif allowed:
        sample = ", ".join(sorted(allowed)[:12])
        if len(allowed) > 12:
            sample += ", …"
        hints.append(f"allowed on {table}: {sample}" if table else f"allowed columns include: {sample}")
    if hints:
        return f"{base}. {'; '.join(hints)}"
    return base


def _validate_columns_single_stmt(
    stmt: Statement,
    *,
    table_columns: dict[str, set[str]],
    alias_map: dict[str, str],
    cte_names: set[str],
) -> str | None:
    canonical_tables = {t for t in alias_map.values() if t not in cte_names}
    union_cols: set[str] = set()
    for t in canonical_tables:
        union_cols |= table_columns.get(t, set())

    proj_aliases = _select_projection_aliases(_select_list_text(stmt))
    physical_tables = _extract_from_join_tables_stmt(stmt) | set(table_columns.keys())

    for ident in _collect_column_identifiers(stmt, skip_subselects=True):
        parent = ident.get_parent_name()
        real = ident.get_real_name()
        if real is None:
            continue
        real_l = real.lower()
        if real_l == "*":
            continue
        if parent:
            parent_l = parent.lower()
            if parent_l not in alias_map:
                # Correlated reference to outer query (e.g. pp.col inside NOT EXISTS).
                continue
            tbl = _resolve_canonical_table(parent, alias_map)
            if tbl in cte_names:
                continue
            allowed = table_columns.get(tbl)
            if allowed is None or real_l not in allowed:
                return _column_allowlist_error(table=tbl, column=real_l, allowed=allowed)
        else:
            if real_l in cte_names:
                continue
            if real_l in _SQL_KEYWORDS:
                continue
            if real_l in _SQL_BUILTIN_IDENTIFIERS:
                continue
            if real_l in proj_aliases:
                continue
            # sqlparse may surface inner ``FROM tablename`` as an unqualified column identifier.
            if real_l in physical_tables:
                continue
            if real_l not in union_cols:
                return _column_allowlist_error(table=None, column=real_l, allowed=union_cols or None)
    return None


def _validate_columns_for_map(
    stmt: Statement,
    *,
    table_columns: dict[str, set[str]],
    alias_map: dict[str, str],
    cte_names: set[str] | None = None,
) -> str | None:
    ctes = cte_names or set()
    err = _validate_columns_single_stmt(
        stmt,
        table_columns=table_columns,
        alias_map=alias_map,
        cte_names=ctes,
    )
    if err:
        return err
    for inner in _nested_select_statements(stmt):
        inner_alias = _from_join_alias_map_stmt(inner)
        err = _validate_columns_single_stmt(
            inner,
            table_columns=table_columns,
            alias_map=inner_alias,
            cte_names=ctes,
        )
        if err:
            return err
    return None


def _select_has_limit_clause(sql: str) -> bool:
    """Detect LIMIT regardless of newlines (LLM often emits multi-line SELECT)."""
    collapsed = re.sub(r"\s+", " ", sql.strip())
    upper = collapsed.upper()
    return " LIMIT " in f" {upper} " or upper.rstrip().rstrip(";").endswith("LIMIT")


def normalize_llm_sql_output(sql: str | None) -> str:
    """Strip common markdown fences (```sql … ```) so sqlparse sees a plain SELECT."""
    if not sql:
        return ""
    t = sql.strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if not lines:
        return ""
    if lines[0].lstrip().startswith("```"):
        lines = lines[1:]
    while lines and lines[-1].strip() == "```":
        lines.pop()
    return "\n".join(lines).strip()


def is_llm_select_sql_shape(sql: str | None) -> bool:
    """True iff ``sql`` parses as a single SELECT without DDL/DML (shape only; not allowlist)."""
    s = normalize_llm_sql_output(sql)
    if not s.strip():
        return False
    try:
        parsed = sqlparse.parse(s)
    except Exception:
        return False
    if len(parsed) != 1:
        return False
    stype = (parsed[0].get_type() or "").upper()
    if stype != "SELECT":
        return False
    return _DDL_DML.search(s) is None


def strip_trailing_semicolons(sql: str) -> str:
    """Remove trailing semicolons. Spring readonly executor rejects ';' in the query body."""
    s = (sql or "").strip()
    while s.endswith(";"):
        s = s[:-1].rstrip()
    return s


def validate_sql_deterministic(
    sql: str | None,
    settings: GraphSettings,
    *,
    allowlist_tables: set[str] | None = None,
    table_columns: dict[str, set[str]] | None = None,
) -> tuple[bool, str | None, str | None, list[str]]:
    """
    Returns (ok, detail, sanitized_sql, policy_notes).
    If ok, sanitized_sql may inject LIMIT; notes capture hybrid LIMIT policy messages.
    """
    notes: list[str] = []
    if not sql or not sql.strip():
        return False, "empty sql", None, notes
    s = normalize_llm_sql_output(sql)
    if not s:
        return False, "empty sql", None, notes
    s, enum_notes = fix_enum_literals_in_sql(s)
    notes.extend(enum_notes)
    s, name_notes = fix_name_equality_to_ilike(s)
    notes.extend(name_notes)
    parsed = sqlparse.parse(s)
    if len(parsed) != 1:
        return False, "only single statement allowed", None, notes
    stmt = parsed[0]
    stype = (stmt.get_type() or "").upper()
    if stype != "SELECT":
        return False, "only SELECT is allowed", None, notes
    if _DDL_DML.search(s):
        return False, "DDL/DML keywords not allowed", None, notes

    if allowlist_tables is not None:
        allow = allowlist_tables
    else:
        cfg = settings.sql_allowed_tables
        if cfg:
            allow = {t.strip().lower() for t in cfg.split(",") if t.strip()}
        else:
            allow = None

    cte_names = extract_cte_names(s)
    tables = _extract_from_join_tables_stmt(stmt) - cte_names
    if allow is not None:
        if tables and not tables <= allow:
            offending = sorted(tables - allow)
            return (
                False,
                f"table not in allowlist: {offending}. Allowed: {sorted(allow)}",
                None,
                notes,
            )

    if table_columns is not None:
        alias_map = _from_join_alias_map_stmt(stmt)
        col_err = _validate_columns_for_map(
            stmt,
            table_columns=table_columns,
            alias_map=alias_map,
            cte_names=cte_names,
        )
        if col_err:
            return False, col_err, None, notes

    if not _select_has_limit_clause(s):
        lim = settings.sql_limit_max
        s = f"{strip_trailing_semicolons(s)} LIMIT {lim}"
        notes.append("LIMIT injected (was missing)")
    s = strip_trailing_semicolons(s)
    return True, None, s, notes


def check_ledger_metric_policy(
    sql: str | None,
    *,
    metric_id: str | None,
    user_q: str | None,
    enabled: bool,
) -> tuple[bool, str | None]:
    """
    Returns (ok, detail). When enabled, revenue/expense metrics require financeledger in SQL.
    """
    if not enabled or not metric_id or not sql:
        return True, None
    low = sql.lower()
    if metric_id in ("ledger_revenue", "ledger_expense", "ledger_net_cashflow", "ledger_by_dimension"):
        if "financeledger" not in low:
            return False, (
                "policy: metric requires financeledger as fact table "
                f"(metric_id={metric_id})"
            )
    if metric_id in ("ledger_revenue", "ledger_expense") and "financeledger" in low:
        if metric_id == "ledger_revenue" and "salesrevenue" not in low.replace(" ", "").replace("_", ""):
            if "transaction_type" in low and "salesrevenue" not in low:
                return False, "policy: ledger_revenue should filter transaction_type SalesRevenue"
    if "salesorders" in low and "financeledger" in low:
        from app.graph.reference_joins import salesorders_join_requires_reference_type

        if salesorders_join_requires_reference_type(sql):
            return False, (
                "policy: when joining salesorders from financeledger, "
                "include reference_type = 'SalesOrder' (and reference_id match)"
            )
    _ = user_q
    return True, None
