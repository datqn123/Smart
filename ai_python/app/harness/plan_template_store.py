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
import logging
import re
import sqlite3
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.harness.plan_graph import PlanGraph

logger = logging.getLogger(__name__)

PLANNER_GENERATED = "planner_generated"


def _req_str(r: object) -> str:
    """Extract a stable string key from a RequiredDataItem or plain string."""
    return str(getattr(r, "field", r))


def normalize_intent_key(text: str) -> str:
    """Stable, lowercased, whitespace-collapsed key for matching common intents."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    return cleaned


def build_intent_key(
    *,
    intent_type: str = "",
    goal: str = "",
    required_data: Any = (),
    entities: Any = (),
    fallback: str = "",
) -> str:
    """Semantic intent key for template lookup + K15 aggregation (SRS-006 LOW-4 fix).

    Built from the structured IntentObject (type + cleaned goal + required data +
    resolved entities) rather than the raw user message, so phrasing variants of
    the same intent share a key. ``goal`` is kept so distinguishing entities such
    as the time window (``tháng này`` vs ``tháng trước``) never collapse together.
    Falls back to the normalized raw question when no intent is available.
    """
    it = str(intent_type or "").strip().lower()
    g = normalize_intent_key(str(goal or ""))
    req = ",".join(sorted(_req_str(r).strip().lower() for r in (required_data or ()) if _req_str(r).strip()))
    ents = ",".join(sorted(str(e).strip().lower() for e in (entities or ()) if str(e).strip()))
    parts = [p for p in (it, g, req, ents) if p]
    return "|".join(parts) or normalize_intent_key(fallback)


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

    def consider_promotion(self, candidate: PlanTemplateRecord, *, promote_after: int) -> bool:
        ...

    def note_non_success(self, normalized_intent_key: str, *, role_scope: str) -> None:
        ...


class InMemoryPlanTemplateStore:
    def __init__(self) -> None:
        self._store: dict[str, PlanTemplateRecord] = {}
        self._candidates: dict[str, PlanTemplateRecord] = {}
        logger.info("template_store_init backend=%s", "memory")

    def promote(self, record: PlanTemplateRecord) -> bool:
        if record.source != PLANNER_GENERATED:
            return False
        self._store[_key(record.normalized_intent_key, record.role_scope)] = record
        logger.info("template_promoted intent=%s plan_hash=%s role=%s after_successes=%s", record.normalized_intent_key, record.plan_graph_hash, record.role_scope, record.success_count)
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
        if record is not None:
            logger.info("template_lookup intent=%s found=%s demoted=%s versions_ok=%s stored_versions=(m=%s,p=%s,a=%s)", normalized_intent_key, True, record.demoted, record.versions_match(manifest_version=manifest_version, policy_version=policy_version, asset_versions=asset_versions), record.manifest_version, record.policy_version, record.asset_versions)
        else:
            logger.info("template_lookup intent=%s found=%s demoted=%s versions_ok=%s stored_versions=(m=%s,p=%s,a=%s)", normalized_intent_key, False, False, False, "", "", {})
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
        if status != "success":
            logger.warning("template_streak_broken intent=%s status=%s counts=(s=%s,d=%s,f=%s)", normalized_intent_key, status, record.success_count, record.degraded_count, record.failure_count)
        if record.demoted:
            logger.warning("template_demoted intent=%s status=%s counts=(s=%s,d=%s,f=%s)", normalized_intent_key, status, record.success_count, record.degraded_count, record.failure_count)

    def consider_promotion(self, candidate: PlanTemplateRecord, *, promote_after: int) -> bool:
        """Track a clean-success streak and promote when it reaches the threshold.

        FR-11.3/11.7: only planner-generated plans are promoted, and only after
        ``promote_after`` consecutive clean successes for the same intent key,
        role, plan hash, and pinned versions.
        """
        if candidate.source != PLANNER_GENERATED:
            return False
        promote_after = max(1, int(promote_after))
        k = _key(normalize_intent_key(candidate.normalized_intent_key), candidate.role_scope)

        active = self._store.get(k)
        if active is not None and active.plan_graph_hash == candidate.plan_graph_hash and active.versions_match(
            manifest_version=candidate.manifest_version,
            policy_version=candidate.policy_version,
            asset_versions=candidate.asset_versions,
        ):
            active.success_count += 1
            self._candidates.pop(k, None)
            return True

        cand = self._candidates.get(k)
        if cand is not None and cand.plan_graph_hash == candidate.plan_graph_hash and cand.versions_match(
            manifest_version=candidate.manifest_version,
            policy_version=candidate.policy_version,
            asset_versions=candidate.asset_versions,
        ):
            cand.success_count += 1
        else:
            cand = candidate.model_copy(update={"success_count": 1})
            self._candidates[k] = cand

        if cand.success_count >= promote_after:
            self.promote(cand.model_copy())
            self._candidates.pop(k, None)
            return True
        accuracy = cand.success_count / promote_after
        logger.info("template_candidate_streak intent=%s plan_hash=%s success_count=%s/%s", candidate.normalized_intent_key, candidate.plan_graph_hash, cand.success_count, promote_after)
        logger.info("template_promotion_blocked accuracy=%.2f below_threshold=%.2f", accuracy, 1.0)
        return False

    def note_non_success(self, normalized_intent_key: str, *, role_scope: str) -> None:
        """A degraded/failed run breaks the promotion streak (FR-11.3 anti-poisoning)."""
        self._candidates.pop(_key(normalize_intent_key(normalized_intent_key), role_scope), None)


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS plan_templates (
    key TEXT PRIMARY KEY,
    normalized_intent_key TEXT NOT NULL,
    role_scope TEXT NOT NULL,
    record_json TEXT NOT NULL
)
"""

