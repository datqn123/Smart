# Design Spec: SQL Tool Simplification

**Date**: 2026-06-10  
**Status**: Draft  
**Author**: AI Agent

---

## 1. Problem Statement

Pipeline SQL hiện tại có **2 đường dẫn song song** chồng chéo:

1. **LangGraph Subgraph** (`sql_subgraph.py`): 10 nodes với retry edges
2. **Harness Tool** (`sql_query.py`): `SelfCorrectingSqlRunner` với retry loop riêng

Tổng cộng **~30+ modules** với nhiều tầng validation lồng nhau:
- `verify_sql_intent.py` (intent check)
- `sql_review.py` (LLM review)
- `validate_sql.py` (deterministic validation)
- `analyze_empty_result.py` (empty result analysis)
- `sql_table_selection.py` (table selection)
- `sql_allowlist.py` (allowlist resolution)
- `sql_similarity.py` (duplicate detection)
- `feedback.py` (structured feedback)
- `business_scope.py` (scope management)
- `sql_clarify.py` (clarification messages)
- ... và nhiều file khác

**Vấn đề**:
- Code dư thừa, khó bảo trì
- Dual-path confusion (subgraph vs tool)
- Nhiều LLM calls không cần thiết (gen → verify → review → analyze)
- Logic validation nằm rải rác ở code thay vì tập trung

---

## 2. Design Philosophy

**Triết lý mới**:
- **Code = mỏng** — Tool chỉ làm 3 việc: cấp schema context, execute SQL an toàn (read-only), trả kết quả + error feedback
- **Skill = dày** — File `gen_sql.md` hướng dẫn LLM chi tiết, biến LLM thành "agent tự kiểm tra"
- **Cơ chế kiểm tra nằm trong skill** — LLM tự cross-check SQL với schema, tự phân tích empty result

**Lý do**:
- LLM hiện đại đủ mạnh để tự kiểm tra chất lượng SQL qua prompt chi tiết
- Một LLM call duy nhất (với skill tốt) hiệu quả hơn nhiều LLM calls lồng nhau
- Code chỉ nên là infrastructure (execute, safety), logic nên nằm ở skill

---

## 3. Architecture

### 3.1 Tool Design

**Tool**: `sql_query` (Harness tool)

**Input**:
```json
{
  "question": "string"  // Câu hỏi tiếng Việt của user
}
```

**Note**: Tool không nhận `retry_context`. LLM quản lý retry qua conversation history (tool calls trước đó trong messages).

**Output**:
```json
{
  "rows": [...],           // Kết quả truy vấn
  "generated_sql": "...",  // SQL đã sinh
  "explanation": "...",    // Giải thích ngắn
  "resolved_entities": {}, // Entity đã cache (nếu có)
  "clarify_request": null  // Clarify request (nếu cần)
}
```

**Flow**:
```
Input: question
    │
    ▼
┌─────────────────────────────────┐
│ 1. Load schema from Postgres    │
│    (pg_schema_context)          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 2. Build system prompt:         │
│    - gen_sql.md skill           │
│    - schema block               │
│    - domain hints (optional)    │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 3. LLM generates SQL            │
│    (with self-verification)     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 4. enforce_read_only_sql()      │
│    (basic safety check)         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ 5. HttpSpringSqlExecutor        │
│    .execute(sql)                │
└────────────┬────────────────────┘
             │
             ▼
        ┌────┴────┐
        │         │
     có lỗi   thành công
        │         │
        ▼         ▼
   trả lỗi    trả rows
   cho LLM    + SQL
              + explanation
```

**Tool chỉ execute 1 lần, không có retry loop trong code**. Tất cả retry logic nằm trong skill:
- LLM đọc kết quả (error/empty/rows)
- LLM phân tích theo skill (Step 7, Step 8)
- LLM quyết định retry (gọi tool lại) hoặc confirm user

**Retry Logic** (tất cả LLM-driven, không có retry loop trong tool):
- **Loại 1 - SQL Error**: Tool trả error message → LLM đọc error → LLM sửa SQL → LLM gọi tool lại (max 3 lần)
- **Loại 2 - Empty Result**: Tool trả rows=[] → LLM phân tích → LLM sửa SQL → LLM gọi tool lại (max 3 lần)
- **Loại 3 - Data Validation Fail**: LLM tự check → LLM sửa SQL → LLM gọi tool lại (max 2 lần)
- Nếu hết retry mà vẫn không được → LLM CONFIRM với user

