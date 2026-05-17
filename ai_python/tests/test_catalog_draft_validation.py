from __future__ import annotations

from app.graph.catalog_draft_schema import validate_draft_rows


def test_validate_product_requires_category() -> None:
    rows = [
        {
            "rowId": "r1",
            "values": {
                "skuCode": "NEW-1",
                "name": "SP",
                "baseUnitName": "Cái",
                "costPrice": 1,
                "salePrice": 2,
            },
        }
    ]
    issues = validate_draft_rows("product", rows)
    assert any("danh mục" in i.lower() for i in issues)


def test_validate_category_duplicate_in_batch() -> None:
    rows = [
        {"rowId": "r1", "values": {"categoryCode": "CAT-A", "name": "A"}},
        {"rowId": "r2", "values": {"categoryCode": "CAT-A", "name": "B"}},
    ]
    issues = validate_draft_rows("category", rows)
    assert any("trùng" in i for i in issues)
