# Answer Quality Upgrade — Implementation Plan

> **Trạng thái**: **Implemented** (2026-05-17) theo các đề xuất mặc định Q1–Q8. Phase 7 middleware chưa làm (helper `finalize_answer` dùng chung tại từng node).

## Goal

Nâng cấp mọi path ghi `final_answer` trong LangGraph `ai_python`, đảm bảo:

1. **Không trả lời cụt** — Có ngữ cảnh, giải thích, gợi ý bước tiếp theo khi phù hợp.
2. **Tự động làm giàu câu trả lời** — Khi output quá ngắn hoặc thiếu hướng dẫn, hệ thống **viết lại / mở rộng** (LLM enrich hoặc template), không trả thẳng bản cụt cho user.

**Phạm vi phase này (đề xuất mặc định):** làm giàu **văn bản** (`final_answer`). **Re-query SQL** khi thiếu dữ liệu là scope **riêng** (xem [Q1](#q1-có-re-query-sql-khi-thiếu-dữ-liệu-không)) — không implement ngầm trong enrich trừ khi đã chốt.

---

## Quyết định cần hỏi (Product/Tech)

Các câu dưới đây cần **một dòng trả lời** (chọn A/B hoặc điền ngưỡng) trước khi code. Cột **Đề xuất** là default nếu team không phản hồi trong 48h.

### Q1: Có re-query SQL khi thiếu dữ liệu không?

| | |
|---|---|
| **Câu hỏi** | Khi user hỏi số liệu mà `chat_normal` không có DB, hoặc `summarize` trả empty — hệ thống có được **chạy lại pipeline SQL** (prompt/SQL mới) trước khi trả lời không? |
| **Vì sao cần hỏi** | Goal #2 gốc nói "query lại"; toàn bộ kiến trúc enrich chỉ **sửa text**, không lấy thêm rows. Hai hướng khác latency, rủi ro loop SQL, và phạm vi task. |
| **Lựa chọn** | **A)** Chỉ enrich text (không re-query). **B)** Re-query tối đa 1 lần khi `result_empty` và intent = data_query. **C)** `chat_normal` detect thiếu số liệu → route sang nhánh SQL (đổi graph, không chỉ prompt). |
| **Đề xuất** | **A** cho phase hiện tại; ghi backlog **B** sau khi có metric re-ask. |
| **Đã chốt** | **A** |
| **Ảnh hưởng** | A → chỉ sửa plan Phase 2–3. B/C → thêm node/edge, timeout SQL, test `docs/test-ai`. |

---

### Q2: `chat_normal` khi user hỏi số liệu cụ thể?

| | |
|---|---|
| **Câu hỏi** | User hỏi kiểu *"Doanh thu tháng này bao nhiêu?"* nhưng router đưa vào `chat_normal` — mong đợi là gì? |
| **Vì sao cần hỏi** | Enrich chỉ làm câu trả lời dài hơn, **không** tự có số từ DB → dễ hallucinate nếu prompt không chặt. |
| **Lựa chọn** | **A)** Enrich + nhắc "hãy hỏi lại để tra cứu số liệu" (không số). **B)** Sửa `intent` router để ít khi vào `chat_normal` với data questions. **C)** Cả A và B. |
| **Đề xuất** | **C** — router trước, enrich sau. |
| **Đã chốt** | **C** (`intent.md` + enrich `chat_normal`) |
| **Ảnh hưởng** | B/C → có thể sửa `intent.md` / `main_graph.py`, không chỉ `chat_normal.py`. |

---

### Q3: Clarify UI — dài `final_answer` hay giữ intro ngắn?

| | |
|---|---|
| **Câu hỏi** | `domain_guard` clarify: hiện `final_answer` = intro ngắn (~1 câu) + chi tiết trong `domain_clarify_sse` (bubble FE). Có **bắt buộc** `final_answer` ≥150 ký tự không? |
| **Vì sao cần hỏi** | Code `_pack_clarify` dùng `_short_clarify_intro()`, **không** dùng `assistant_message` LLM. Chỉ sửa prompt `domain_guard.md` **không đủ**. Dài hóa intro có thể **trùng** nội dung bubble. |
| **Lựa chọn** | **A)** Giữ intro ngắn; quality gate **skip** clarify (`scenario=clarify_sse`). **B)** Dài hóa intro; FE ẩn bớt bubble trùng. **C)** Reject ≥150 chars; clarify exempt. |
| **Đề xuất** | **A** cho clarify; **C** cho reject (≥150 chars qua prompt + `_pack_reject`). |
| **Đã chốt** | **A** + **C** |
| **Ảnh hưởng** | Phase 4: sửa `domain_guard.py` + `QualityContext.skip_quality_check` hoặc profile `clarify`. |

