"""HIGH-1 fix: live JWT role/permissions are plumbed into the policy gate.

Before this fix, draft tools (rbac_required=("draft_create",)) were permanently
blocked under the harness loop because ChatMetadata never carried the JWT role/mp
claim, so live permissions were always empty and policy fail-closed for everyone.
"""

from __future__ import annotations

import pytest

from app.api.auth import derive_role_permissions
from app.api.routes import _enforce_identity_context
from app.api.schemas import ChatMetadata, ChatRequest


# --- derive_role_permissions ---------------------------------------------

def test_owner_role_implies_draft_create():
    role, perms = derive_role_permissions({"role": "owner", "user_id": "u1", "tenant_id": "t1"})
    assert role == "owner"
    assert "draft_create" in perms


def test_staff_with_explicit_mp_flag_dict():
    role, perms = derive_role_permissions(
        {"role": "staff", "mp": {"draft_create": True, "report_view": False}}
    )
    assert role == "staff"
    assert "draft_create" in perms
    assert "report_view" not in perms


def test_staff_with_mp_list():
    _, perms = derive_role_permissions({"role": "staff", "mp": ["draft_create", "data_read"]})
    assert "draft_create" in perms


def test_staff_without_permissions_gets_nothing():
    role, perms = derive_role_permissions({"role": "staff", "user_id": "u1", "tenant_id": "t1"})
    assert role == "staff"
    assert "draft_create" not in perms


def test_missing_claims_fail_closed():
    role, perms = derive_role_permissions({})
    assert role is None
    assert perms == ()


def test_derive_role_permissions_list_valued_role_claim() -> None:
    """JWT roles=['admin'] (list) must grant same implied caps as role='admin' (str)."""
    role, perms = derive_role_permissions({"roles": ["admin"]})
    assert role == "admin", f"Expected 'admin', got {role!r}"
    assert "draft_create" in perms
    assert "data_read" in perms


def test_derive_role_permissions_list_first_element_wins() -> None:
    """When roles is a multi-element list, the first element is used."""
    role, perms = derive_role_permissions({"roles": ["owner", "staff"]})
    assert role == "owner"
    assert "draft_create" in perms
    assert "data_read" in perms


def test_derive_role_permissions_string_role_still_works() -> None:
    """String role claim must continue to work unchanged after the list fix."""
    role, perms = derive_role_permissions({"role": "admin"})
    assert role == "admin"
    assert "draft_create" in perms


# --- _enforce_identity_context injects server-authoritative claims --------

def test_enforce_identity_overwrites_client_supplied_role_and_permissions():
    request = ChatRequest(
        message="tạo sản phẩm mới",
        metadata=ChatMetadata(
            user_id="u1", tenant_id="t1", role="owner", permissions=("draft_create",)
        ),
    )
    # Attacker-style claims: staff with no permissions must win over client metadata.
    claims = {"user_id": "u1", "tenant_id": "t1", "role": "staff", "mp": []}
    _enforce_identity_context(request, claims, correlation_id="cid")
    assert request.metadata.role == "staff"
    assert "draft_create" not in request.metadata.permissions


def test_enforce_identity_populates_owner_permissions():
    request = ChatRequest(
        message="tạo sản phẩm mới",
        metadata=ChatMetadata(user_id="u1", tenant_id="t1"),
    )
    claims = {"user_id": "u1", "tenant_id": "t1", "role": "owner", "mp": []}
    _enforce_identity_context(request, claims, correlation_id="cid")
    assert request.metadata.role == "owner"
    assert "draft_create" in request.metadata.permissions


# --- the gap the review flagged: draft through the orchestrator policy gate -

def _registry_with_draft():
    from app.harness.tool_registry import ToolManifest, ToolRegistry, ToolResult

    class DraftTool:
        async def invoke(self, args, ctx):  # noqa: ANN001
            return ToolResult(ok=True, output={"draft": {"id": 1}}, observation_text="draft created")

    registry = ToolRegistry()
    registry.register(
        ToolManifest(
            name="catalog_draft",
            description="draft",
            args_schema="{}",
            capability="draft_create",
            rbac_required=("draft_create",),
            side_effect_class="non_idempotent_write",
        ),
        DraftTool(),
    )
    return registry


def _ctx(permissions):
    from app.harness.tool_registry import TurnContext

    return TurnContext(
        tenant_id="t1",
        user_id="u1",
        thread_id="th1",
        correlation_id="cid",
        bearer_token=None,
        schema_version=None,
        role="owner",
        permissions=permissions,
    )


def _draft_plan():
    from app.harness.plan_graph import PlanGraph, PlanNode

    return PlanGraph(
        nodes=[PlanNode(id="d1", tool="catalog_draft", input_spec={"request": "x"}, output_expect="")]
    )


@pytest.mark.asyncio
async def test_draft_node_allowed_with_live_permission():
    from app.harness.plan_graph import PlanExecutor
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness

    executor = PlanExecutor(
        tool_registry=_registry_with_draft(), policy=HarnessPolicy(), harness=AgentHarness(enabled=False)
    )
    results = await executor.execute(_draft_plan(), _ctx(("draft_create",)))
    assert results[0].ok is True


@pytest.mark.asyncio
async def test_draft_node_blocked_without_live_permission():
    from app.harness.plan_graph import PlanExecutor
    from app.harness.policy import HarnessPolicy
    from app.harness.runtime import AgentHarness

    executor = PlanExecutor(
        tool_registry=_registry_with_draft(), policy=HarnessPolicy(), harness=AgentHarness(enabled=False)
    )
    results = await executor.execute(_draft_plan(), _ctx(()))
    assert results[0].ok is False
    assert "quyền" in results[0].error
