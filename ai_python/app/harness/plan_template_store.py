"""Plan template store for the v3 execution tier (SRS-006 FR-11).

A plan template is a *validated, Planner-generated* PlanGraph promoted for reuse
on a normalized intent key, so a common low-risk intent can run a fast-path plan
without invoking the Planner LLM. Hard guarantees:

- Only ``source="planner_generated"`` plans that passed eval may be promoted
  (FR-11.7) — never hand-authored routes.
- Every template pins ``manifest_version`` + ``policy_version`` + K asset
  versions; any mismatch invalidates the template (FR-11.8).
- A degraded/failed outcome demotes the template so it is no longer preferred
  (FR-11.3, anti-poisoning).
- Tiering is an optimization only; the runtime still runs the template through
  full Harness policy/validation (FR-11.4).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.harness.plan_graph import PlanGraph

PLANNER_GENERATED = "planner_generated"


def normalize_intent_key(text: str) -> str:
    """Stable, lowercased, whitespace-collapsed key for matching common intents."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    return cleaned


def plan_graph_hash(plan: PlanGraph) -> str:
    payload = [
        {
            "id": n.id,
            "tool": n.tool,
            "needs": sorted(n.needs),
            "input_spec": n.input_spec,
            "output_expect": n.output_expect,
        }
        for n in sorted(plan.nodes, key=lambda x: x.id)
    ]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class PlanTemplateRecord(BaseModel):
    normalized_intent_key: str
    plan_graph_hash: str
    plan_graph: PlanGraph
    manifest_version: str
    policy_version: str
    asset_versions: dict[str, str] = Field(default_factory=dict)
    role_scope: str = "owner"
    source: str = ""
    success_count: int = 0
    degraded_count: int = 0
    failure_count: int = 0

    @property
    def demoted(self) -> bool:
        """A template that ever degraded or failed is no longer preferred."""
        return self.degraded_count > 0 or self.failure_count > 0

    def versions_match(
        self, *, manifest_version: str, policy_version: str, asset_versions: dict[str, str]
    ) -> bool:
        return (
            self.manifest_version == manifest_version
            and self.policy_version == policy_version
            and self.asset_versions == dict(asset_versions or {})
        )


def _key(normalized_intent_key: str, role_scope: str) -> str:
    return f"{role_scope}::{normalized_intent_key}"


class PlanTemplateStore(Protocol):
    def promote(self, record: PlanTemplateRecord) -> bool:
        ...

    def get(
        self,
        normalized_intent_key: str,
        *,
        role_scope: str,
        manifest_version: str,
        policy_version: str,
        asset_versions: dict[str, str],
    ) -> PlanTemplateRecord | None:
        ...

    def record_outcome(self, normalized_intent_key: str, *, role_scope: str, status: str) -> None:
        ...


class InMemoryPlanTemplateStore:
    def __init__(self) -> None:
        self._store: dict[str, PlanTemplateRecord] = {}

    def promote(self, record: PlanTemplateRecord) -> bool:
        # FR-11.7: provenance gate — reject anything not planner-generated.
        if record.source != PLANNER_GENERATED:
            return False
        self._store[_key(record.normalized_intent_key, record.role_scope)] = record
        return True

    def get(
        self,
        normalized_intent_key: str,
        *,
        role_scope: str,
        manifest_version: str,
        policy_version: str,
        asset_versions: dict[str, str],
    ) -> PlanTemplateRecord | None:
        record = self._store.get(_key(normalize_intent_key(normalized_intent_key), role_scope))
        if record is None:
            return None
        # FR-11.8: version pin — any drift invalidates the template.
        if not record.versions_match(
            manifest_version=manifest_version,
            policy_version=policy_version,
            asset_versions=asset_versions,
        ):
            return None
        # FR-11.3: demoted templates are not preferred.
        if record.demoted:
            return None
        return record

    def record_outcome(self, normalized_intent_key: str, *, role_scope: str, status: str) -> None:
        record = self._store.get(_key(normalize_intent_key(normalized_intent_key), role_scope))
        if record is None:
            return
        if status == "success":
            record.success_count += 1
        elif status == "degraded":
            record.degraded_count += 1
        else:
            record.failure_count += 1


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS plan_templates (
    key TEXT PRIMARY KEY,
    normalized_intent_key TEXT NOT NULL,
    role_scope TEXT NOT NULL,
    record_json TEXT NOT NULL
)
"""


class SqlitePlanTemplateStore:
    """Single-instance / integration store for OQ-6."""

    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(_CREATE_SQL)
        self._conn.commit()

    def promote(self, record: PlanTemplateRecord) -> bool:
        if record.source != PLANNER_GENERATED:
            return False
        key = _key(record.normalized_intent_key, record.role_scope)
        self._conn.execute(
            "INSERT OR REPLACE INTO plan_templates(key, normalized_intent_key, role_scope, record_json)"
            " VALUES (?,?,?,?)",
            (key, record.normalized_intent_key, record.role_scope, record.model_dump_json()),
        )
        self._conn.commit()
        return True

    def _load(self, normalized_intent_key: str, role_scope: str) -> PlanTemplateRecord | None:
        key = _key(normalize_intent_key(normalized_intent_key), role_scope)
        cur = self._conn.execute("SELECT record_json FROM plan_templates WHERE key=?", (key,))
        row = cur.fetchone()
        if row is None:
            return None
        return PlanTemplateRecord.model_validate_json(row[0])

    def get(
        self,
        normalized_intent_key: str,
        *,
        role_scope: str,
        manifest_version: str,
        policy_version: str,
        asset_versions: dict[str, str],
    ) -> PlanTemplateRecord | None:
        record = self._load(normalized_intent_key, role_scope)
        if record is None:
            return None
        if not record.versions_match(
            manifest_version=manifest_version,
            policy_version=policy_version,
            asset_versions=asset_versions,
        ):
            return None
        if record.demoted:
            return None
        return record

    def record_outcome(self, normalized_intent_key: str, *, role_scope: str, status: str) -> None:
        record = self._load(normalized_intent_key, role_scope)
        if record is None:
            return
        if status == "success":
            record.success_count += 1
        elif status == "degraded":
            record.degraded_count += 1
        else:
            record.failure_count += 1
        key = _key(record.normalized_intent_key, record.role_scope)
        self._conn.execute(
            "UPDATE plan_templates SET record_json=? WHERE key=?", (record.model_dump_json(), key)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
