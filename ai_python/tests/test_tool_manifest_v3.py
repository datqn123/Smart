"""Slice A — rich v3 tool manifest + registry (SRS-006 FR-2, QA TC-A)."""

from __future__ import annotations

import pytest

from app.harness.tool_registry import (
    DecisionSchema,
    ToolManifest,
    ToolRegistry,
    can_silent_retry,
)

_SIDE_EFFECT_CLASSES = {"read_only", "idempotent_write", "non_idempotent_write"}


def _all_tool_manifests() -> dict[str, ToolManifest]:
    """Class-attribute manifests — accessible without constructing the tools."""
    from app.graph.tools.answer_composer import AnswerComposerTool
    from app.graph.tools.build_chart import BuildChartTool
    from app.graph.tools.catalog_draft import CatalogDraftTool
    from app.graph.tools.data_table_builder import DataTableBuilderTool
    from app.graph.tools.data_validator import DataValidatorTool
    from app.graph.tools.erp_guide import ErpGuideTool
    from app.graph.tools.inventory_draft import InventoryDraftTool
    from app.graph.tools.schema_explore import SchemaExploreTool
    from app.graph.tools.sql_query import SqlQueryTool

    classes = [
        SqlQueryTool,
        SchemaExploreTool,
        CatalogDraftTool,
        InventoryDraftTool,
        DataValidatorTool,
        DataTableBuilderTool,
        AnswerComposerTool,
        BuildChartTool,
        ErpGuideTool,
    ]
    return {cls.manifest.name: cls.manifest for cls in classes}


# --- TC-A-001 -------------------------------------------------------------

def test_every_v3_tool_declares_required_manifest_fields():
    manifests = _all_tool_manifests()
    assert manifests, "no tool manifests discovered"
    for name, m in manifests.items():
        assert m.capability, f"{name} missing capability"
        assert m.side_effect_class in _SIDE_EFFECT_CLASSES, f"{name} bad side_effect_class"
        assert m.observation_schema, f"{name} missing observation_schema"
        assert isinstance(m.produces, tuple), f"{name} produces must be a tuple"
        assert isinstance(m.consumes, tuple), f"{name} consumes must be a tuple"


# --- TC-A-002 -------------------------------------------------------------

def test_planner_prompt_excludes_governance_only_fields():
    registry = ToolRegistry()
    manifest = ToolManifest(
        name="sql_query",
        description="Read ERP data.",
        args_schema='{"query":"string"}',
        capability="data_read",
        when_to_use="WHENUSE_SENTINEL",
        when_not_to_use="WHENNOTUSE_SENTINEL",
        examples=("EXAMPLE_SENTINEL",),
        # governance-only — must NOT appear in planner prompt
        eval_cases=("EVALCASE_SENTINEL",),
        rbac_required=("RBAC_SENTINEL",),
        cache_policy="tenant_scoped",
        preconditions=("PRECOND_SENTINEL",),
        output_schema="OUTPUTSCHEMA_SENTINEL",
        side_effect_class="read_only",
    )
    registry.register(manifest, _NoopTool())
    text = registry.tools_manifest_text()

    # planner-visible
    assert "WHENUSE_SENTINEL" in text
    assert "WHENNOTUSE_SENTINEL" in text
    assert "EXAMPLE_SENTINEL" in text
    # governance-only must be absent
    assert "EVALCASE_SENTINEL" not in text
    assert "RBAC_SENTINEL" not in text
    assert "PRECOND_SENTINEL" not in text
    assert "OUTPUTSCHEMA_SENTINEL" not in text
    assert "tenant_scoped" not in text


# --- TC-A-003 -------------------------------------------------------------

def test_manifest_version_changes_on_contract_change():
    registry = ToolRegistry()
    registry.register(
        ToolManifest(name="t", description="d", args_schema='{"a":"string"}', capability="data_read"),
        _NoopTool(),
    )
    v1 = registry.manifest_version

    registry.register(
        ToolManifest(name="t", description="d", args_schema='{"a":"int"}', capability="data_read"),
        _NoopTool(),
    )
    v2 = registry.manifest_version

    assert v1 != v2


def test_manifest_version_stable_when_unchanged():
    def build() -> ToolRegistry:
        r = ToolRegistry()
        r.register(
            ToolManifest(name="t", description="d", args_schema="{}", capability="data_read"),
            _NoopTool(),
        )
        return r

    assert build().manifest_version == build().manifest_version


# --- TC-A-004 -------------------------------------------------------------

def test_similar_tools_have_distinct_boundaries():
    manifests = _all_tool_manifests()
    similar = [
        manifests["answer_composer"],
        manifests["build_chart"],
        manifests["data_table_builder"],
        manifests["catalog_draft"],
        manifests["inventory_draft"],
        manifests["data_validator"],
    ]
    for m in similar:
        assert m.when_to_use, f"{m.name} missing when_to_use"
        assert m.when_not_to_use, f"{m.name} missing when_not_to_use"
    # Boundary that drives planner routing is the produced artifact type, not the
    # coarse capability label (two draft tools legitimately share draft_create).
    produces = [m.produces for m in similar]
    assert len(set(produces)) == len(produces), "produced artifact types must be distinct"


# --- TC-A-005 -------------------------------------------------------------

def test_side_effect_class_drives_retry_safety():
    assert can_silent_retry("read_only") is True
    assert can_silent_retry("idempotent_write") is True
    assert can_silent_retry("non_idempotent_write") is False


def test_draft_tools_are_non_idempotent_writes():
    manifests = _all_tool_manifests()
    assert manifests["catalog_draft"].side_effect_class == "non_idempotent_write"
    assert manifests["inventory_draft"].side_effect_class == "non_idempotent_write"
    assert not can_silent_retry(manifests["inventory_draft"].side_effect_class)


def test_decision_schema_accepts_v3_planner_actions():
    from app.harness.plan_graph import PlanGraph, PlanNode

    plan = PlanGraph(
        nodes=[PlanNode(id="q1", tool="sql_query", input_spec={"query": "x"}, output_expect="rows")]
    )

    plan_decision = DecisionSchema(action="plan_graph", plan_graph=plan, trace_reasoning="trace only")
    degraded = DecisionSchema(
        action="degrade_final_answer",
        degraded_reason="max_replans",
        final_answer="Câu trả lời chưa đầy đủ.",
    )

    assert plan_decision.plan_graph is plan
    assert degraded.degraded_reason == "max_replans"


class _NoopTool:
    async def invoke(self, args, ctx):  # pragma: no cover - registry needs an impl
        raise NotImplementedError
