"""Tests for verify_sql_intent node — intent alignment detection."""

from __future__ import annotations

import pytest

from app.graph.verify_sql_intent import _detect_fact_table, _fallback_verify, _is_simple_sql


class TestDetectFactTable:
    def test_inventory_table(self):
        sql = "SELECT quantity FROM inventory WHERE product_id = 1"
        assert _detect_fact_table(sql) == "inventory"

    def test_with_join(self):
        sql = "SELECT p.name, i.quantity FROM inventory i JOIN products p ON i.product_id = p.id"
        assert _detect_fact_table(sql) == "inventory"

    def test_stockreceipts_table(self):
        sql = "SELECT * FROM stockreceipts WHERE status = 'Approved'"
        assert _detect_fact_table(sql) == "stockreceipts"

    def test_with_cte_ignores_cte_name(self):
        sql = "WITH months AS (...) SELECT * FROM financeledger"
        result = _detect_fact_table(sql)
        assert result is not None


class TestIsSimpleSql:
    def test_simple_select(self):
        assert _is_simple_sql("SELECT name FROM products WHERE status = 'Active' LIMIT 10") is True

    def test_simple_with_one_join(self):
        assert _is_simple_sql(
            "SELECT p.name, i.quantity FROM inventory i JOIN products p ON i.product_id = p.id"
        ) is True

    def test_cte_is_not_simple(self):
        assert _is_simple_sql("WITH months AS (...) SELECT ...") is False

    def test_multiple_joins_not_simple(self):
        assert _is_simple_sql(
            "SELECT * FROM a JOIN b ON a.id = b.id JOIN c ON b.id = c.id"
        ) is False


class TestFallbackVerify:
    def test_detects_wrong_fact_table(self):
        """inventory domain but SQL uses stockreceipts"""
        result = _fallback_verify("SELECT * FROM stockreceipts", "inventory")
        assert result["intent_match"] is False
        assert result["action"] == "regen"

    def test_correct_fact_table_inventory(self):
        result = _fallback_verify("SELECT quantity FROM inventory WHERE product_id = 1", "inventory")
        assert result["intent_match"] is True

    def test_correct_fact_table_ledger(self):
        result = _fallback_verify(
            "SELECT SUM(amount) FROM financeledger WHERE transaction_type = 'SalesRevenue'",
            "ledger",
        )
        assert result["intent_match"] is True

    def test_generic_domain_always_passes(self):
        result = _fallback_verify("SELECT name FROM products", "generic")
        assert result["intent_match"] is True

    def test_bypass_review_for_simple_sql(self):
        result = _fallback_verify("SELECT name FROM products WHERE status = 'Active'", "generic")
        assert result["action"] == "bypass_review"

    def test_proceed_for_join_sql(self):
        result = _fallback_verify(
            "SELECT p.name, i.quantity FROM inventory i JOIN products p ON i.product_id = p.id",
            "inventory",
        )
        assert result["action"] == "proceed"
