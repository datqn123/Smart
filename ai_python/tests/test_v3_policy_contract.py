"""SRS-006 policy contract: live permissions are the source of truth."""

from __future__ import annotations

import pytest

from app.harness.policy import HarnessPolicy, HarnessPolicyError


def test_protected_draft_tool_fails_closed_without_live_permission() -> None:
    with pytest.raises(HarnessPolicyError):
        HarnessPolicy().check(
            "catalog_draft",
            {"request": "tạo sản phẩm mới"},
            role="owner",
            permissions=(),
            rbac_required=("draft_create",),
            side_effect_class="non_idempotent_write",
        )


def test_protected_draft_tool_allows_explicit_live_permission() -> None:
    HarnessPolicy().check(
        "catalog_draft",
        {"request": "tạo sản phẩm mới"},
        role="staff",
        permissions=("draft_create",),
        rbac_required=("draft_create",),
        side_effect_class="non_idempotent_write",
    )


def test_artifact_builder_tools_are_read_only_policy_scopes() -> None:
    policy = HarnessPolicy()

    policy.check("answer_composer", {}, permissions=())
    policy.check("build_chart", {}, permissions=())
    policy.check("data_table_builder", {}, permissions=())
