"""Shared pytest fixtures for ai_python."""

from __future__ import annotations

import pytest

from app.config.graph_settings import GraphSettings
from app.graph.dbmeta import FileSchemaLoader, SchemaArtifact


@pytest.fixture
def patch_pg_schema_v1(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub live Postgres schema builder with packaged v1 YAML (offline graph tests)."""
    art = FileSchemaLoader(None).load("v1")

    def _fake(settings: GraphSettings, user_q: str) -> tuple[SchemaArtifact | None, str | None]:
        _ = settings, user_q
        return art, None

    monkeypatch.setattr(
        "app.graph.pg_schema_context.build_schema_artifact_from_postgres",
        _fake,
    )