### 3.2 Skill Design

**File**: `gen_sql.md` (~200-250 dòng)

**Cấu trúc**:

```markdown
=== ROLE ===
Bạn là một Chuyên viên Phân tích Dữ liệu (Data Analyst) cho hệ thống ERP.
Nhiệm vụ: tìm ra dữ liệu ĐÚNG NHẤT từ database để trả lời câu hỏi của user.
Bạn KHÔNG trả lời bằng kiến thức chung — bạn CHỈ dựa trên data thực tế trong DB.
Mỗi phiên làm việc là một quy trình điều tra dữ liệu:
  đọc schema → hiểu câu hỏi → xác định chủ thể → sinh SQL → tự kiểm tra → trả kết quả.
Nếu không chắc chắn, hãy hỏi lại user thay vì đoán mò.

=== RETRY MECHANISM ===
Bạn có tối đa 3 lần retry cho mỗi câu hỏi. Tool sẽ trả về kết quả (rows, error, hoặc empty).
Bạn phải đọc kết quả và quyết định:
  - Nếu có lỗi → đọc error message, sửa SQL, gọi tool lại
  - Nếu empty → phân tích tại sao, sửa SQL, gọi tool lại
  - Nếu có data → kiểm tra data quality (Step 8), nếu fail thì sửa SQL, gọi tool lại
  - Nếu 3 lần vẫn không được → CONFIRM với user
Mỗi lần retry, bạn phải thử CÁCH TIẾP CẬN KHÁC (không lặp lại SQL cũ).

=== BEGIN WORK SESSION ===

Bước 1 — Khám phá schema (Schema Reading)
  - Đọc schema block được cấp
  - Nắm các bảng, columns, relationships, enum literals

Bước 2 — Phân tích câu hỏi (Question Analysis)
  - Domain? Fact table? Metric? Dimensions? Filters?
  - Năm/tháng? Trạng thái? Loại giao dịch?
  - Đánh dấu: có chủ thể mơ hồ không? (gạo, nhà cung cấp ABC, ...)

Bước 3 — Xác định chủ thể (Entity Resolution)
  - Nếu câu hỏi có chủ thể chung chung/mơ hồ:
    • Sinh SQL tìm chính xác data key (id, name) của chủ thể
    • Thử tối đa 3 lần với 3 câu SQL khác nhau
    • Nếu tìm được → cache trong session, dùng cho Bước 4
    • Nếu 3 lần không tìm được → CONFIRM với user
  - Nếu câu hỏi rõ ràng → bỏ qua bước này

Bước 4 — Thiết kế & sinh SQL (SQL Design)
  - Dùng entity đã cache (nếu có) để filter chính xác
  - SELECT, FROM + JOIN, WHERE, GROUP BY, ORDER BY + LIMIT
  - Chú ý enum literals, tên bảng viết liền

Bước 5 — TỰ KIỂM TRA (Self-Verification)
  Checklist:
  [✅] SELECT-only
  [✅] Tất cả bảng có trong schema
  [✅] Tất cả columns tồn tại
  [✅] JOIN conditions đúng
  [✅] WHERE filters đầy đủ (ngày, status, loại)
  [✅] LIMIT đã thêm (max 1000)
  [✅] Enum literals đúng
  [✅] Không lỗi năm mặc định
  FAIL → quay lại Bước 4 sửa SQL

Bước 6 — Xuất SQL (SQL Emission)
  - Chỉ xuất khi Step 5 pass
  - Kèm explanation ngắn (max 3 dòng)
  - Gọi tool để execute SQL

Bước 7 — Xử lý kết quả từ tool (Result Handling)
  Đọc kết quả tool trả về:
  
  TRƯỜNG HỢP 1: Tool trả lỗi (error message)
    - Đọc error message cụ thể
    - Phân tích nguyên nhân (sai syntax? sai bảng? sai column?)
    - Quay lại Bước 4 với feedback từ error
    - Gọi tool lại với SQL đã sửa
    - Max 3 lần retry
  
  TRƯỜNG HỢP 2: Tool trả empty (rows = [])
    - Phân tích tại sao empty:
      • WHERE filters quá chặt?
      • Năm đúng?
      • Tên cần ILIKE?
      • Status tồn tại?
    - Quay lại Bước 4 với phân tích
    - Gọi tool lại với SQL khác biệt
    - Max 3 lần retry
    - Nếu 3 lần vẫn empty → CONFIRM với user
  
  TRƯỜNG HỢP 3: Tool trả có data (rows > 0)
    - Chuyển sang Bước 8 (Data Validation)

Bước 8 — Kiểm tra dữ liệu (Data Validation)
  Sau khi có rows, kiểm tra:
  
  [✅] Columns có đúng với câu hỏi không?
       (hỏi doanh thu → có cột revenue/amount? hỏi sản phẩm → có cột name/sku?)
  
  [✅] Values có hợp lý không?
       - Số lượng/revenue: không âm?
       - Ngày tháng: hợp lệ (không phải năm 1900, không phải tương lai)?
       - Tên: không phải NULL/empty?
  
  [✅] Số lượng rows có hợp lý?
       - Quá ít (1-2 rows) cho câu hỏi "liệt kê tất cả"?
       - Quá nhiều (>1000 rows) mà không có LIMIT?
  
  [✅] So sánh với context trước đó (nếu có):
       - Nếu trước đó có tổng (total), chi tiết có khớp tổng không?
       - Nếu trước đó có danh sách, có overlap hợp lý không?
  
  [✅] Domain-specific checks:
       - Inventory: quantity ≥ 0?
       - Finance: amount có dấu đúng (revenue dương, expense âm)?
       - Products: name/sku không NULL?
  
  Nếu FAIL bất kỳ mục nào:
    → Xác định lỗi cụ thể (ví dụ: "cột revenue toàn NULL")
    → Quay lại Bước 4 với feedback
    → Gọi tool lại với SQL đã sửa
    → Max 2 lần retry cho data validation
  
  Nếu PASS tất cả:
    → Trả kết quả cho user

=== END WORK SESSION ===
```