---

### Q4: Ma trận ngưỡng độ dài theo scenario?

| | |
|---|---|
| **Câu hỏi** | Một `MIN_ANSWER_CHARS = 80` cho mọi node có chấp nhận được không? |
| **Vì sao cần hỏi** | Confirm draft, chart success ("Đã tạo biểu đồ…") có thể hợp lệ <80 chars; reject/empty cần ≥200. |
| **Lựa chọn** | Dùng bảng [Quality profiles](#quality-profiles-theo-scenario) (đề xuất). |
| **Đề xuất** | Profiles theo `scenario`, không một ngưỡng global. |
| **Ảnh hưởng** | `answer_quality.py` nhận `QualityContext.scenario`. |

---

### Q5: LLM enrich — role, timeout, khi vẫn fail?

| | |
|---|---|
| **Câu hỏi** | Enrich gọi model nào? Timeout? Sau 1 lần enrich vẫn không đạt heuristic thì trả gì? |
| **Vì sao cần hỏi** | Registry hiện có `chat`, `summarize` (text); chưa có role `enrich`. |
| **Lựa chọn** | Role: **A)** tái dùng `chat`. Timeout: **15s** (cùng client HTTP hiện có). Fail: **A)** trả bản enrich dù chưa đạt **B)** trả hardcoded template **C)** trả bản gốc + log warning. |
| **Đề xuất** | Role `chat`; timeout 15s; fail → **B** nếu có `fallback_template_id`, else **A**. |
| **Ảnh hưởng** | `enforce_answer_quality()` + constants `answer_fallbacks.py` (mới, optional). |

---

### Q6: Phase 7 middleware hay helper chung ngay từ Phase 1?

| | |
|---|---|
| **Câu hỏi** | Gọi `enforce_answer_quality()` ở từng node (2–6) hay một middleware graph sau mọi node? |
| **Vì sao cần hỏi** | Middleware trễ → dễ **double enrich** nếu node cũng gọi enrich. |
| **Lựa chọn** | **A)** Phase 1 tạo helper; node gọi 1 dòng; Phase 7 chỉ refactor gom chỗ (không logic mới). **B)** Chỉ middleware, node không gọi tay. |
| **Đề xuất** | **A** — một implementation duy nhất trong `answer_quality.py`. |
| **Ảnh hưởng** | Tránh duplicate LLM calls. |

---

### Q7: Feature flag & rollout?

| | |
|---|---|
| **Câu hỏi** | Có cần tắt quality gate khi debug/production incident không? |
| **Lựa chọn** | **A)** `ANSWER_QUALITY_ENABLED=true` (default true). **B)** Luôn bật. |
| **Đề xuất** | **A** trong `.env.example`. |
| **Ảnh hưởng** | `settings.py` + check đầu `enforce_answer_quality`. |

---

### Q8: Nối test tự động?

| | |
|---|---|
| **Câu hỏi** | Tiêu chí done có chạy `docs/test-ai/run_test.py` / pytest không? |
| **Đề xuất** | Thêm ≥3 case vào `docs/test-ai` (empty SQL, domain reject, chart_fail) + unit test `check_answer_quality` với profiles. |

---

## Bảng node — phạm vi đầy đủ

Mọi path ghi `state["final_answer"]` (grep `ai_python/app/graph`):

