# IntentSubagent — Phân tích chi tiết

> **File:** `app/harness/intent.py`  
> **Gọi từ:** `HarnessOrchestrator._dispatch()` tại `orchestrator.py:218-250`  
> **Gated bởi:** `agentic_intent_object_enabled` (default: `false`)

---

## 1. Vai trò

`IntentSubagent` là thành phần **phân tích ý định người dùng** trong Harness loop. Nó quyết định:

1. **User muốn làm gì?** → `intent_type` (`data_query`, `catalog_draft`, `inventory_draft`, `chart_report`, `chat`)
2. **Có đủ thông tin để chạy không?** → `mode`: `run` | `clarify` | `auto_assume`
3. **Entity nào được đề cập?** → fuzzy matching qua `EntityResolver`
4. **Key intent cho template lookup + K15** → semantic intent key

---

## 2. Luồng hoạt động

```
User message
     │
     ▼
HarnessOrchestrator._dispatch()
     │
     ├─ Bước 1: WorkingMemory trim history
     │
     ├─ Bước 2: IntentSubagent.analyze(question, memory, dictionary)
     │      │
     │      ├─ LLM available? → gọi "intent" role → astructured_predict(IntentObjectOutput)
     │      │                     fallback: _heuristic(question) nếu LLM lỗi
     │      │
     │      └─ LLM unavailable? → _heuristic(question) (keyword-based)
     │
     ├─ Bước 3: Build semantic intent key → _intent_key_from(intent)
     │
     ├─ Bước 4: IntentSubagent.decide(intent)
     │      │
     │      └─ Quyết định: run / clarify / auto_assume
     │
     ├─ Bước 5: Nếu mode == "clarify" → yield ClarifyEvent, return
     │
     ├─ Bước 6: Nếu mode == "auto_assume" hoặc "run" → attach assumptions
     │
     └─ Bước 7: Nếu plan DAG enabled + intent phù hợp → _run_plan_mode()
                Nếu không → reactive decision loop
```

---

## 3. Chi tiết các thành phần

### 3.1 IntentObject — Schema đầu ra của LLM

```python
class IntentObject(BaseModel):
    goal: str                          # Mục tiêu người dùng (VD: "Xem doanh thu tháng 3")
    intent_type: str                   # Phân loại: data_query, catalog_draft, inventory_draft, chart_report, chat
    required_data: list[str]           # Dữ liệu cần để hoàn thành (VD: ["revenue", "time_period"])
    resolved_entities: list[ResolvedEntity]  # Entity đã match (VD: sản phẩm, khách hàng)
    confidence: float                  # Độ tự tin 0.0 - 1.0
    ambiguities: list[Ambiguity]       # Các điểm mơ hồ cần làm rõ
    missing_required: list[str]        # Trường bắt buộc còn thiếu
```

### 3.2 IntentDecision — Quyết định sau phân tích

```python
class IntentDecision(BaseModel):
    mode: str                          # "run" | "clarify" | "auto_assume"
    clarify_questions: list[str]       # Câu hỏi làm rõ (nếu mode=="clarify")
    assumptions: list[str]             # Giả định (nếu mode=="auto_assume")
```

### 3.3 EntityResolver — Fuzzy Matching

```python
class EntityResolver:
    synonym_map: dict[str, list[str]]  # Từ đồng nghĩa → tên chuẩn
    catalog: list[dict]                # Danh sách entity có sẵn {entity_type, display}

    score_sync(raw, entity_type) → ResolvedEntity
```

Thuật toán:
1. **Normalize**: casefold, collapse whitespace
2. **Match với catalog**: dùng `SequenceMatcher` ratio + substring boost (0.8)
3. **Fallback synonym map**: nếu không match catalog, thử synonym map
4. **Score**: 0.0 - 1.0, lưu cả `raw` gốc và `matched` chuẩn

### 3.4 Heuristic Fallback

Khi LLM không available hoặc lỗi, dùng keyword matching:

| Keyword | intent_type |
|---------|-------------|
| `tạo sản phẩm`, `tạo danh mục`, `catalog` | `catalog_draft` |
| `nhập kho`, `xuất kho`, `tạo phiếu` | `inventory_draft` |
| `biểu đồ`, `chart`, `vẽ` | `chart_report` |
| `doanh thu`, `tồn kho`, `báo cáo`, `công nợ` | `data_query` |
| *none of the above* | `chat` |

Heuristic luôn trả về `confidence=0.9` (đủ để chạy, không cần clarify).

---

## 4. Decision Logic (`decide()`)

Đây là phần quan trọng nhất — quyết định mode dựa trên confidence và entities:

```
decide(intent):
  │
  ├─ 1. missing_required không phải time?
  │     YES → clarify (hỏi thông tin còn thiếu)
  │
  ├─ 2. missing_required CHỈ là time?
  │     YES → auto_assume (tự động giả định thời gian)
  │
  ├─ 3. confidence < intent_confidence_hitl (default 0.75)?
  │     YES → clarify (hỏi lại mục tiêu)
  │
  ├─ 4. entity_score < entity_score_hitl (default 0.6)?
  │     YES → clarify (hỏi entity chính xác)
  │
  ├─ 5. confidence < intent_confidence_run (default 0.9)?
  │     YES → auto_assume (chạy với giả định)
  │
  └─ 6. ELSE → run (tự tin chạy luôn)
```

### 4.1 Threshold settings

