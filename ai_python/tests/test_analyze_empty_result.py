"""Tests for analyze_empty_result module — heuristics and node factory."""

from __future__ import annotations

import pytest

from app.graph.analyze_empty_result import (
    _detect_year_mismatch,
    _detect_exact_name_match,
    _detect_future_dates,
    _analyze_empty_heuristic,
)


class TestYearMismatch:
    def test_detects_year_mismatch(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"
        user_q = "doanh thu năm 2025"
        result = _detect_year_mismatch(sql, user_q)
        assert result is not None
        assert "2024" in result or "2025" in result

    def test_no_mismatch_when_years_align(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2025-01-01' AND '2025-03-31'"
        user_q = "doanh thu quý 1 năm 2025"
        result = _detect_year_mismatch(sql, user_q)
        assert result is None

    def test_no_user_question_years_returns_none(self):
        sql = "SELECT * FROM products WHERE name ILIKE '%iphone%'"
        user_q = "liệt kê sản phẩm"
        result = _detect_year_mismatch(sql, user_q)
        assert result is None

    def test_mismatch_from_non_overlap_years(self):
        sql = "SELECT * FROM inventory WHERE expiry_date < '2025-06-01'"
        user_q = "hàng hết hạn trong năm 2026"
        result = _detect_year_mismatch(sql, user_q)
        assert result is not None

    def test_no_sql_dates_returns_none(self):
        sql = "SELECT name FROM products WHERE status = 'Active'"
        user_q = "danh sách sản phẩm năm 2025"
        result = _detect_year_mismatch(sql, user_q)
        assert result is None


class TestExactNameMatch:
    def test_detects_exact_name_match(self):
        sql = "SELECT * FROM products WHERE name = 'Điện thoại'"
        result = _detect_exact_name_match(sql)
        assert result is not None

    def test_detects_exact_category_name(self):
        sql = "SELECT * FROM categories WHERE category_name = 'Điện tử'"
        result = _detect_exact_name_match(sql)
        assert result is not None

    def test_skips_iliike(self):
        sql = "SELECT * FROM products WHERE name ILIKE '%Điện thoại%'"
        result = _detect_exact_name_match(sql)
        assert result is None

    def test_skips_code_columns(self):
        sql = "SELECT * FROM products WHERE sku_code = 'ABC123'"
        result = _detect_exact_name_match(sql)
        assert result is None

    def test_no_name_filter_returns_none(self):
        sql = "SELECT quantity FROM inventory WHERE product_id = 1"
        result = _detect_exact_name_match(sql)
        assert result is None


class TestDetectFutureDates:
    def test_detects_future_date(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date >= '2099-01-01'"
        result = _detect_future_dates(sql)
        assert result is not None

    def test_past_dates_return_none(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"
        result = _detect_future_dates(sql)
        assert result is None

    def test_no_dates_returns_none(self):
        sql = "SELECT name FROM products"
        result = _detect_future_dates(sql)
        assert result is None


class TestAnalyzeEmptyHeuristic:
    def test_legitimate_no_data(self):
        sql = "SELECT * FROM inventory WHERE product_id = 99999"
        user_q = "kiểm tra sản phẩm 99999"
        result = _analyze_empty_heuristic(sql, user_q, "inventory")
        assert result["verdict"] == "legitimate"

    def test_suspicious_year_mismatch(self):
        sql = "SELECT * FROM financeledger WHERE transaction_date BETWEEN '2024-01-01' AND '2024-12-31'"
        user_q = "doanh thu năm 2025"
        result = _analyze_empty_heuristic(sql, user_q, "ledger")
        assert result["verdict"] == "suspicious"

    def test_suspicious_exact_name_match(self):
        sql = "SELECT * FROM products WHERE name = 'Điện thoại'"
        user_q = "sản phẩm tên Điện thoại"
        result = _analyze_empty_heuristic(sql, user_q, "catalog_price")
        assert result["verdict"] == "suspicious"

    def test_legitimate_future_date_empty(self):
        sql = "SELECT * FROM stockreceipts WHERE created_at >= '2099-01-01'"
        user_q = "phiếu nhập tương lai"
        result = _analyze_empty_heuristic(sql, user_q, "receipt")
        assert result["verdict"] == "legitimate"

    def test_generic_domain_no_patterns_returns_legitimate(self):
        sql = "SELECT name FROM products WHERE status = 'Active'"
        user_q = "danh sách sản phẩm"
        result = _analyze_empty_heuristic(sql, user_q, "generic")
        assert result["verdict"] == "legitimate"
