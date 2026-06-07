# Agentic AI Supporting Knowledge Assets — Index

```yaml
index_version: "2026.06.07"
owner: ai_python
design_source: docs/dev/requires/Design Agentic AI.md — mục 16
total_assets: 15
p0_assets: 6
p1_assets: 6
p2_assets: 3
```

## Mục đích

Bộ 15 tài liệu tri thức (K1–K15) này là **điều kiện tiên quyết** để Harness, tool và subagent của Smart ERP Assistant hoạt động đúng. Không có bộ này, intent subagent sẽ đoán schema, sql_subagent sẽ sinh SQL sai bảng, và answer_composer sẽ trả lời thiếu ngữ cảnh.

---

## Kiến trúc phụ thuộc

```
User → Harness
          │
          ├── Intent subagent     đọc: K1, K2, K3, K4, K13
          ├── Planner             đọc: K1, K8, K13, K15
          ├── SQL subagent        đọc: K1, K2, K3, K5, K7, K8
          ├── Data Validator      đọc: K3, K8
          ├── Chart tool          đọc: K9, K14
          ├── Catalog Draft       đọc: K6, K11
          ├── Inventory Draft     đọc: K6, K11
          ├── Answer Composer     đọc: K8, K10, K13, K14
          ├── Guardrail/Policy    đọc: K5, K6
          └── Eval Harness        đọc: K12, K15
```

---

## Asset List

| ID | File | Priority | Consumer chính | Trạng thái nội dung | Refresh policy |
|---|---|---|---|---|---|
| K1 | `002_K1_system_data_dictionary.md` | 🔴 P0 | intent, planner, sql_subagent | ✅ 18 bảng thực từ schema | on_schema_change |
| K2 | `003_K2_vi_synonym_to_column_dictionary.md` | 🔴 P0 | intent, sql_subagent | ✅ 30+ term tiếng Việt | monthly_review |
| K3 | `004_K3_enum_status_dictionary.md` | 🔴 P0 | sql_subagent, data_validator | ✅ 20 enum đầy đủ | on_schema_change |
| K4 | `005_K4_real_catalog_embedding_index.md` | 🔴 P0 | intent entity resolver | ✅ 5 collections + scoring | incremental + nightly |
| K5 | `006_K5_sql_allowlist_safety_policy.md` | 🔴 P0 | guardrail, sql_subagent | ✅ owner/staff table matrix | on_rbac_change |
| K6 | `007_K6_capability_rbac_matrix.md` | 🔴 P0 | guardrail, harness | ✅ 9 capabilities × 4 roles | on_rbac_change |
| K7 | `008_K7_sql_few_shot_examples.md` | 🟡 P1 | sql_subagent | ✅ 22 ví dụ thực | manual_review |
| K8 | `009_K8_business_rules_formulas.md` | 🟡 P1 | data_validator, sql_subagent | ✅ 10 metric + intent keys | manual_review |
| K9 | `010_K9_chart_spec_catalog.md` | 🟡 P1 | chart tool | ✅ 5 chart types + selection rules | manual_review |
| K10 | `011_K10_answer_templates.md` | 🟡 P1 | answer_composer | ✅ 10 templates (T1–T10) | manual_review |
| K11 | `012_K11_draft_slot_schema.md` | 🟡 P1 | catalog_draft, inventory_draft | ✅ 5 draft types + HITL flow | on_schema_change |
| K12 | `013_K12_golden_eval_set.md` | 🟡 P1 | eval harness | ✅ 15 cases + 3 fixtures | append_on_failure |
| K13 | `014_K13_erp_domain_guide.md` | 🟢 P2 | intent, answer_composer | ✅ 8 domain + cross-relation | manual_review |
| K14 | `015_K14_vi_units_formatting.md` | 🟢 P2 | answer_composer, chart | ✅ VND, ngày, số, đơn vị | manual_review |
| K15 | `016_K15_intent_tool_success_history.md` | 🟢 P2 | planner, observability | ✅ event schema + query interface | append_every_turn |

---

## Shared Metadata Contract

Mọi asset phải có header YAML với các field sau:

```yaml
asset_id: K1                          # ID duy nhất
version: "2026.06.07"                 # YYYY.MM.DD của lần cập nhật gần nhất
source_of_truth: hybrid               # generated | manual | hybrid | generated_append_only
refresh_policy: on_schema_change      # xem bảng trên
consumers: [intent, planner, ...]     # danh sách subagent/tool đọc asset này
must_log_version_in_trace: true       # nếu true, harness phải log version vào trace mỗi turn
```

**Bất biến quan trọng:** Harness phải log `asset_id + version` của mọi asset `must_log_version_in_trace: true` vào trace turn, để khi câu trả lời sai có thể truy vết về đúng phiên bản tài liệu đã dùng.

---

## P0 Gate — Bắt buộc trước khi bật harness_loop production

Tất cả 6 asset P0 phải đạt trước khi `harness_loop_enabled=True` với bất kỳ intent nào:

