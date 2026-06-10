#!/usr/bin/env python3
"""Introspect PostgreSQL → docs/reference/tables/*.md

Usage:
  python scripts/db-docs.py
  python scripts/db-docs.py --db-url postgresql://user:pass@host/db
  python scripts/db-docs.py --out docs/reference/tables

Reads DATABASE_URL_METADATA_RO / DATABASE_URL_RO from ai_python/.env if --db-url omitted.
"""

import os, re, argparse, configparser
from pathlib import Path
from datetime import datetime

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate DB schema documentation")
    p.add_argument("--db-url", help="PostgreSQL connection URL")
    p.add_argument("--out", default="docs/reference/tables", help="Output directory")
    p.add_argument("--schema", default="public", help="DB schema (default: public)")
    return p.parse_args()


def _load_env(path: Path) -> dict:
    """Minimal .env parser (no dependency)."""
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip("\"'")
    return env


def get_db_url(args) -> str:
    url = args.db_url or os.environ.get("DATABASE_URL_METADATA_RO") or os.environ.get("DATABASE_URL_RO")
    if not url:
        env = _load_env(Path("ai_python/.env"))
        url = env.get("DATABASE_URL_METADATA_RO") or env.get("DATABASE_URL_RO")
    if not url:
        url = "postgresql://smart_erp:smart_erp@127.0.0.1:5432/smart_erp"
    return url


def _skip(t: str) -> bool:
    return t.startswith("flyway_") or t in ("schema_migration",)


def fetch_tables(cur, schema: str) -> list[str]:
    cur.execute(
        "SELECT tablename::text FROM pg_tables WHERE schemaname = %s ORDER BY tablename",
        (schema,),
    )
    return [r[0] for r in cur.fetchall() if not _skip(r[0])]


def fetch_columns(cur, schema: str, tables: list[str]) -> dict:
    if not tables:
        return {}
    cur.execute(
        """SELECT c.table_name::text, c.column_name::text, c.data_type::text,
                  c.is_nullable::text, c.column_default::text,
                  c.character_maximum_length::int, c.ordinal_position::int
           FROM information_schema.columns c
           WHERE c.table_schema = %s AND c.table_name = ANY(%s::text[])
           ORDER BY c.table_name, c.ordinal_position""",
        (schema, tables),
    )
    out: dict = {}
    for r in cur.fetchall():
        out.setdefault(r[0], []).append(r)
    return out


def fetch_pks(cur, schema: str, tables: list[str]) -> dict[str, set[str]]:
    if not tables:
        return {}
    cur.execute(
        """SELECT kcu.table_name::text, kcu.column_name::text
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu USING (constraint_schema, constraint_name)
           WHERE tc.table_schema = %s AND tc.constraint_type = 'PRIMARY KEY'
             AND kcu.table_name = ANY(%s::text[])
           ORDER BY kcu.table_name, kcu.ordinal_position""",
        (schema, tables),
    )
    pks: dict[str, set[str]] = {}
    for t, c in cur.fetchall():
        pks.setdefault(t, set()).add(c)
    return pks


def fetch_unique_cols(cur, schema: str, tables: list[str]) -> dict[str, set[str]]:
    """Return set of column names that are part of a single-column UNIQUE constraint."""
    if not tables:
        return {}
    cur.execute(
        """SELECT table_name, column_name
           FROM (
               SELECT kcu.table_name::text, kcu.column_name::text,
                      COUNT(*) OVER (PARTITION BY kcu.table_name, kcu.constraint_name) AS cnt
               FROM information_schema.table_constraints tc
               JOIN information_schema.key_column_usage kcu USING (constraint_schema, constraint_name)
               WHERE tc.table_schema = %s AND tc.constraint_type = 'UNIQUE'
                 AND kcu.table_name = ANY(%s::text[])
           ) sub
           WHERE sub.cnt = 1""",
        (schema, tables),
    )
    out: dict[str, set[str]] = {}
    for t, c in cur.fetchall():
        out.setdefault(t, set()).add(c)
    return out


