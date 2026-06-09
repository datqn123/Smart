"""Live PostgreSQL schema for gen_sql: ai_table_description + introspection (Task007+)."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import logging
import re
import threading
from threading import RLock
from time import monotonic
from typing import Any

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import ColumnMeta, SchemaArtifact, TableMeta

try:
    from psycopg2 import sql as pysql
except ImportError:
    pysql = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _SchemaSnapshot:
    rows: list[tuple[str, str]]
    desc_map: dict[str, str]
    reg_names: set[str]
    fk_edges: list[tuple[str, str, str, str]]
    cols: dict[str, list[ColumnMeta]]
    pks: dict[str, list[str]]
    fks: dict[str, list[dict[str, Any]]]
    col_desc_map: dict[tuple[str, str], str]
    rel_desc_map: dict[tuple[str, str, str, str], str]
    sample_rows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    distinct_values: dict[str, dict[str, list[str]]] = field(default_factory=dict)


@dataclass
class _CacheEntry:
    snapshot: _SchemaSnapshot
    expires_at: float


@dataclass
class _FingerprintState:
    value: str | None
    checked_at: float


class SchemaArtifactCache:
    """Process-local LRU+TTL cache keyed by schema namespace + db fingerprint."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._items: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._fingerprints: dict[str, _FingerprintState] = {}

    def get(self, key: str) -> _SchemaSnapshot | None:
        now = monotonic()
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return entry.snapshot

    def set(self, key: str, snapshot: _SchemaSnapshot, *, ttl_seconds: int, max_items: int) -> None:
        now = monotonic()
        with self._lock:
            self._items[key] = _CacheEntry(
                snapshot=snapshot,
                expires_at=now + max(1, int(ttl_seconds)),
            )
            self._items.move_to_end(key)
            while len(self._items) > max(1, int(max_items)):
                self._items.popitem(last=False)

    def refresh_fingerprint(
        self,
        namespace: str,
        *,
        check_interval_seconds: int,
        fetch: Any,
    ) -> tuple[str | None, bool, str | None]:
        now = monotonic()
        with self._lock:
            prev = self._fingerprints.get(namespace)
            if prev is not None and (now - prev.checked_at) < max(1, int(check_interval_seconds)):
                return prev.value, False, None
        try:
            value = fetch()
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            with self._lock:
                prev = self._fingerprints.get(namespace)
                if prev is not None:
                    self._fingerprints[namespace] = _FingerprintState(value=prev.value, checked_at=now)
                    return prev.value, False, msg
            return None, False, msg
        changed = False
        with self._lock:
            prev = self._fingerprints.get(namespace)
            prev_val = prev.value if prev is not None else None
            self._fingerprints[namespace] = _FingerprintState(value=value, checked_at=now)
            changed = prev_val is not None and value is not None and value != prev_val
            if changed:
                stale = [k for k in self._items.keys() if k.startswith(namespace + "|")]
                for k in stale:
                    self._items.pop(k, None)
        return value, changed, None


_SCHEMA_CACHE = SchemaArtifactCache()


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


def _fetch_relationship_descriptions(
    cur: Any, *, schema: str, registry_table: str
) -> list[dict[str, str]]:
    """Fetch business descriptions for FK relationships from ai_relationship_description."""
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", schema) or not re.match(
        r"^[A-Za-z_][A-Za-z0-9_]*$", registry_table
    ):
        raise ValueError("invalid schema or registry_table identifier for ai_relationship_description")
    q = f"""
        SELECT from_table, from_column, to_table, to_column, COALESCE(description, '')
        FROM {schema}.{registry_table}
        ORDER BY from_table, from_column
    """
    cur.execute(q)
    return [
        {
            "from_table": str(r[0]),
            "from_column": str(r[1]),
            "to_table": str(r[2]) if r[2] else "",
            "to_column": str(r[3]) if r[3] else "",
            "description": str(r[4]),
        }
        for r in cur.fetchall()
    ]


