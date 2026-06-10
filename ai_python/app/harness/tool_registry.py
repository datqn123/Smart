"""Tool manifest, result, and decision contracts for the harness loop."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from collections.abc import Sequence
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TurnContext:
    tenant_id: str | None
    user_id: str | None
    thread_id: str | None
    correlation_id: str
    bearer_token: str | None
    schema_version: str | None
    clarification_response: dict[str, Any] | None = None
    pending_hitl_tool: str | None = None
    pending_hitl_payload: dict[str, Any] | None = None
    intent_object: dict[str, Any] | None = None
    assumptions: list[str] = field(default_factory=list)
    role: str | None = None
    permissions: Sequence[str] = ()
    result_store: Any | None = None


@dataclass(frozen=True)
class ToolInput:
    tool_name: str
    args: dict[str, Any]
    context: TurnContext


@dataclass
class HitlSpec:
    event_name: str
    payload: dict[str, Any]
    resume_token: str


@dataclass
class ToolResult:
    ok: bool
    output: dict[str, Any]
    observation_text: str
    sse_payload: dict[str, Any] | None = None
    pending_hitl: HitlSpec | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ToolManifest:
    """Tool contract surface for the v3 planner-brain (SRS-006 FR-2).

    The first four fields preserve the v1/v2 construction shape; every v3 field
    has a default so existing ``ToolManifest(name=, description=, args_schema=)``
    call sites keep working. Tuples (not lists) keep the dataclass frozen/hashable.
    """

    name: str
    description: str
    args_schema: str
    has_hitl: bool = False
    # --- v3 planner-brain manifest fields ---
    capability: str = ""
    output_schema: str = ""
    output_artifact_types: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    when_to_use: str = ""
    when_not_to_use: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"
    rbac_required: tuple[str, ...] = ()
    budget_class: Literal["cheap", "standard", "expensive"] = "standard"
    cache_policy: Literal["none", "tenant_scoped", "global_static"] = "none"
    eval_cases: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    side_effect_class: Literal["read_only", "idempotent_write", "non_idempotent_write"] = "read_only"
    produces: tuple[str, ...] = ()
    consumes: tuple[str, ...] = ()
    result_ref_policy: Literal["inline", "result_ref"] = "inline"
    observation_schema: str = "ObservationEnvelope"


def can_silent_retry(side_effect_class: str) -> bool:
    """FR-6.6: only read-only / idempotent tools may be auto-retried silently.

    A ``non_idempotent_write`` tool must surface its failure to the Planner for an
    explicit new decision instead of being re-run.
    """
    return side_effect_class in ("read_only", "idempotent_write")


# Fields injected into the planner prompt (FR-2.1). Everything not listed here is
# governance-only (eval_cases, full output_schema, cache_policy, preconditions,
# rbac_required, side_effect_class, version fields) and must NOT reach the prompt.
_PLANNER_VISIBLE_FIELDS = (
    "name",
    "description",
    "capability",
    "args_schema",
    "output_artifact_types",
    "when_to_use",
    "when_not_to_use",
    "examples",
    "produces",
    "consumes",
)


class AsyncTool(Protocol):
    async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, ToolManifest] = {}
        self._impls: dict[str, AsyncTool] = {}
        self._cached_version: str | None = None

    def register(self, manifest: ToolManifest, impl: AsyncTool) -> None:
        self._manifests[manifest.name] = manifest
        self._impls[manifest.name] = impl
        self._cached_version = None
        logger.info("tool_registered name=%s hitl=%s capability=%s side_effect=%s", manifest.name, manifest.has_hitl, manifest.capability, manifest.side_effect_class)

    def get_impl(self, name: str) -> AsyncTool:
        try:
            return self._impls[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

    def get_manifest(self, name: str) -> ToolManifest | None:
        return self._manifests.get(name)

    def manifests(self) -> dict[str, ToolManifest]:
        return dict(self._manifests)

    @property
    def manifest_version(self) -> str:
        """Stable short hash over contract-shaping fields (FR-11.8).

        Changing a tool's ``args_schema``, ``capability``, ``side_effect_class``,
        data-flow types, or HITL flag produces a new version so a pinned plan
        template can be invalidated.
        """
        if self._cached_version is not None:
            return self._cached_version
        payload = [
            {
                "name": m.name,
                "args_schema": m.args_schema,
                "capability": m.capability,
                "side_effect_class": m.side_effect_class,
                "produces": list(m.produces),
                "consumes": list(m.consumes),
                "output_schema": m.output_schema,
                "result_ref_policy": m.result_ref_policy,
                "has_hitl": m.has_hitl,
                "rbac_required": list(m.rbac_required),
            }
            for name in sorted(self._manifests)
            for m in (self._manifests[name],)
        ]
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        self._cached_version = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        logger.info("tool_manifest_version hash=%s tool_count=%s", self._cached_version, len(self._manifests))
        return self._cached_version

    def tools_manifest_text(self) -> str:
        """Planner-visible tool surface (FR-2.1) — governance fields excluded."""
        lines: list[str] = []
        for manifest in self._manifests.values():
            hitl = " HITL" if manifest.has_hitl else ""
            parts = [f"- {manifest.name}{hitl}: {manifest.description}"]
            if manifest.capability:
                parts.append(f"capability={manifest.capability}")
            parts.append(f"Args: {manifest.args_schema}")
            if manifest.output_artifact_types:
                parts.append(f"artifacts={','.join(manifest.output_artifact_types)}")
            if manifest.produces:
                parts.append(f"produces={','.join(manifest.produces)}")
            if manifest.consumes:
                parts.append(f"consumes={','.join(manifest.consumes)}")
            if manifest.when_to_use:
                parts.append(f"when_to_use: {manifest.when_to_use}")
            if manifest.when_not_to_use:
                parts.append(f"when_not_to_use: {manifest.when_not_to_use}")
            if manifest.examples:
                parts.append(f"examples: {' | '.join(manifest.examples[:2])}")
            lines.append(" ".join(parts))
        return "\n".join(lines)


class ToolCall(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""


class ClarifyRequest(BaseModel):
    """Ask the user a clarifying question (rendered as a UI bubble, not plain text)."""

    questions: list[str] = Field(default_factory=list)
    suggested_rewrite: str = ""


class DecisionSchema(BaseModel):
    action: Literal["call_tool", "plan_graph", "clarify", "final_answer", "degrade_final_answer"]
    tool_call: ToolCall | None = None
    plan_graph: Any | None = None
    final_answer: str | None = None
    clarify: ClarifyRequest | None = None
    degraded_reason: str | None = None
    trace_reasoning: str = ""
