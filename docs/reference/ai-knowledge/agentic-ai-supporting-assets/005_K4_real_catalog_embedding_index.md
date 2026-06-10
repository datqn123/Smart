# K4 - Real Catalog Embedding Index

```yaml
asset_id: K4
version: "2026.06.07"
source_of_truth: generated
refresh_policy: incremental_on_change + full_rebuild_nightly
store: pgvector
consumers: [intent_entity_resolver, planner, hitl_suggestion_builder]
must_log_version_in_trace: true
```

## Purpose

Cung cấp semantic/fuzzy matching cho entity thực trong DB để intent subagent phân giải tên sản phẩm, danh mục, nhà cung cấp, khách hàng, vị trí kho từ input tiếng Việt của user — kể cả viết tắt, sai chính tả, tên không đầy đủ.

---

## Collections

### products
```yaml
collection: products
source_table: products
id_column: id
tenant_scoped: true
filter_active: "status = 'Active'"
text_fields:
  - name: product_name      weight: 1.0   label: "Tên sản phẩm"
  - name: sku_code          weight: 0.8   label: "Mã SKU"
  - name: barcode           weight: 0.6   label: "Mã vạch"
metadata_fields:
  - category_id
  - status
  - tenant_id
embedding_text_template: "{product_name} {sku_code}"
refresh_trigger: [INSERT, UPDATE ON products WHERE status='Active']
```

### categories
```yaml
collection: categories
source_table: categories
id_column: id
tenant_scoped: true
filter_active: "status = 'Active' AND deleted_at IS NULL"
text_fields:
  - name: name              weight: 1.0   label: "Tên danh mục"
  - name: description       weight: 0.4   label: "Mô tả"
metadata_fields:
  - parent_id
  - status
embedding_text_template: "{name}"
refresh_trigger: [INSERT, UPDATE ON categories]
```

### suppliers
```yaml
collection: suppliers
source_table: suppliers
id_column: id
tenant_scoped: true
filter_active: "status = 'Active'"
text_fields:
  - name: name              weight: 1.0   label: "Tên nhà cung cấp"
  - name: contact_person    weight: 0.5   label: "Người liên hệ"
  - name: supplier_code     weight: 0.7   label: "Mã NCC"
metadata_fields:
  - status
  - tax_code
embedding_text_template: "{name}"
pii_note: "phone và email KHÔNG được index vào vector — chỉ dùng cho lookup trực tiếp"
refresh_trigger: [INSERT, UPDATE ON suppliers]
```

### customers
```yaml
collection: customers
source_table: customers
id_column: id
tenant_scoped: true
filter_active: "status = 'Active' AND deleted_at IS NULL"
text_fields:
  - name: name              weight: 1.0   label: "Tên khách hàng"
  - name: customer_code     weight: 0.7   label: "Mã KH"
metadata_fields:
  - status
  - loyalty_points
embedding_text_template: "{name} {customer_code}"
pii_note: "phone và email KHÔNG được index — PII, chỉ lookup khi owner yêu cầu rõ ràng"
refresh_trigger: [INSERT, UPDATE ON customers]
```

### warehouse_locations
```yaml
collection: warehouse_locations
source_table: warehouselocations
id_column: id
tenant_scoped: false
filter_active: "status = 'Active'"
text_fields:
  - name: combined          weight: 1.0   label: "Kho-Kệ"    derived: "warehouse_code || '-' || shelf_code"
  - name: description       weight: 0.5   label: "Mô tả"
metadata_fields:
  - warehouse_code
  - shelf_code
  - status
embedding_text_template: "{warehouse_code}-{shelf_code} {description}"
refresh_trigger: [INSERT, UPDATE ON warehouselocations]
```

---

## Matching Output Contract

```json
{
  "raw": "coca cola",
  "entity_type": "product",
  "query_tenant_id": "t1",
  "matches": [
    {
      "id": "42",
      "display": "Coca-Cola lon 330ml",
      "score": 0.94,
      "match_kind": "embedding+fuzzy",
      "metadata": { "category_id": 2, "status": "Active", "tenant_id": "t1" }
    },
    {
      "id": "43",
      "display": "Coca-Cola chai 1.5L",
      "score": 0.87,
      "match_kind": "embedding",
      "metadata": { "category_id": 2, "status": "Active", "tenant_id": "t1" }
    }
  ]
}
```

---

## Scoring & Decision Logic

| Score range | Hành động của intent |
|---|---|
| ≥ 0.9 | Chọn top 1 tự động, không cần xác nhận |
| 0.75 – 0.9 | Chọn top 1, nêu giả định trong câu trả lời |
| 0.6 – 0.75 | HITL: hỏi user chọn trong top 3 candidates |
| < 0.6 | HITL bắt buộc: không tìm thấy, hỏi user cung cấp tên chính xác hơn |
| 0 matches | HITL: thực thể chưa có trong hệ thống, gợi ý tạo mới nếu phù hợp |

---

## Matching Method (hybrid)

```
1. Exact match normalized (lowercase, bỏ dấu tiếng Việt) → score = 1.0
2. Fuzzy string match (Levenshtein/n-gram) → score = 0.6-0.9
3. Embedding cosine similarity (pgvector) → score = 0.5-0.95
4. Final score = max(fuzzy_score, embedding_score) × weight
```

---

## Guardrails

- Mỗi query phải có `tenant_id` filter — không trả match của tenant khác.
- Không index raw PII (phone, email, password_hash).
- inactive/deleted records loại trừ khỏi index mặc định.
- Kết quả HITL hiển thị `display` (tên nghiệp vụ), không hiển thị internal `id`.
- Embedding model version được lưu kèm; thay đổi model → rebuild toàn bộ vectors.

---

## Refresh Policy

```yaml
incremental:
  trigger: DB change event (INSERT/UPDATE trên các source_table)
  lag_max: 60 seconds
full_rebuild:
  schedule: "daily 02:00 Asia/Ho_Chi_Minh"
  trigger_also: embedding_model_version_change
metadata_stored:
  - embedding_model_name
  - embedding_model_version
  - index_built_at
  - source_record_count
```

---

## Acceptance Checklist

- [ ] Resolve đúng tên sản phẩm viết tắt/sai chính tả (VD: "coke" → "Coca-Cola")
- [ ] Không bao giờ trả match của tenant khác
- [ ] Trả top 3 candidates cho HITL khi score thấp
- [ ] Version index được log vào trace
- [ ] Inactive/deleted records không xuất hiện trong kết quả mặc định
- [ ] phone/email không xuất hiện trong embedding text