def fetch_fks(cur, schema: str, tables: list[str]) -> dict[str, dict[str, tuple]]:
    if not tables:
        return {}
    cur.execute(
        """SELECT kcu.table_name::text, kcu.column_name::text,
                  ccu.table_name::text, ccu.column_name::text
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu
             ON tc.constraint_catalog = kcu.constraint_catalog
            AND tc.constraint_schema  = kcu.constraint_schema
            AND tc.constraint_name    = kcu.constraint_name
           JOIN information_schema.constraint_column_usage ccu
             ON tc.constraint_catalog = ccu.constraint_catalog
            AND tc.constraint_schema  = ccu.constraint_schema
            AND tc.constraint_name    = ccu.constraint_name
           WHERE tc.constraint_type = 'FOREIGN KEY'
             AND tc.table_schema = %s AND kcu.table_name = ANY(%s::text[])
           ORDER BY kcu.table_name, kcu.ordinal_position""",
        (schema, tables),
    )
    fks: dict = {}
    for t, c, rt, rc in cur.fetchall():
        fks.setdefault(t, {})[c] = (rt, rc)
    return fks


def fetch_indexes(cur, schema: str, tables: list[str]) -> list[tuple]:
    if not tables:
        return []
    cur.execute(
        """SELECT i.tablename::text, i.indexname::text, i.indexdef::text
           FROM pg_indexes i
           WHERE i.schemaname = %s AND i.tablename = ANY(%s::text[])
             AND i.indexname NOT LIKE %s
           ORDER BY i.tablename, i.indexname""",
        (schema, tables, '%_pkey'),
    )
    rows = cur.fetchall()
    out = []
    for tbl, name, defn in rows:
        m = re.search(r"\((.+?)\)", defn.split("WHERE")[0])
        cols = m.group(1) if m else ""
        notes = ""
        if "UNIQUE" in defn:
            notes = "UNIQUE"
        if "WHERE" in defn:
            w = defn.split("WHERE", 1)[1].strip().rstrip(")").strip()
            notes = (notes + " " + w) if notes else w
        out.append((tbl, name, cols, notes))
    return out


def fmt_type(raw_type: str, char_max: int | None) -> str:
    t = raw_type.lower()
    if t in ("character varying", "varchar") and char_max:
        return f"VARCHAR({char_max})"
    if t == "character" and char_max:
        return f"CHAR({char_max})"
    if t == "timestamp without time zone":
        return "TIMESTAMP"
    if t == "timestamp with time zone":
        return "TIMESTAMPTZ"
    if t == "time without time zone":
        return "TIME"
    if t == "time with time zone":
        return "TIMETZ"
    if t == "double precision":
        return "DOUBLE PRECISION"
    if t == "real":
        return "REAL"
    if t == "numeric":
        return "NUMERIC"
    if t == "boolean":
        return "BOOLEAN"
    if t == "jsonb":
        return "JSONB"
    if t == "json":
        return "JSON"
    if t == "text":
        return "TEXT"
    if t == "integer":
        return "INT"
    if t == "bigint":
        return "BIGINT"
    if t == "smallint":
        return "SMALLINT"
    if t == "uuid":
        return "UUID"
    if t == "bytea":
        return "BYTEA"
    return raw_type.upper()


def fmt_default(raw: str | None) -> str | None:
    if raw is None:
        return None
    v = raw.strip()
    v = re.sub(r"::\w+(?:\[\])?", "", v)
    v = re.sub(r"\s+", " ", v)
    return v


def build_constraints(col: str, data_type: str, nullable: str, default: str | None,
                       pks: set[str], uniques: set[str], fks: dict) -> str:
    parts = []
    if col in pks:
        parts.append("PRIMARY KEY")
    if col in fks:
        tbl, refcol = fks[col]
        parts.append(f"FK -> {tbl}({refcol})")
    if nullable == "NO":
        parts.append("NOT NULL")
    d = fmt_default(default)
    if d:
        parts.append(f"DEFAULT {d}")
    if col in uniques:
        parts.append("UNIQUE")
    if col == "deleted_at":
        parts.append("(soft delete)")
    return ", ".join(parts)