**Output Contract**:
```json
{
  "sql": "SELECT ...",
  "explanation": "...",
  "self_verify_ok": true,
  "data_validation_ok": true,
  "data_validation_notes": "5 rows, revenue range: 1000-50000, all non-null",
  "resolved_entities": {"products": [{"id": 5, "name": "Gạo ST25"}]},
  "empty_is_legitimate": true,
  "clarify_request": null
}
```

### 3.3 Mapping: Logic cũ → Logic mới

| Logic cũ (code) | → | Logic mới (skill) |
|-----------------|---|-------------------|
| `verify_sql_intent.py` | → | Step 5: Tự kiểm tra intent |
| `sql_review.py` + hints | → | Step 5: Tự review SQL |
| `validate_sql.py` | → | Step 5: Tự check schema mapping |
| `analyze_empty_result.py` | → | Step 7: Tự phân tích empty result |
| `sql_table_selection.py` | → | Step 1 + Step 4: Tự chọn bảng từ schema |
| `sql_similarity.py` | → | Track trong reasoning |
| `sql_allowlist.py` | → | Step 5: Tự check bảng có trong schema |
| `sql_clarify.py` | → | Step 3 + Step 7: Confirm với user |

---

## 4. Files Affected

### 4.1 Files Giữ Lại (Reuse)

| File | Mục đích |
|------|----------|
| `sql_executor.py` | `HttpSpringSqlExecutor` — execute SQL qua Spring |
| `sql_safety.py` | `enforce_read_only_sql()` — basic safety check (56 dòng) |
| `pg_schema_context.py` | Load schema từ Postgres |
| `sql_prompts.py` | `format_schema_block()` — format schema cho prompt |
| `sql_query_domain.py` | Domain detection (optional hints) |
| `tool_registry.py` | Đăng ký manifest (giữ nguyên) |
| `gen_sql.md` | Skill file cũ (sẽ viết lại) |

### 4.2 Files Mới/Viết Lại

| File | Mô tả |
|------|-------|
| `sql_query.py` | Tool đơn giản, không phụ thuộc subgraph |
| `gen_sql.md` | Skill mới (~200-250 dòng) |

### 4.3 Files Xoá

**Core pipeline** (~15 files):
- `sql_subgraph.py`
- `sql_pipeline.py` (toàn bộ nodes)
- `verify_sql_intent.py`
- `validate_sql.py`
- `analyze_empty_result.py`
- `sql_table_selection.py`
- `sql_allowlist.py`
- `sql_clarify.py`
- `sql_similarity.py`
- `feedback.py` (đa phần)
- `business_scope.py` (đa phần)
- `schema_explore.py` node
- `chart_readiness.py`
- `chart_sql_shape.py`
- `sql_review_hints.py`