_CREATE_CANDIDATES_SQL = """
CREATE TABLE IF NOT EXISTS plan_template_candidates (
    key TEXT PRIMARY KEY,
    record_json TEXT NOT NULL
)
"""


class SqlitePlanTemplateStore:
    """Single-instance / integration store for OQ-6."""

    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(_CREATE_SQL)
        self._conn.execute(_CREATE_CANDIDATES_SQL)
        self._conn.commit()
        logger.info("template_store_init backend=%s", "sqlite")

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
        logger.info("template_promoted intent=%s plan_hash=%s role=%s after_successes=%s", record.normalized_intent_key, record.plan_graph_hash, record.role_scope, record.success_count)
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
        if record is not None:
            logger.info("template_lookup intent=%s found=%s demoted=%s versions_ok=%s stored_versions=(m=%s,p=%s,a=%s)", normalized_intent_key, True, record.demoted, record.versions_match(manifest_version=manifest_version, policy_version=policy_version, asset_versions=asset_versions), record.manifest_version, record.policy_version, record.asset_versions)
        else:
            logger.info("template_lookup intent=%s found=%s demoted=%s versions_ok=%s stored_versions=(m=%s,p=%s,a=%s)", normalized_intent_key, False, False, False, "", "", {})
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
        if status != "success":
            logger.warning("template_streak_broken intent=%s status=%s counts=(s=%s,d=%s,f=%s)", normalized_intent_key, status, record.success_count, record.degraded_count, record.failure_count)
        if record.demoted:
            logger.warning("template_demoted intent=%s status=%s counts=(s=%s,d=%s,f=%s)", normalized_intent_key, status, record.success_count, record.degraded_count, record.failure_count)
        key = _key(record.normalized_intent_key, record.role_scope)
        self._conn.execute(
            "UPDATE plan_templates SET record_json=? WHERE key=?", (record.model_dump_json(), key)
        )
        self._conn.commit()

    def _load_candidate(self, key: str) -> PlanTemplateRecord | None:
        cur = self._conn.execute("SELECT record_json FROM plan_template_candidates WHERE key=?", (key,))
        row = cur.fetchone()
        if row is None:
            return None
        return PlanTemplateRecord.model_validate_json(row[0])

    def consider_promotion(self, candidate: PlanTemplateRecord, *, promote_after: int) -> bool:
        if candidate.source != PLANNER_GENERATED:
            return False
        promote_after = max(1, int(promote_after))
        key = _key(normalize_intent_key(candidate.normalized_intent_key), candidate.role_scope)

        active = self._load(candidate.normalized_intent_key, candidate.role_scope)
        if active is not None and active.plan_graph_hash == candidate.plan_graph_hash and active.versions_match(
            manifest_version=candidate.manifest_version,
            policy_version=candidate.policy_version,
            asset_versions=candidate.asset_versions,
        ):
            self.record_outcome(candidate.normalized_intent_key, role_scope=candidate.role_scope, status="success")
            self._conn.execute("DELETE FROM plan_template_candidates WHERE key=?", (key,))
            self._conn.commit()
            return True

        cand = self._load_candidate(key)
        if cand is not None and cand.plan_graph_hash == candidate.plan_graph_hash and cand.versions_match(
            manifest_version=candidate.manifest_version,
            policy_version=candidate.policy_version,
            asset_versions=candidate.asset_versions,
        ):
            cand.success_count += 1
        else:
            cand = candidate.model_copy(update={"success_count": 1})

        if cand.success_count >= promote_after:
            self.promote(cand.model_copy())
            self._conn.execute("DELETE FROM plan_template_candidates WHERE key=?", (key,))
            self._conn.commit()
            return True

        accuracy = cand.success_count / promote_after
        logger.info("template_candidate_streak intent=%s plan_hash=%s success_count=%s/%s", candidate.normalized_intent_key, candidate.plan_graph_hash, cand.success_count, promote_after)
        logger.info("template_promotion_blocked accuracy=%.2f below_threshold=%.2f", accuracy, 1.0)
        self._conn.execute(
            "INSERT OR REPLACE INTO plan_template_candidates(key, record_json) VALUES (?,?)",
            (key, cand.model_dump_json()),
        )
        self._conn.commit()
        return False

    def note_non_success(self, normalized_intent_key: str, *, role_scope: str) -> None:
        key = _key(normalize_intent_key(normalized_intent_key), role_scope)
        self._conn.execute("DELETE FROM plan_template_candidates WHERE key=?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
