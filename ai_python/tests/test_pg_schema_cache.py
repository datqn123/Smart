"""Schema cache fingerprint/TTL behavior."""

from __future__ import annotations

from app.graph.dbmeta import ColumnMeta
from app.graph.pg_schema_context import SchemaArtifactCache, _SchemaSnapshot


def _snapshot() -> _SchemaSnapshot:
    return _SchemaSnapshot(
        rows=[("customers", "Customer registry")],
        desc_map={"customers": "Customer registry"},
        reg_names={"customers"},
        fk_edges=[],
        cols={"customers": [ColumnMeta(name="id", type="bigint")]},
        pks={"customers": ["id"]},
        fks={"customers": []},
        col_desc_map={},
        sample_rows={},
        distinct_values={},
    )


def test_schema_cache_hit_and_invalidate_on_fingerprint_change() -> None:
    cache = SchemaArtifactCache()
    snap = _snapshot()
    ns = "public.ai_table_description.ai_column_description|x"
    key1 = f"{ns}|fp1"
    cache.set(key1, snap, ttl_seconds=60, max_items=8)
    assert cache.get(key1) is not None

    fp, changed, err = cache.refresh_fingerprint(
        ns,
        check_interval_seconds=1,
        fetch=lambda: "fp1",
    )
    assert fp == "fp1"
    assert changed is False
    assert err is None

    # Force next fingerprint poll immediately.
    cache._fingerprints[ns].checked_at -= 2  # type: ignore[attr-defined]
    fp2, changed2, err2 = cache.refresh_fingerprint(
        ns,
        check_interval_seconds=1,
        fetch=lambda: "fp2",
    )
    assert fp2 == "fp2"
    assert changed2 is True
    assert err2 is None
    assert cache.get(key1) is None


def test_schema_cache_fingerprint_failure_falls_back_to_previous_value() -> None:
    cache = SchemaArtifactCache()
    ns = "public.ai_table_description.ai_column_description|x"
    cache.refresh_fingerprint(
        ns,
        check_interval_seconds=1,
        fetch=lambda: "fp-ok",
    )
    cache._fingerprints[ns].checked_at -= 2  # type: ignore[attr-defined]
    fp, changed, err = cache.refresh_fingerprint(
        ns,
        check_interval_seconds=1,
        fetch=lambda: (_ for _ in ()).throw(RuntimeError("db fingerprint timeout")),
    )
    assert fp == "fp-ok"
    assert changed is False
    assert "timeout" in str(err).lower()