| Graph node | File | Scenario (`QualityContext`) | Quality gate? | Enrich? | Ghi chú |
|------------|------|----------------------------|---------------|---------|---------|
| `chat_normal` | `chat_normal.py` | `chat` | Có | Có | Không có DB context |
| `summarize_answer` | `summarize.py` | `sql_summary` / `sql_empty` / `sql_error` | Có | Có (empty/error ưu tiên template + LLM) | Empty hiện ~120 chars cố định |
| `domain_guard` reject | `domain_guard.py` | `domain_reject` | Có | Có | Dùng `assistant_message` LLM |
| `domain_guard` clarify | `domain_guard.py` | `domain_clarify` | **Skip** (Q3) | Không | Intro ngắn + `domain_clarify_sse` |
| `agent_review` | `chart_report.py` | `chart_success` / `chart_review` | Có (review fail) | Có khi fail | Role LLM: `review` |
| `chart_fail_message` | `chart_report.py` | `chart_fail` | Có | Có | Template cứng, **không** qua `agent_review` |
| `catalog_draft` | `catalog_draft.py` | `draft_confirm` | Có (profile nhẹ) | Tùy Q4 | Liệt kê items từ state |
| `inventory_draft` | `inventory_draft.py` | `draft_confirm` | Có | Tùy Q4 | Giống catalog |
| SQL pipeline clarify | `sql_pipeline.py` | `sql_clarify` | TBD (Q3) | TBD | `final_answer` = intro clarify |
| Draft entity clarify | `draft_entity_resolution.py` | `draft_clarify` | TBD | TBD | Body + bullet questions |

**Không** set `final_answer`: `intent`, `sql_pipeline` (success path), `query_table`, `schema_explore`, … — chỉ patch state trung gian.

---

## Problem Analysis

### Root cause
- Prompt không yêu cầu độ đầy đủ tối thiểu theo **loại** câu trả lời.
- Không có `check_answer_quality` + enrich tập trung.
- Một số path **cố ý** ngắn (clarify SSE) nhưng plan cũ áp ngưỡng chung → conflict.

---

## Solution Architecture

### Strategy: Heuristic gate → Text enrich (không LLM critique riêng)

```
Node tạo final_answer (draft)
    ↓
enforce_answer_quality()  ← một helper, mọi phase dùng chung
    ↓
check_answer_quality(answer, QualityContext)   # heuristic only
    ↓
┌──────────────┬──────────────────────────────┐
│ passed       │ failed & enrich_allowed      │
└──────┬───────┴──────────────┬───────────────┘
       │                      ↓
       │              LLM invoke (role: chat)
       │              system: answer_enrich.md
       │              + optional scenario context
       │                      ↓
       │              check lần 2 (không enrich lần 3)
       │                      ↓
       │              fail → fallback template (nếu có)
       └──────────────────────┘
                    ↓
              truncate max ~2000 chars
                    ↓
              return final_answer
```

**Không** có bước LLM "critique pass/fail" riêng — LLM chỉ dùng cho **enrich**. Heuristic = self-critique.

---

## Quality profiles (theo scenario)

| `scenario` | `min_chars` | Bắt buộc gợi ý? | Pattern đặc biệt | `skip_quality` |
|------------|-------------|-----------------|------------------|----------------|
| `chat` | 80 | Khuyến khích (không fail cứng) | — | false |
| `sql_summary` | 80 | false | — | false |
| `sql_empty` | 200 | true (≥3 gợi ý) | no-data patterns | false |
| `sql_error` | 150 | true | không fail vì từ "xin lỗi" nếu ≥150 | false |
| `domain_reject` | 150 | true (≥2 ví dụ module) | — | false |
| `domain_clarify` | — | — | — | **true** (mặc định Q3-A) |
| `chart_success` | 40 | false | — | false |
| `chart_review` / `chart_fail` | 120 | true | — | false |
| `draft_confirm` | 60 | next steps | — | false |
| `sql_clarify` / `draft_clarify` | — | — | — | **true** until Q3 resolved |

**Pattern "no data"** (chỉ khi `sql_empty`): nếu match `không có dữ liệu|không tìm thấy|…` và `len < min_chars` → fail. **Không** dùng pattern `xin lỗi` cho `sql_error` (tránh false positive).

---

## Phase 1: Core module (làm trước)

### 1.1 `app/graph/answer_quality.py`