| # | Asset | Điều kiện pass |
|---|---|---|
| K1 | System Data Dictionary | Phủ đủ 18 bảng, mỗi bảng có label_vi + read_roles + tất cả cột nhạy cảm đã mark |
| K2 | VI Synonym Dictionary | Có ≥ 20 term thực dùng, mọi term resolve về K1 table/column hoặc K8 metric |
| K3 | Enum Dictionary | Mọi enum column trong K1 có entry đầy đủ, không còn `values: {}` rỗng |
| K4 | Catalog Embedding Index | Index đã build với dữ liệu thực; refresh nightly đang chạy; score threshold test pass |
| K5 | SQL Allowlist | staff denied financeledger/partnerdebts đã verify; SQL examples K7 pass policy |
| K6 | RBAC Matrix | Đồng bộ với Backend permission source; mọi tool có RBAC entry |

---

## P1 Gate — Bắt buộc trước khi chạy beta

| # | Asset | Mức tối thiểu |
|---|---|---|
| K7 | SQL Few-Shot | ≥ 22 ví dụ (đã đạt); review tay trước khi dùng prompt |
| K8 | Business Rules | ≥ 10 metric; normalized_intent_keys đầy đủ |
| K9 | Chart Spec | 5 chart types đã verify với frontend renderer |
| K10 | Answer Templates | 10 templates (T1–T10) đầy đủ |
| K11 | Draft Slot Schema | required_slots và HITL flow đã test end-to-end |
| K12 | Golden Eval Set | ≥ 15 test cases; fixtures có seed data thực; regression chạy được |

---

## P2 Gate — Chạy trước production rollout đầy đủ

| # | Asset | Mục tiêu |
|---|---|---|
| K13 | ERP Domain Guide | 8 domain đầy đủ; linked về K1/K8 |
| K14 | VI Units Formatting | Verify với answer_composer và chart payload thực |
| K15 | Success History | Event append đang chạy; planner query interface hoạt động |

---

## Update Rules

### Generated assets (K1, K3, K4, K15)
- Phải có `schema_fingerprint` hoặc `source_record_count` để phát hiện drift.
- Khi schema DB thay đổi (Flyway migration mới): rebuild K1 và K3 trước khi deploy.
- K4: nếu embedding model version thay đổi → rebuild toàn bộ vectors trước khi dùng.
- K15: append-only, không sửa record cũ.

### Manual assets (K2, K7, K8, K10, K13)
- Review ít nhất mỗi tháng; thêm term/ví dụ từ failed intent log.
- Mọi thay đổi phải có reviewer và review_date trong header.
- Không được có mapping trỏ về bảng/cột không tồn tại trong K1.

### Hybrid assets (K5, K6)
- **Nguồn sự thật: Backend Spring** cho RBAC/permissions.
- Khi Backend thay đổi quyền → cập nhật K5 + K6 trong cùng PR.
- Sau khi update: chạy eval_002 (staff permission denied) và eval_009 trước khi deploy.

### Security rules (mọi asset)
- Không chứa bearer token, mật khẩu, raw PII thực của production.
- Không chứa ví dụ SQL nguy hiểm (INSERT/UPDATE/DELETE).
- K4: phone/email không được index vào vector store.
- K15: tenant_id phải được hash; không lưu raw question.

---

## Cross-Asset Integrity Rules

Các ràng buộc phải kiểm tra khi cập nhật:

| Rule | Kiểm tra |
|---|---|
| K2 → K1 | Mọi `maps_to.table/column` trong K2 phải tồn tại trong K1 |
| K2 → K8 | Mọi `maps_to.metric_id` trong K2 phải có entry trong K8 |
| K3 → K1 | Mọi `table + column` trong K3 phải khớp K1 |
| K5 → K1 | Mọi tên cột trong `denied_columns` phải là cột thực trong K1 |
| K5 → K6 | `allowed_tables` trong K5 phải đồng nhất với `capabilities` trong K6 |
| K7 → K1 | Tên bảng/cột trong SQL examples phải khớp K1 (lowercase PostgreSQL) |
| K7 → K3 | Giá trị enum trong WHERE clause phải khớp K3 raw code |
| K7 → K5 | SQL examples phải pass K5 policy |
| K8 → K1 | `source_tables` trong K8 phải tồn tại trong K1 |
| K10 → K14 | Templates phải dùng format tiền/ngày theo K14 |
| K11 → K1 | Slot FK references (category_id, supplier_id...) phải khớp K1 |
| K12 → K8 | `normalized_intent_key` trong K12 phải có trong K8 intent key catalog |
| K15 → K8 | `normalized_intent_key` trong K15 phải là key hợp lệ trong K8 |

---

## Quick Reference — Consumer Map

| Tôi đang làm gì? | Đọc asset nào? |
|---|---|
| Phân tích intent user | K1, K2, K3, K4, K13 |
| Lập plan DAG | K1, K8, K13, K15 |
| Sinh SQL | K1, K2, K3, K5, K7, K8 |
| Review SQL an toàn | K5 |
| Validate dữ liệu trả về | K3, K8 |
| Vẽ biểu đồ | K9, K14 |
| Soạn câu trả lời | K8, K10, K13, K14 |
| Tạo nháp catalog/inventory | K6, K11 |
| Kiểm tra quyền truy cập | K5, K6 |
| Chọn câu hỏi gợi ý tiếp | K10 (next_question_suggestions) |
| Chạy regression test | K12 |
| Planner học từ lịch sử | K15 |
