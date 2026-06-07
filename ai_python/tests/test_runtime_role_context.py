"""Placeholder tests for role/RBAC context — Slice A (deferred per project decision)."""

from __future__ import annotations

import pytest


# Slice A (Role/RBAC) is intentionally deferred — full implementation pending.
# These placeholders ensure the test file exists so QA matrix counts are consistent.


def test_slice_a_placeholder_role_context_skipped():
    """Slice A skipped until agentic loop is validated end-to-end."""
    pytest.skip("Slice A (Role/RBAC) deferred — not yet implemented")


def test_slice_a_placeholder_rbac_guard_skipped():
    pytest.skip("Slice A (Role/RBAC) deferred — not yet implemented")