```python
@dataclass(frozen=True)
class QualityContext:
    node_name: str
    scenario: str
    skip_quality: bool = False
    has_query_result: bool | None = None  # True/False/None
    user_question: str | None = None
    enrich_allowed: bool = True
    fallback_template_id: str | None = None  # key in answer_fallbacks

@dataclass
class QualityVerdict:
    passed: bool
    issues: list[str]
    enrichment_hints: list[str]

def check_answer_quality(answer: str, *, ctx: QualityContext) -> QualityVerdict: ...

def enforce_answer_quality(
    answer: str,
    *,
    ctx: QualityContext,
    deps: GraphDeps,
    max_enrich_attempts: int = 1,
) -> str: ...
```

- Load profile từ dict `SCENARIO_PROFILES[ctx.scenario]`.
- `skip_quality=True` → return answer ngay.
- Emit `emit_agent_trace` phase `answer_quality` / `answer_enrich`.

### 1.2 `app/prompts/agents/answer_enrich.md`

Placeholder: `{previous_answer}`, `{issues}`, `{hints}`, `{user_question}`, `{scenario}`.

Rules giữ như bản cũ + **không invent số liệu** + min 200 chars khi scenario là `sql_empty` / `sql_error`.

### 1.3 `app/graph/answer_fallbacks.py` (optional, khuyến nghị)

Hardcoded templates: `sql_empty_vi`, `sql_error_vi`, `chart_fail_vi`, `domain_reject_stub_vi` — mỗi template ≥200 chars, có 3 bullet gợi ý.

### 1.4 Settings

```env
ANSWER_QUALITY_ENABLED=true
ANSWER_QUALITY_MAX_CHARS=2000
ANSWER_ENRICH_TIMEOUT_SEC=15
```

---

## Phase 2: `chat_normal`

**Flow:** `invoke chat` → `enforce_answer_quality(..., scenario="chat")`.

**Prompt** `chat_normal.md`: thêm rule không trả lời cụt; nếu cần số liệu thì hướng dẫn câu hỏi tra cứu (không bịa số).

**Done khi:** unit test + 1 manual case trong docs/test-ai.

---

## Phase 3: `summarize_answer`

| Scenario | Hiện tại | Mới |
|----------|----------|-----|
| Empty rows | Cố định ~120 chars | LLM `summarize_empty` **hoặc** enrich với `ctx` có `normalized_user_question`, `sql` (nếu có trong state) |
| SQL error | "Xin lỗi, không hoàn tất…" | `scenario=sql_error`, template fallback + enrich |
| Summary ngắn | Trả thẳng | `scenario=sql_summary`, enrich nếu <80 |

**Prompt mới (đề xuất):** `app/prompts/agents/summarize_empty.md` — chuyên empty result (đừng nhầm với `answer_enrich` generic).

**Input LLM empty:** `user_question`, `conversation tail`, `selected_tables` (nếu có), **không** gửi full rows.

---

## Phase 4: `domain_guard`

| Action | Việc làm |
|--------|----------|
| **reject** | Prompt `domain_guard.md`: module hỗ trợ + 2–3 ví dụ; `_pack_reject` qua `enforce_answer_quality(scenario=domain_reject)` |
| **clarify** | Mặc định `skip_quality=True`; nếu Q3-B: sửa `_pack_clarify` dùng `assistant_message` LLM thay `_short_clarify_intro` |

---

## Phase 5: Chart (`chart_report.py`)

Tách rõ hai path:

| Path | Node | Việc làm |
|------|------|----------|
| Review OK/fail text | `agent_review` | Prompt `chart_review.md`: fail phải giải thích + gợi ý; `enforce` khi `final_answer` ngắn |
| Abort chart | `chart_fail_message` | Thay template cứng bằng `enforce(scenario=chart_fail)` + fallback `chart_fail_vi` |

**Q phụ (chưa chốt):** Khi có `query_table_sse` nhưng chart fail — có tự chèn *"Xem bảng bên dưới"* vào `final_answer` không? → cần xác nhận với FE (widget đã hiển thị bảng).

---

## Phase 6: Draft nodes

- Đọc payload từ state (field hiện có trong `catalog_draft` / `inventory_draft`).
- Format: danh sách tối đa N dòng (đề xuất N=10) + next steps.
- `enforce_answer_quality(scenario=draft_confirm)`.
- Không enrich nếu message đã > `min_chars` và có next steps.

---

## Phase 7: Middleware (refactor only)

