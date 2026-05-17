"""Column label Vietnamese mapping for query tables."""

from __future__ import annotations

from app.graph.column_labels_vi import column_label_vi, resolve_column_label


def test_products_columns() -> None:
    assert column_label_vi("sku_code") == "Mã SKU"
    assert column_label_vi("category_id") == "Mã danh mục"
    assert column_label_vi("created_at") == "Ngày tạo"
    assert column_label_vi("image_url") == "Ảnh (URL)"


def test_resolve_skips_raw_english_label() -> None:
    assert resolve_column_label("SKU_CODE", "SKU_CODE") == "Mã SKU"
    assert resolve_column_label("name", "Tên hiển thị") == "Tên hiển thị"
