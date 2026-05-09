from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

ALLOWED_TABLES: frozenset[str] = frozenset({"products", "revenue_daily"})


def allowlist_lower() -> set[str]:
    return {t.lower() for t in ALLOWED_TABLES}


def catalog_snapshot() -> dict[str, Any]:
    """Live-shaped catalog for grounding (demo columns)."""
    now = datetime.now(UTC).isoformat()
    return {
        "ok": True,
        "data_as_of": now,
        "tables": {
            "products": {"columns": ["id", "sku", "qty"]},
            "revenue_daily": {"columns": ["d", "amount"]},
        },
    }


def seed_demo_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            sku TEXT NOT NULL,
            qty INTEGER NOT NULL
        );
        CREATE TABLE revenue_daily (
            d TEXT NOT NULL,
            amount REAL NOT NULL
        );
        INSERT INTO products (id, sku, qty) VALUES
            (1, 'SKU-1', 10),
            (2, 'SKU-2', 3);
        INSERT INTO revenue_daily (d, amount) VALUES
            ('2026-05-01', 1000.0),
            ('2026-05-02', 1205.5);
        """
    )