| Setting | Default | Ý nghĩa |
|---------|---------|---------|
| `intent_confidence_hitl` | 0.75 | Dưới ngưỡng này → clarify (hỏi người dùng) |
| `entity_score_hitl` | 0.6 | Entity không rõ ràng → clarify |
| `intent_confidence_run` | 0.9 | Trên ngưỡng này → chạy luôn, dưới → auto_assume |

### 4.2 Các câu hỏi clarify

```python
# Thiếu thông tin thời gian
→ "Bạn muốn xem trong khoảng thời gian nào? hôm nay, tháng này hoặc một khoảng ngày cụ thể."

# Thiếu thông tin khác
→ "Bạn vui lòng bổ sung thông tin còn thiếu để tôi xử lý chính xác hơn."

# Confidence thấp
→ "Tôi chưa đủ chắc để xử lý yêu cầu này. Bạn vui lòng nói rõ mục tiêu hoặc dữ liệu cần xem?"

# Entity không rõ
→ "Bạn muốn dùng chính xác đối tượng nào? Vui lòng chọn hoặc nhập lại tên đầy đủ."
   (kèm top 3 option gần nhất nếu có)
```

---

## 5. Tích hợp với Orchestrator

Tại `orchestrator.py:218-250`, IntentSubagent được gọi như sau:

```python
if bool(getattr(self._settings, "agentic_intent_object_enabled", False)):
    intent_agent = IntentSubagent(llm_registry=self._llm_registry, settings=self._settings)
    intent = await intent_agent.analyze(
        self._effective_question(scratchpad),  # question (có context nếu follow-up ngắn)
        memory_text=self._memory_text(scratchpad),  # 6 messages gần nhất
        dictionary_text="",  # hiện tại luôn rỗng
    )
    # Build semantic intent key cho template lookup + K15
    self._turn_intent_key = _intent_key_from(intent, fallback=self._original_question(scratchpad))

    intent_decision = intent_agent.decide(intent)
    if intent_decision.mode == "clarify":
        yield ClarifyEvent(...)
        return  # STOP — chờ user reply

    # Attach intent + assumptions vào TurnContext
    ctx = replace(ctx, intent_object=intent.model_dump(mode="json"), assumptions=list(intent_decision.assumptions))

    # Nếu plan DAG mode → chạy plan graph thay vì reactive loop
    if intent.intent_type in {"data_query", "chart_report"}:
        async for event in self._run_plan_mode(intent, scratchpad, ctx, recorder):
            yield event
        return
```

### 5.1 effective_question vs original_question

- `_original_question()`: lấy user message cuối cùng
- `_effective_question()`: nếu user message cuối quá ngắn (< 20 ký tự hoặc < 4 từ), prepend message trước đó để có context đầy đủ

---

## 6. Semantic Intent Key

Sau khi phân tích, intent key được build để dùng cho **template lookup** và **K15 aggregation**:

```python
def _intent_key_from(intent, *, fallback):
    entities = [e.matched for e in intent.resolved_entities]
    return build_intent_key(
        intent_type=intent.intent_type,
        goal=intent.goal,
        required_data=intent.required_data,
        entities=entities,
        fallback=fallback,
    )
```

Key format: `intent_type|goal|required_data|entities`

Giúp các phát biểu khác nhau của cùng một ý định chia sẻ cùng key (LOW-4).

---

## 7. Test Coverage

| File | Test | Scenario |
|------|------|----------|
| `test_intent_object.py` | `test_intent_high_confidence_runs` | confidence=0.95 → mode=run |
| | `test_intent_missing_required_clarifies` | missing time_period → clarify |
| | `test_intent_mid_confidence_auto_assume` | confidence=0.8 → auto_assume |
| | `test_entity_resolver_fuzzy_fallback` | fuzzy match "coca" → "Coca-Cola lon 330ml" |
| | `test_intent_subagent_llm_output` | LLM output → IntentObjectOutput |
| `test_intent_confidence_thresholds.py` | `test_intent_low_entity_score_clarifies` | entity_score=0.5 → clarify |
| | `test_intent_gate_clarify_emits_sse_clarify` | clarify → SSE domain_clarify_sse event |
| | `test_intent_llm_error_fallback_heuristic` | LLM lỗi → heuristic fallback vẫn chạy được |

---

## 8. Flow Diagram

```
                    IntentSubagent.analyze()
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      LLM available?              LLM unavailable?
      → astructured_predict       → _heuristic()
        (IntentObjectOutput)        (keyword-based)
              │                         │
              └────────────┬────────────┘
                           ▼
                   IntentObject
                   {goal, intent_type, confidence,
                    resolved_entities, missing_required}
                           │
                    IntentSubagent.decide()
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           clarify   auto_assume      run
              │            │            │
              ▼            ▼            ▼
        ClarifyEvent   attach       execute
        → đợi reply  assumptions   intent
                           │
                           ▼
                   plan DAG? → PlanGraph
                   hoặc reactive loop
```

---

## 9. Lưu ý

1. **Intent analysis là optional**: disabled mặc định (`agentic_intent_object_enabled=false`). Khi tắt, harness chạy reactive loop không cần intent.
2. **Heuristic là safety net**: đảm bảo hệ thống vẫn hoạt động khi LLM lỗi, nhưng chỉ phân loại được bằng keyword đơn giản.
3. **Time fields được ưu tiên**: nếu chỉ thiếu thời gian, không hỏi mà auto-assume (giả định năm gần nhất).
4. **EntityResolver dùng fuzzy matching đơn giản**: `SequenceMatcher` + substring boost, chưa dùng embedding/vector search.
5. **dictionary_text luôn rỗng**: parameter được design để mở rộng sau (ERP domain dictionary).