def _rank_tables(user_q: str, rows: list[tuple[str, str]], *, max_tables: int) -> list[str]:
    if not rows:
        return []
    q = user_q.lower()
    order_boost = 0.0
    if any(
        p in q
        for p in (
            "đơn hàng",
            "don hang",
            "đơn bán",
            "don ban",
            "bán lẻ",
            "ban le",
            "retail",
            "pos",
            "kênh bán",
        )
    ):
        order_boost = 25.0
    dispatch_boost = 0.0
    if any(p in q for p in ("xuất kho", "xuat kho", "dispatch", "giao hàng", "giao hang")):
        dispatch_boost = 22.0
    ledger_boost = 0.0
    if any(p in q for p in ("doanh thu", "chi phí", "chi phi", "sổ cái", "so cai", "financeledger")):
        ledger_boost = 22.0

    scored: list[tuple[float, str]] = []
    for name, desc in rows:
        score = 0.0
        nl = name.lower()
        if nl == "salesorders" and order_boost:
            score += order_boost
        if nl == "stockdispatches" and dispatch_boost:
            score += dispatch_boost
        if nl == "financeledger" and ledger_boost:
            score += ledger_boost
        if nl in q:
            score += 12.0
        if nl == "salesorders" and ("đơn" in q or "don" in q) and ("hàng" in q or "hang" in q or "bán" in q):
            score += 15.0
        desc_l = desc.lower()
        if nl == "salesorders" and ("đơn bán" in desc_l or "đơn hàng" in desc_l):
            if "đơn" in q or "hàng" in q or "bán" in q:
                score += 8.0
        for tok in re.findall(r"\w+", desc_l):
            if len(tok) > 2 and tok in q:
                score += 2.0
        for part in re.findall(r"\w+", q):
            pl = part.lower()
            if len(pl) > 2 and pl in desc_l:
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


def _cache_namespace(settings: GraphSettings, dsn: str) -> str:
    schema = (settings.pg_metadata_schema or "public").strip().lower()
    desc_table = (settings.pg_ai_description_table or "ai_table_description").strip().lower()
    col_desc_table = (settings.pg_ai_column_description_table or "ai_column_description").strip().lower()
    return f"{schema}.{desc_table}.{col_desc_table}|{abs(hash(dsn))}"