Sau Phase 2–6 ổn định: tùy chọn wrap trong `main_graph` **chỉ nếu** mọi node đã bỏ gọi tay trùng — **không** thêm lần enrich thứ hai.

---

## Files to Create / Modify

### Create

| File | Purpose |
|------|---------|
| `ai_python/app/graph/answer_quality.py` | Profiles, check, enforce |
| `ai_python/app/graph/answer_fallbacks.py` | Hardcoded templates |
| `ai_python/app/prompts/agents/answer_enrich.md` | Generic enrich |
| `ai_python/app/prompts/agents/summarize_empty.md` | Empty SQL dedicated |

### Modify

| File | Changes |
|------|---------|
| `chat_normal.py` / `chat_normal.md` | enforce + prompt |
| `summarize.py` / `summarize.md` | empty/error/summary + `summarize_empty` |
| `domain_guard.py` / `domain_guard.md` | reject enrich; clarify per Q3 |
| `chart_report.py` / `chart_review.md` | `agent_review` + `chart_fail_message` |
| `catalog_draft.py` / `inventory_draft.py` | confirmation body |
| `config/settings.py` / `.env.example` | flags Q7 |
| `sql_pipeline.py` | clarify: align sau Q3 |
| `draft_entity_resolution.py` | clarify: align sau Q3 |

---

## Key Design Decisions (đã chốt trong plan)

| Decision | Rationale |
|----------|-----------|
| Heuristic trước, LLM chỉ enrich | Nhanh, rõ ràng, không 2 lần LLM critique |
| Max 1 enrich | Latency + chống loop |
| Profiles theo `scenario` | Tránh false positive clarify/chart OK |
| Một helper `enforce_answer_quality` | Phase 7 không duplicate logic |
| Không pattern `xin lỗi` cho `sql_error` | Tránh enrich vô ích |
| `skip_quality` cho clarify SSE | Giữ contract FE bubble |

---

## Fallback matrix

| Tình huống | Hành vi |
|------------|---------|
| `ANSWER_QUALITY_ENABLED=false` | Trả answer gốc |
| LLM registry None | Template `fallback_template_id` hoặc answer gốc |
| Enrich timeout/error | Template hoặc answer gốc + log warning |
| Sau enrich vẫn fail heuristic | Dùng bản enrich (thường dài hơn gốc) |
| `len(answer) > MAX_CHARS` | Truncate + "…" |

---

## Testing

### Manual / docs/test-ai
- [ ] Chat chung chung → có gợi ý, không <80 chars (hoặc đã enrich)
- [ ] SQL empty → ≥200 chars, ≥3 gợi ý
- [ ] SQL error → ≥150 chars, không bị enrich chỉ vì "xin lỗi"
- [ ] Chart `chart_fail_message` → ≥120 chars
- [ ] Domain reject → module + ví dụ
- [ ] Domain clarify → intro ngắn vẫn OK (skip gate)
- [ ] Draft confirm → có items + next steps
- [ ] LLM off → fallback template
- [ ] Chỉ 1 lần enrich (trace log đếm)

### Unit
- `test_answer_quality.py`: mỗi `scenario` × pass/fail edge cases.

### Metrics (log structured)
- `answer_chars`, `scenario`, `enrich_triggered`, `enrich_failed`, `quality_passed`

---

## Implementation order

1. Chốt **Q1–Q3** (block scope SQL + clarify).
2. Phase 1 — `answer_quality.py` + tests + flag.
3. Phase 3 → 5 → 2 → 6 (ưu tiên pain user: SQL empty, chart fail, reject).
4. Phase 4 + sql/draft clarify sau Q3.
5. Phase 7 refactor nếu cần.

---

## Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Latency | Max 1 enrich; flag tắt Q7 |
| Hallucinate số | Prompt + không enrich `chat` bằng số giả |
| Trùng clarify bubble | `skip_quality` clarify |
| Double enrich | Một helper, middleware không thêm logic |
| Answer quá dài | `ANSWER_QUALITY_MAX_CHARS=2000` |

---

## Changelog plan

| Ngày | Thay đổi |
|------|----------|
| 2026-05-17 | Bổ sung Q1–Q8, bảng node đầy đủ, profiles, `QualityContext`, tách chart_fail, làm rõ enrich vs re-query |