def gen_core_tables(cols: dict, pks: dict, uniq: dict, fks: dict, path: Path):
    lines = ["# Core Tables\n"]
    for tbl in sorted(cols):
        lines.append(f"## {tbl}")
        lines.append("| Column | Type | Constraints |")
        lines.append("|--------|------|-------------|")
        tbl_pk = pks.get(tbl, set())
        tbl_uq = uniq.get(tbl, set())
        tbl_fk = fks.get(tbl, {})
        for r in cols[tbl]:
            _, col, raw_type, nullable, default, char_max, _ = r
            t = fmt_type(raw_type, char_max)
            c = build_constraints(col, raw_type, nullable, default, tbl_pk, tbl_uq, tbl_fk)
            lines.append(f"| {col} | {t} | {c} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(cols)


def gen_foreign_keys(fks: dict, path: Path):
    rows = []
    for tbl in sorted(fks):
        for col in sorted(fks[tbl]):
            rt, rc = fks[tbl][col]
            rows.append((tbl, col, f"{rt}({rc})"))
    if not rows:
        path.write_text("# Foreign Keys\n\nNo foreign keys found.\n", encoding="utf-8")
        return 0
    lines = ["# Foreign Keys\n", "| Table | Column | References |", "|-------|--------|------------|"]
    for tbl, col, ref in rows:
        lines.append(f"| {tbl} | {col} | {ref} |")
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def gen_indexes(indexes: list, path: Path):
    if not indexes:
        path.write_text("# Indexes\n\nNo indexes found.\n", encoding="utf-8")
        return 0
    lines = ["# Indexes\n", "| Table | Index Name | Columns | Notes |", "|-------|-----------|---------|-------|"]
    for tbl, name, cols, notes in indexes:
        lines.append(f"| {tbl} | {name} | {cols} | {notes} |")
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(indexes)


def gen_readme(out_dir: Path, n_tables: int, n_indexes: int, n_fk: int):
    (out_dir / "README.md").write_text(
        f"# Database Schema Reference\n\n"
        f"Auto-generated from PostgreSQL (`public` schema) — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"| File | Content |\n"
        f"|------|---------|\n"
        f"| `core_tables.md` | {n_tables} tables with columns, types, constraints |\n"
        f"| `indexes.md` | {n_indexes} indexes |\n"
        f"| `foreign_keys.md` | {n_fk} foreign keys |\n",
        encoding="utf-8",
    )


def main():
    args = parse_args()

    if psycopg2 is None:
        print("ERROR: psycopg2 is not installed. Run: pip install psycopg2-binary")
        exit(1)

    db_url = get_db_url(args)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to DB...")
    conn = psycopg2.connect(db_url, connect_timeout=5)
    conn.set_session(readonly=True, autocommit=True)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            ver = cur.fetchone()[0][:60]
            print(f"  {ver}...")

            tables = fetch_tables(cur, args.schema)
            print(f"  Found {len(tables)} tables\nGenerating...")

            cols = fetch_columns(cur, args.schema, tables)
            pks = fetch_pks(cur, args.schema, tables)
            uniq = fetch_unique_cols(cur, args.schema, tables)
            fks = fetch_fks(cur, args.schema, tables)
            indexes = fetch_indexes(cur, args.schema, tables)

            n1 = gen_core_tables(cols, pks, uniq, fks, out_dir / "core_tables.md")
            n2 = gen_indexes(indexes, out_dir / "indexes.md")
            n3 = gen_foreign_keys(fks, out_dir / "foreign_keys.md")
            gen_readme(out_dir, n1, n2, n3)

            print(f"\nDone! Files -> {out_dir.resolve()}")
            print(f"  core_tables.md  ({n1} tables)")
            print(f"  indexes.md      ({n2} indexes)")
            print(f"  foreign_keys.md ({n3} FKs)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