def _fetch_registry_updated_at_fingerprint(
    cur: Any,
    *,
    schema: str,
    table_name: str,
) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", schema) or not re.match(
        r"^[A-Za-z_][A-Za-z0-9_]*$",
        table_name,
    ):
        raise ValueError("invalid schema or table identifier for fingerprint query")
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = 'updated_at'
        )
        """,
        (schema, table_name),
    )
    exists = bool(cur.fetchone()[0])
    if not exists:
        return "no_updated_at"
    cur.execute(
        f"SELECT COALESCE(MAX(updated_at)::text, 'null') FROM {schema}.{table_name}"  # noqa: S608
    )
    row = cur.fetchone()
    return str(row[0]) if row and row[0] is not None else "null"


def _fetch_migration_fingerprint(cur: Any, *, schema: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", schema):
        raise ValueError("invalid schema identifier for migration fingerprint")
    cur.execute(
        "SELECT to_regclass(%s)",
        (f"{schema}.flyway_schema_history",),
    )
    reg = cur.fetchone()
    if not reg or reg[0] is None:
        return "no_flyway"
    cur.execute(
        f"""  -- noqa: S608
        SELECT COALESCE(MAX(version::text), ''),
               COALESCE(MAX(installed_rank)::text, '')
        FROM {schema}.flyway_schema_history
        WHERE success = TRUE
        """
    )
    row = cur.fetchone()
    if not row:
        return "empty_flyway"
    return f"{row[0] or ''}:{row[1] or ''}"


def _build_db_fingerprint(
    cur: Any,
    *,
    schema: str,
    desc_table: str,
    col_desc_table: str,
) -> str:
    desc_fp = _fetch_registry_updated_at_fingerprint(cur, schema=schema, table_name=desc_table)
    col_fp = _fetch_registry_updated_at_fingerprint(cur, schema=schema, table_name=col_desc_table)
    mig_fp = _fetch_migration_fingerprint(cur, schema=schema)
    return f"desc={desc_fp}|col={col_fp}|flyway={mig_fp}"


def _introspect_sample_rows(
    cur: Any, schema: str, table: str, limit: int = 5,
) -> list[dict[str, Any]]:
    safe_name = pysql.Identifier(schema, table)
    cur.execute(pysql.SQL("SELECT * FROM {} LIMIT %s").format(safe_name), (limit,))
    col_names = [desc[0] for desc in cur.description] if cur.description else []
    rows: list[dict[str, Any]] = []
    for row in cur.fetchall():
        d: dict[str, Any] = {}
        for i, c in enumerate(col_names):
            val = row[i]
            if isinstance(val, (bytes, bytearray)):
                val = str(val)[:80]
            elif not isinstance(val, (str, int, float, bool, type(None))):
                val = str(val)[:80]
            d[c] = val
        rows.append(d)
    return rows


_CATEGORICAL_TYPE_KEYWORDS = ("char", "text", "enum", "varchar")


def _is_categorical_column(col: ColumnMeta) -> bool:
    if col.name.lower() in ("id", "created_at", "updated_at", "deleted_at"):
        return False
    if col.type is None:
        return False
    t = col.type.lower()
    return any(kw in t for kw in _CATEGORICAL_TYPE_KEYWORDS) and "[]" not in t


def _introspect_distinct_values(
    cur: Any, schema: str, table: str, columns: list[ColumnMeta], limit: int = 100,
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for col in columns:
        if not _is_categorical_column(col):
            continue
        if not pysql:
            continue
        safe_table = pysql.Identifier(schema, table)
        safe_col = pysql.Identifier(col.name)
        try:
            cur.execute(
                pysql.SQL("SELECT DISTINCT {} FROM {} WHERE {} IS NOT NULL ORDER BY 1 LIMIT %s")
                .format(safe_col, safe_table, safe_col),
                (limit,),
            )
            vals = [str(r[0]) for r in cur.fetchall() if r[0] is not None]
            if vals:
                result[col.name] = vals
        except Exception:
            logger.warning("introspect distinct failed for %s.%s", table, col.name)
    return result


def _build_snapshot(
    cur: Any, *, schema: str, desc_table: str, col_desc_table: str,
    introspection_enabled: bool = True,
    sample_limit: int = 5, distinct_limit: int = 100,
) -> _SchemaSnapshot:
    rows = _fetch_descriptions(cur, schema=schema, table=desc_table)
    if not rows:
        raise RuntimeError("ai_table_description has no rows")
    reg_names = {r[0] for r in rows}
    desc_map = {r[0]: r[1] for r in rows}
    all_tables = sorted(reg_names)
    fk_edges = _fetch_fk_edges(cur, schema, reg_names)
    cols = _introspect_columns(cur, schema, all_tables)
    pks = _introspect_pk(cur, schema, all_tables)
    fks = _introspect_fks_for_tables(cur, schema, all_tables)
    col_desc_map: dict[tuple[str, str], str] = {}
    try:
        col_desc_map = _fetch_column_descriptions(
            cur,
            schema=schema,
            registry_table=col_desc_table,
            tables=all_tables,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ai_column_description registry unavailable: %s", exc)
    rel_desc_map: dict[tuple[str, str, str, str], str] = {}
    try:
        raw_rels = _fetch_relationship_descriptions(
            cur,
            schema=schema,
            registry_table=col_desc_table.replace("ai_column_description", "ai_relationship_description"),
        )
        for r in raw_rels:
            key = (r["from_table"].lower(), r["from_column"].lower(),
                   (r["to_table"] or "").lower(), (r["to_column"] or "").lower())
            rel_desc_map[key] = r["description"]
    except Exception as exc:  # noqa: BLE001
        logger.warning("ai_relationship_description unavailable: %s", exc)
    sample_rows: dict[str, list[dict[str, Any]]] = {}
    distinct_values: dict[str, dict[str, list[str]]] = {}
    if introspection_enabled:
        for tname in all_tables:
            t_cols = cols.get(tname)
            if not t_cols:
                continue
            try:
                sample_rows[tname] = _introspect_sample_rows(cur, schema, tname, limit=sample_limit)
            except Exception:
                pass
            try:
                dv = _introspect_distinct_values(cur, schema, tname, t_cols, limit=distinct_limit)
                if dv:
                    distinct_values[tname] = dv
            except Exception:
                pass
    return _SchemaSnapshot(
        rows=rows,
        desc_map=desc_map,
        reg_names=reg_names,
        fk_edges=fk_edges,
        cols=cols,
        pks=pks,
        fks=fks,
        col_desc_map=col_desc_map,
        rel_desc_map=rel_desc_map,
        sample_rows=sample_rows,
        distinct_values=distinct_values,
    )


def _artifact_from_snapshot(
    snapshot: _SchemaSnapshot,
    *,
    user_q: str,
    cap: int,
    source_mode: str,
) -> SchemaArtifact | None:
    seeds = _rank_tables(user_q, snapshot.rows, max_tables=cap)
    tables = _expand_with_fks(seeds, snapshot.fk_edges, cap=cap)
    tmeta: list[TableMeta] = []
    for tname in tables:
        cols = snapshot.cols.get(tname)
        if not cols:
            logger.warning("table %r in registry but no columns in PG — skip", tname)
            continue
        merged_cols: list[ColumnMeta] = []
        for cm in cols:
            key = (tname.lower(), cm.name.lower())
            reg_txt = snapshot.col_desc_map.get(key)
            if reg_txt:
                merged_cols.append(cm.model_copy(update={"description": reg_txt}))
            else:
                merged_cols.append(cm)
        rel_hints: list[str] = []
        for fk in snapshot.fks.get(tname, []):
            key = (tname.lower(), fk.get("column", "").lower(),
                   (fk.get("ref_table") or "").lower(), (fk.get("ref_column") or "").lower())
            desc = snapshot.rel_desc_map.get(key)
            if desc:
                rel_hints.append(f"{fk['column']} → {fk['ref_table']}.{fk['ref_column']}: {desc}")
        tmeta.append(
            TableMeta(
                name=tname,
                columns=merged_cols,
                pk=snapshot.pks.get(tname, []),
                fks=snapshot.fks.get(tname, []),
                description=snapshot.desc_map.get(tname),
                sample_rows=snapshot.sample_rows.get(tname, []),
                distinct_values=snapshot.distinct_values.get(tname, {}),
                relationship_hints=rel_hints,
            )
        )
    if not tmeta:
        return None
    return SchemaArtifact(
        schema_version="postgres_live",
        tables=tmeta,
        source_mode=source_mode,
    )


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

    cache_enabled = bool(settings.schema_cache_enabled)
    cache_key: str | None = None
    namespace = _cache_namespace(settings, dsn)
    snapshot: _SchemaSnapshot | None = None

    if cache_enabled:
        def _fetch_fp() -> str:
            conn_fp = psycopg2.connect(dsn, connect_timeout=timeout)
            try:
                conn_fp.set_session(readonly=True, autocommit=True)
                with conn_fp.cursor() as cur_fp:
                    return _build_db_fingerprint(
                        cur_fp,
                        schema=schema,
                        desc_table=desc_table,
                        col_desc_table=col_desc_table,
                    )
            finally:
                conn_fp.close()

        fp, _changed, fp_err = _SCHEMA_CACHE.refresh_fingerprint(
            namespace,
            check_interval_seconds=int(settings.schema_fingerprint_check_interval_seconds),
            fetch=_fetch_fp,
        )
        if fp_err:
            logger.warning("schema fingerprint unavailable, fallback to TTL cache: %s", fp_err)
        fp_token = fp or "no_fingerprint"
        cache_key = f"{namespace}|{fp_token}"
        snapshot = _SCHEMA_CACHE.get(cache_key)

    if snapshot is None:
        conn = None
        try:
            conn = psycopg2.connect(dsn, connect_timeout=timeout)
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                snapshot = _build_snapshot(
                    cur,
                    schema=schema,
                    desc_table=desc_table,
                    col_desc_table=col_desc_table,
                    introspection_enabled=bool(settings.sql_introspection_enabled),
                    sample_limit=int(settings.sql_introspection_sample_limit),
                    distinct_limit=int(settings.sql_introspection_distinct_limit),
                )
        except Exception as exc:
            logger.warning("pg schema build failed: %s", exc, exc_info=True)
            return None, str(exc)
        finally:
            if conn is not None:
                conn.close()
        if cache_enabled and cache_key is not None and snapshot is not None:
            _SCHEMA_CACHE.set(
                cache_key,
                snapshot,
                ttl_seconds=int(settings.schema_cache_ttl_seconds),
                max_items=int(settings.schema_cache_max_items),
            )

    if snapshot is None:
        return None, "schema snapshot unavailable"
    art = _artifact_from_snapshot(
        snapshot,
        user_q=user_q,
        cap=cap,
        source_mode="postgres_ai_table_description",
    )
    if art is None:
        return None, "no introspected tables after registry match"
    return art, None


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
    cache_enabled = bool(settings.schema_cache_enabled)
    namespace = _cache_namespace(settings, dsn)
    cache_key: str | None = None
    snapshot: _SchemaSnapshot | None = None
    if cache_enabled:
        def _fetch_fp() -> str:
            conn_fp = psycopg2.connect(dsn, connect_timeout=timeout)
            try:
                conn_fp.set_session(readonly=True, autocommit=True)
                with conn_fp.cursor() as cur_fp:
                    return _build_db_fingerprint(
                        cur_fp,
                        schema=schema,
                        desc_table=desc_table,
                        col_desc_table=(settings.pg_ai_column_description_table or "ai_column_description").strip(),
                    )
            finally:
                conn_fp.close()

        fp, _changed, fp_err = _SCHEMA_CACHE.refresh_fingerprint(
            namespace,
            check_interval_seconds=int(settings.schema_fingerprint_check_interval_seconds),
            fetch=_fetch_fp,
        )
        if fp_err:
            logger.warning("schema fingerprint unavailable, fallback to TTL cache: %s", fp_err)
        cache_key = f"{namespace}|{fp or 'no_fingerprint'}"
        snapshot = _SCHEMA_CACHE.get(cache_key)
    if snapshot is None:
        conn = None
        try:
            conn = psycopg2.connect(dsn, connect_timeout=timeout)
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                snapshot = _build_snapshot(
                    cur,
                    schema=schema,
                    desc_table=desc_table,
                    col_desc_table=(settings.pg_ai_column_description_table or "ai_column_description").strip(),
                    introspection_enabled=bool(settings.sql_introspection_enabled),
                    sample_limit=int(settings.sql_introspection_sample_limit),
                    distinct_limit=int(settings.sql_introspection_distinct_limit),
                )
        except Exception as exc:
            return [], str(exc)
        finally:
            if conn is not None:
                conn.close()
        if cache_enabled and cache_key is not None and snapshot is not None:
            _SCHEMA_CACHE.set(
                cache_key,
                snapshot,
                ttl_seconds=int(settings.schema_cache_ttl_seconds),
                max_items=int(settings.schema_cache_max_items),
            )
    if snapshot is None:
        return [], "schema snapshot unavailable"
    return list(snapshot.rows), None


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
    cache_enabled = bool(settings.schema_cache_enabled)
    namespace = _cache_namespace(settings, dsn)
    cache_key: str | None = None
    snapshot: _SchemaSnapshot | None = None
    if cache_enabled:
        def _fetch_fp() -> str:
            conn_fp = psycopg2.connect(dsn, connect_timeout=timeout)
            try:
                conn_fp.set_session(readonly=True, autocommit=True)
                with conn_fp.cursor() as cur_fp:
                    return _build_db_fingerprint(
                        cur_fp,
                        schema=schema,
                        desc_table=desc_table,
                        col_desc_table=col_desc_table,
                    )
            finally:
                conn_fp.close()

        fp, _changed, fp_err = _SCHEMA_CACHE.refresh_fingerprint(
            namespace,
            check_interval_seconds=int(settings.schema_fingerprint_check_interval_seconds),
            fetch=_fetch_fp,
        )
        if fp_err:
            logger.warning("schema fingerprint unavailable, fallback to TTL cache: %s", fp_err)
        cache_key = f"{namespace}|{fp or 'no_fingerprint'}"
        snapshot = _SCHEMA_CACHE.get(cache_key)
    if snapshot is None:
        conn = None
        try:
            conn = psycopg2.connect(dsn, connect_timeout=timeout)
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                snapshot = _build_snapshot(
                    cur,
                    schema=schema,
                    desc_table=desc_table,
                    col_desc_table=col_desc_table,
                    introspection_enabled=bool(settings.sql_introspection_enabled),
                    sample_limit=int(settings.sql_introspection_sample_limit),
                    distinct_limit=int(settings.sql_introspection_distinct_limit),
                )
        except Exception as exc:
            logger.warning("pg schema build for tables failed: %s", exc, exc_info=True)
            return None, str(exc)
        finally:
            if conn is not None:
                conn.close()
        if cache_enabled and cache_key is not None and snapshot is not None:
            _SCHEMA_CACHE.set(
                cache_key,
                snapshot,
                ttl_seconds=int(settings.schema_cache_ttl_seconds),
                max_items=int(settings.schema_cache_max_items),
            )
    if snapshot is None:
        return None, "schema snapshot unavailable"

    reg_lower = {r[0].lower(): r[0] for r in snapshot.rows}
    tables: list[str] = []
    for n in names:
        canon = reg_lower.get(n.lower())
        if canon and canon not in tables:
            tables.append(canon)
    if not tables:
        return None, "requested tables not in ai_table_description registry"
    tmeta: list[TableMeta] = []
    for tname in tables:
        cols = snapshot.cols.get(tname)
        if not cols:
            logger.warning("table %r in registry but no columns in PG — skip", tname)
            continue
        merged_cols: list[ColumnMeta] = []
        for cm in cols:
            key = (tname.lower(), cm.name.lower())
            reg_txt = snapshot.col_desc_map.get(key)
            if reg_txt:
                merged_cols.append(cm.model_copy(update={"description": reg_txt}))
            else:
                merged_cols.append(cm)
        tmeta.append(
            TableMeta(
                name=tname,
                columns=merged_cols,
                pk=snapshot.pks.get(tname, []),
                fks=snapshot.fks.get(tname, []),
                description=snapshot.desc_map.get(tname),
                sample_rows=snapshot.sample_rows.get(tname, []),
                distinct_values=snapshot.distinct_values.get(tname, {}),
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


class SchemaWarmupWarmer:
    """Build schema + introspection cache at startup for zero-latency first query."""

    def __init__(self, settings: GraphSettings) -> None:
        self._settings = settings
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if not self._settings.sql_introspection_warmup_enabled:
            logger.info("schema warmup disabled by config")
            return
        dsn = _metadata_dsn(self._settings)
        if not dsn:
            logger.info("schema warmup skipped — no metadata DSN configured")
            return
        self._thread = threading.Thread(target=self._run, name="schema-warmer", daemon=True)
        self._thread.start()
        logger.info("schema warmup thread started")

    def _run(self) -> None:
        try:
            import psycopg2
        except ImportError:
            logger.warning("schema warmup: psycopg2 not installed")
            return
        dsn = _metadata_dsn(self._settings)
        schema = (self._settings.pg_metadata_schema or "public").strip()
        desc_table = (self._settings.pg_ai_description_table or "ai_table_description").strip()
        col_desc_table = (self._settings.pg_ai_column_description_table or "ai_column_description").strip()
        timeout = int(self._settings.pg_metadata_connect_timeout_seconds)
        try:
            conn = psycopg2.connect(dsn, connect_timeout=timeout)
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                snapshot = _build_snapshot(
                    cur, schema=schema, desc_table=desc_table, col_desc_table=col_desc_table,
                    introspection_enabled=bool(self._settings.sql_introspection_enabled),
                    sample_limit=int(self._settings.sql_introspection_sample_limit),
                    distinct_limit=int(self._settings.sql_introspection_distinct_limit),
                )
                fp = _build_db_fingerprint(
                    cur, schema=schema, desc_table=desc_table, col_desc_table=col_desc_table,
                )
            conn.close()
            namespace = _cache_namespace(self._settings, dsn)
            cache_key = f"{namespace}|{fp}" if fp else f"{namespace}|warmup"
            _SCHEMA_CACHE.set(
                cache_key, snapshot,
                ttl_seconds=int(self._settings.schema_cache_ttl_seconds),
                max_items=int(self._settings.schema_cache_max_items),
            )
            logger.info("schema warmup complete (tables=%d)", len(snapshot.reg_names))
        except Exception:
            logger.warning("schema warmup failed — will lazy-build on first query", exc_info=True)
