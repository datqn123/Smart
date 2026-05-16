"""Live PostgreSQL schema for gen_sql: ai_table_description + introspection (Task007+)."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import ColumnMeta, SchemaArtifact, TableMeta

logger = logging.getLogger(__name__)


def _metadata_dsn(settings: GraphSettings) -> str | None:
    u = settings.database_url_metadata_ro or settings.database_url_ro
    if u and str(u).strip():
        return str(u).strip()
    return None


def _fetch_descriptions(cur: Any, *, schema: str, table: str) -> list[tuple[str, str]]:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", schema) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", table):
        raise ValueError("invalid schema or table identifier for ai_table_description query")
    q = f"SELECT table_name, COALESCE(description, '') FROM {schema}.{table} ORDER BY table_name"
    cur.execute(q)
    return [(str(r[0]), str(r[1])) for r in cur.fetchall()]


def _fetch_column_descriptions(
    cur: Any, *, schema: str, registry_table: str, tables: list[str]
) -> dict[tuple[str, str], str]:
    """(table_name_lower, column_name_lower) -> trimmed description from ai_column_description."""
    if not tables:
        return {}
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", schema) or not re.match(
        r"^[A-Za-z_][A-Za-z0-9_]*$", registry_table
    ):
        raise ValueError("invalid schema or registry_table identifier for ai_column_description query")
    q = f"""
        SELECT table_name, column_name, COALESCE(description, '')
        FROM {schema}.{registry_table}
        WHERE table_name = ANY(%s::text[])
        """
    cur.execute(q, (tables,))
    out: dict[tuple[str, str], str] = {}
    for tbl, col, desc in cur.fetchall():
        t = str(tbl).strip().lower()
        c = str(col).strip().lower()
        d = str(desc).strip()
        if t and c and d:
            out[(t, c)] = d
    return out


def _rank_tables(user_q: str, rows: list[tuple[str, str]], *, max_tables: int) -> list[str]:
    if not rows:
        return []
    q = user_q.lower()
    scored: list[tuple[float, str]] = []
    for name, desc in rows:
        score = 0.0
        nl = name.lower()
        if nl in q:
            score += 12.0
        for tok in re.findall(r"\w+", desc.lower()):
            if len(tok) > 2 and tok in q:
                score += 2.0
        for part in re.findall(r"\w+", q):
            pl = part.lower()
            if len(pl) > 2 and pl in desc.lower():
                score += 2.5
        for tok in re.findall(r"\w+", nl):
            if len(tok) > 2 and tok in q:
                score += 1.5
        scored.append((score, name))
    scored.sort(key=lambda x: -x[0])
    picked = [n for s, n in scored if s > 0.0][:max_tables]
    if not picked:
        picked = [n for _, n in scored[:max_tables]]
    return picked


def _fetch_fk_edges(cur: Any, schema: str, reg_tables: set[str]) -> list[tuple[str, str, str, str]]:
    """from_table, from_col, to_table, to_col — only FKs where both ends are in registry."""
    if not reg_tables:
        return []
    cur.execute(
        """
        SELECT c.relname::text AS src_table,
               a.attname::text AS src_col,
               fc.relname::text AS tgt_table,
               fa.attname::text AS tgt_col
        FROM pg_constraint co
        JOIN pg_class c ON c.oid = co.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_class fc ON fc.oid = co.confrelid
        JOIN LATERAL unnest(co.conkey) WITH ORDINALITY AS u(attnum, ord) ON TRUE
        JOIN LATERAL UNNEST(co.confkey) WITH ORDINALITY AS v(attnum2, ord2) ON u.ord = v.ord2
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = u.attnum AND NOT a.attisdropped
        JOIN pg_attribute fa ON fa.attrelid = fc.oid AND fa.attnum = v.attnum2 AND NOT fa.attisdropped
        WHERE co.contype = 'f'
          AND n.nspname = %s
          AND c.relname = ANY(%s::text[])
          AND fc.relname = ANY(%s::text[])
        """,
        (schema, list(reg_tables), list(reg_tables)),
    )
    return [(str(r[0]), str(r[1]), str(r[2]), str(r[3])) for r in cur.fetchall()]


def _expand_with_fks(seeds: list[str], fk_edges: list[tuple[str, str, str, str]], *, cap: int) -> list[str]:
    sset = list(dict.fromkeys(seeds))  # preserve order, unique
    known = set(sset)
    changed = True
    while changed and len(sset) < cap:
        changed = False
        for ft, _, tt, _ in fk_edges:
            if ft in known and tt not in known and len(sset) < cap:
                sset.append(tt)
                known.add(tt)
                changed = True
            if tt in known and ft not in known and len(sset) < cap:
                sset.append(ft)
                known.add(ft)
                changed = True
    return sset[:cap]


def _introspect_columns(cur: Any, schema: str, tables: list[str]) -> dict[str, list[ColumnMeta]]:
    if not tables:
        return {}
    cur.execute(
        """
        SELECT table_name::text, column_name::text, data_type::text
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = ANY(%s::text[])
        ORDER BY table_name, ordinal_position
        """,
        (schema, tables),
    )
    out: dict[str, list[ColumnMeta]] = {}
    for tbl, col, dtype in cur.fetchall():
        out.setdefault(tbl, []).append(ColumnMeta(name=col, type=dtype, allowlist=True))
    return out


def _introspect_pk(cur: Any, schema: str, tables: list[str]) -> dict[str, list[str]]:
    if not tables:
        return {}
    cur.execute(
        """
        SELECT kcu.table_name::text, kcu.column_name::text
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_schema = kcu.constraint_schema
         AND tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = %s
          AND tc.constraint_type = 'PRIMARY KEY'
          AND kcu.table_name = ANY(%s::text[])
        ORDER BY kcu.table_name, kcu.ordinal_position
        """,
        (schema, tables),
    )
    pks: dict[str, list[str]] = {}
    for tbl, col in cur.fetchall():
        pks.setdefault(tbl, []).append(col)
    return pks


def _introspect_fks_for_tables(
    cur: Any, schema: str, tables: list[str]
) -> dict[str, list[dict[str, Any]]]:
    """table_name -> list of {column, ref_table, ref_column}."""
    if not tables:
        return {}
    cur.execute(
        """
        SELECT c.relname::text AS src_table,
               a.attname::text AS src_col,
               fc.relname::text AS tgt_table,
               fa.attname::text AS tgt_col
        FROM pg_constraint co
        JOIN pg_class c ON c.oid = co.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_class fc ON fc.oid = co.confrelid
        JOIN LATERAL unnest(co.conkey) WITH ORDINALITY AS u(attnum, ord) ON TRUE
        JOIN LATERAL UNNEST(co.confkey) WITH ORDINALITY AS v(attnum2, ord2) ON u.ord = v.ord2
        JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = u.attnum AND NOT a.attisdropped
        JOIN pg_attribute fa ON fa.attrelid = fc.oid AND fa.attnum = v.attnum2 AND NOT fa.attisdropped
        WHERE co.contype = 'f'
          AND n.nspname = %s
          AND c.relname = ANY(%s::text[])
        """,
        (schema, tables),
    )
    fks: dict[str, list[dict[str, Any]]] = {}
    for st, sc, tt, tc in cur.fetchall():
        fks.setdefault(st, []).append({"column": sc, "ref_table": tt, "ref_column": tc})
    return fks


def build_schema_artifact_from_postgres(
    settings: GraphSettings,
    user_q: str,
) -> tuple[SchemaArtifact | None, str | None]:
    """
    Read ai_table_description, optional ai_column_description, rank tables, introspect columns/PK/FK.

    Returns (artifact, error_message). On recoverable empty/error returns (None, msg).
    """
    try:
        import psycopg2
    except ImportError:
        return None, "psycopg2 not installed (add psycopg2-binary to requirements)"

    dsn = _metadata_dsn(settings)
    if not dsn:
        return None, "DATABASE_URL_METADATA_RO or DATABASE_URL_RO is required for postgres schema source"

    schema = (settings.pg_metadata_schema or "public").strip()
    desc_table = (settings.pg_ai_description_table or "ai_table_description").strip()
    col_desc_table = (settings.pg_ai_column_description_table or "ai_column_description").strip()
    timeout = int(settings.pg_metadata_connect_timeout_seconds)
    cap = int(settings.sql_max_selected_tables)

    conn = None
    try:
        conn = psycopg2.connect(dsn, connect_timeout=timeout)
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            rows = _fetch_descriptions(cur, schema=schema, table=desc_table)
            if not rows:
                return None, "ai_table_description has no rows"
            reg_names = {r[0] for r in rows}
            desc_map = {r[0]: r[1] for r in rows}
            seeds = _rank_tables(user_q, rows, max_tables=cap)
            fk_edges = _fetch_fk_edges(cur, schema, reg_names)
            tables = _expand_with_fks(seeds, fk_edges, cap=cap)
            cols = _introspect_columns(cur, schema, tables)
            col_desc_map: dict[tuple[str, str], str] = {}
            try:
                col_desc_map = _fetch_column_descriptions(
                    cur, schema=schema, registry_table=col_desc_table, tables=tables
                )
            except Exception as exc:
                logger.warning("ai_column_description registry unavailable: %s", exc)
            pks = _introspect_pk(cur, schema, tables)
            fks = _introspect_fks_for_tables(cur, schema, tables)
            tmeta: list[TableMeta] = []
            for tname in tables:
                if tname not in cols:
                    logger.warning("table %r in registry but no columns in PG — skip", tname)
                    continue
                merged_cols: list[ColumnMeta] = []
                for cm in cols[tname]:
                    key = (tname.lower(), cm.name.lower())
                    reg_txt = col_desc_map.get(key)
                    if reg_txt:
                        merged_cols.append(cm.model_copy(update={"description": reg_txt}))
                    else:
                        merged_cols.append(cm)
                tmeta.append(
                    TableMeta(
                        name=tname,
                        columns=merged_cols,
                        pk=pks.get(tname, []),
                        fks=fks.get(tname, []),
                        description=desc_map.get(tname),
                    )
                )
            if not tmeta:
                return None, "no introspected tables after registry match"
            art = SchemaArtifact(
                schema_version="postgres_live",
                tables=tmeta,
                source_mode="postgres_ai_table_description",
            )
            return art, None
    except Exception as exc:
        logger.warning("pg schema build failed: %s", exc, exc_info=True)
        return None, str(exc)
    finally:
        if conn is not None:
            conn.close()


def rank_tables_for_question(user_q: str, rows: list[tuple[str, str]], *, max_tables: int) -> list[str]:
    """Public wrapper for unit tests (same logic as internal ranker)."""
    return _rank_tables(user_q, rows, max_tables=max_tables)


def list_registry_tables(settings: GraphSettings) -> tuple[list[tuple[str, str]], str | None]:
    """Return (table_name, description) rows from ai_table_description."""
    try:
        import psycopg2
    except ImportError:
        return [], "psycopg2 not installed"
    dsn = _metadata_dsn(settings)
    if not dsn:
        return [], "DATABASE_URL_METADATA_RO or DATABASE_URL_RO is required"
    schema = (settings.pg_metadata_schema or "public").strip()
    desc_table = (settings.pg_ai_description_table or "ai_table_description").strip()
    timeout = int(settings.pg_metadata_connect_timeout_seconds)
    conn = None
    try:
        conn = psycopg2.connect(dsn, connect_timeout=timeout)
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            return _fetch_descriptions(cur, schema=schema, table=desc_table), None
    except Exception as exc:
        return [], str(exc)
    finally:
        if conn is not None:
            conn.close()


def build_schema_artifact_for_table_names(
    settings: GraphSettings,
    table_names: list[str],
) -> tuple[SchemaArtifact | None, str | None]:
    """Introspect only the given registry tables (schema explorer path)."""
    try:
        import psycopg2
    except ImportError:
        return None, "psycopg2 not installed"
    dsn = _metadata_dsn(settings)
    if not dsn:
        return None, "DATABASE_URL_METADATA_RO or DATABASE_URL_RO is required"
    names = [str(t).strip() for t in table_names if str(t).strip()]
    if not names:
        return None, "no tables requested"
    schema = (settings.pg_metadata_schema or "public").strip()
    desc_table = (settings.pg_ai_description_table or "ai_table_description").strip()
    col_desc_table = (settings.pg_ai_column_description_table or "ai_column_description").strip()
    timeout = int(settings.pg_metadata_connect_timeout_seconds)
    conn = None
    try:
        conn = psycopg2.connect(dsn, connect_timeout=timeout)
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            rows = _fetch_descriptions(cur, schema=schema, table=desc_table)
            desc_map = {r[0]: r[1] for r in rows}
            reg_lower = {r[0].lower(): r[0] for r in rows}
            tables: list[str] = []
            for n in names:
                canon = reg_lower.get(n.lower())
                if canon and canon not in tables:
                    tables.append(canon)
            if not tables:
                return None, "requested tables not in ai_table_description registry"
            cols = _introspect_columns(cur, schema, tables)
            col_desc_map: dict[tuple[str, str], str] = {}
            try:
                col_desc_map = _fetch_column_descriptions(
                    cur, schema=schema, registry_table=col_desc_table, tables=tables
                )
            except Exception as exc:
                logger.warning("ai_column_description registry unavailable: %s", exc)
            pks = _introspect_pk(cur, schema, tables)
            fks = _introspect_fks_for_tables(cur, schema, tables)
            tmeta: list[TableMeta] = []
            for tname in tables:
                if tname not in cols:
                    logger.warning("table %r in registry but no columns in PG — skip", tname)
                    continue
                merged_cols: list[ColumnMeta] = []
                for cm in cols[tname]:
                    key = (tname.lower(), cm.name.lower())
                    reg_txt = col_desc_map.get(key)
                    if reg_txt:
                        merged_cols.append(cm.model_copy(update={"description": reg_txt}))
                    else:
                        merged_cols.append(cm)
                tmeta.append(
                    TableMeta(
                        name=tname,
                        columns=merged_cols,
                        pk=pks.get(tname, []),
                        fks=fks.get(tname, []),
                        description=desc_map.get(tname),
                    )
                )
            if not tmeta:
                return None, "no introspected tables"
            return (
                SchemaArtifact(
                    schema_version="postgres_live",
                    tables=tmeta,
                    source_mode="postgres_schema_explorer",
                ),
                None,
            )
    except Exception as exc:
        logger.warning("pg schema build for tables failed: %s", exc, exc_info=True)
        return None, str(exc)
    finally:
        if conn is not None:
            conn.close()