**Prompt files** (~4 files):
- `prompts/agents/sql_review.md`
- `prompts/agents/verify_sql_intent.md`
- `prompts/agents/sql_table_pick.md`
- `prompts/agents/analyze_empty_result.md`
- `prompts/agents/schema_explore.md`

**Main graph changes**:
- `main_graph.py`: Bỏ `sql_branch` node, route `classify_intent` → `agent_planner` (hoặc chat_normal)
- `sql_query.py`: Đăng ký lại manifest

---

## 5. Migration Strategy

### Phase 1: Write New Tool + Skill
1. Viết `gen_sql.md` mới (skill chi tiết)
2. Viết `sql_query.py` mới (tool đơn giản)
3. Unit tests cho tool mới

### Phase 2: Switch Routes
1. Cập nhật `main_graph.py`: bỏ `sql_branch`, route qua `agent_planner`
2. Cập nhật `tool_registry.py`: đăng ký tool mới
3. Integration tests

### Phase 3: Cleanup
1. Xoá các files cũ
2. Xoá các prompt files cũ
3. Update docs

---

## 6. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM không tự kiểm tra tốt | Skill chi tiết với checklist rõ ràng; LLM tự retry qua conversation |
| Empty result không được phát hiện | Step 7 trong skill yêu cầu phân tích chi tiết; LLM tự retry |
| Entity resolution không chính xác | Retry 3 lần với 3 SQL khác nhau; confirm với user nếu không chốt được |
| Mất deterministic validation | Chấp nhận: LLM đủ mạnh để tự check qua schema |
| Chart pipeline bị ảnh hưởng | Chart node sẽ xử lý riêng, không phụ thuộc SQL subgraph |
| Data validation không phát hiện lỗi business logic | Step 8 chỉ check sanity (NULL, số âm, ngày sai); user là validator cuối cùng |
| LLM retry loop sinh SQL trùng nhau | Skill yêu cầu đọc conversation history, thử cách tiếp cận khác |
| LLM không biết khi nào dừng retry | Skill quy định max 3 lần retry, sau đó confirm user |

---

## 7. Success Criteria

- [ ] Code giảm ~80% (từ ~30 files xuống ~5 files cốt lõi)
- [ ] Tool đơn giản, không có retry loop trong code
- [ ] Skill hướng dẫn LLM tự kiểm tra và tự retry hiệu quả
- [ ] LLM đọc được error/empty/data từ tool và quyết định retry đúng
- [ ] Empty result được xử lý đúng (legitimate vs wrong) qua LLM retry
- [ ] Entity resolution hoạt động cho câu hỏi mơ hồ
- [ ] Data validation phát hiện lỗi cơ bản (NULL, số âm, ngày sai)
- [ ] LLM không retry vô hạn (max 3 lần, sau đó confirm user)
- [ ] Integration tests pass

---

## 8. Open Questions

1. **Chart pipeline**: Hiện tại `chart_readiness` nằm trong SQL subgraph. Sau khi bỏ subgraph, chart node sẽ xử lý thế nào?
   - **Đề xuất**: Chart node tự gọi `sql_query` tool, tự xử lý chart-specific logic

2. **Business scope**: Hiện tại `business_scope.py` quản lý scope qua các turn. Sau khi bỏ, scope sẽ được quản lý thế nào?
   - **Đề xuất**: Scope được truyền qua `TurnContext`, LLM tự xử lý qua skill

3. **Schema loading**: Hiện tại có nhiều cách load schema (schema_explore, pg_schema_context, spring_describe). Sau khi bỏ, chỉ giữ cách nào?
   - **Đề xuất**: Chỉ giữ `pg_schema_context.py` (load từ Postgres trực tiếp)

---

## 9. Conclusion

Thiết kế mới đơn giản hoá pipeline SQL bằng cách:
1. **Bỏ LangGraph subgraph** — chỉ giữ 1 Harness tool
2. **Chuyển logic validation vào skill** — LLM tự kiểm tra qua prompt chi tiết
3. **Thêm entity resolution** — xử lý câu hỏi mơ hồ trước khi sinh SQL chính
4. **LLM-driven retry** — tool chỉ execute 1 lần, LLM đọc kết quả và quyết định retry (error/empty/data validation)
5. **Data validation** — LLM kiểm tra chất lượng data sau khi execute

Kết quả: Code giảm ~80%, dễ bảo trì, LLM chịu trách nhiệm chất lượng SQL + data + retry logic.
