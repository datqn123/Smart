# SRS-003 (upgrade/ai-python): HITL Resume Flow cho Harness Loop

- **Status**: DRAFT
- **Author**: AI workflow
- **Date**: 2026-06-07
- **Scope tier**: Feature — bổ sung vào SRS-002 (Harness-Orchestrated Agentic Loop)
- **Related**: `docs/upgrade/ai-python/srs/002_harness-orchestrated-agentic-loop.md`, `app/harness/orchestrator.py`, `app/graph/tools/catalog_draft.py`, `app/graph/tools/inventory_draft.py`

---

## 1. Vấn đề

SRS-002 đã thiết kế HITL theo mô hình "tool trả `pending_hitl` → orchestrator dừng loop → FE hiển thị form → user xác nhận → lượt kế tiếp resume". Tuy nhiên **lượt kế tiếp chưa được xử lý**:

- `CatalogDraftTool` và `InventoryDraftTool` trả `pending_hitl` đúng, orchestrator dừng và phát SSE `draft`/`inventory_draft`.
- Khi FE gửi request kế tiếp với `request.options.clarification` filled, Strangler routing **không nhận ra đây là lượt resume HITL** — nó chạy `_quick_classify_harness_intent` bình thường và có thể route nhầm sang legacy graph, hoặc tạo scratchpad mới bỏ qua context draft.

### 1.1 Luồng hiện tại (broken)

```
Turn N:   user "tạo sản phẩm X"
          → harness loop → CatalogDraftTool → pending_hitl
          → SSE "draft" phát → FE hiện form
          → suppress_done=True (không gửi "done" → FE giữ stream?)

Turn N+1: user submit form → request.options.clarification = {fields...}
          → _quick_classify_harness_intent("tạo sản phẩm X") = "catalog_draft"
          → nếu may mắn route đúng harness → scratchpad MỚI, không có draft context
          → CatalogDraftTool chạy lại từ đầu (re-generate draft) ← SAI
```

### 1.2 Luồng đúng (target)

```
Turn N:   → CatalogDraftTool → pending_hitl → SSE "draft" → dừng, không gửi "done"
          → Server lưu resume_token = thread_id

Turn N+1: request có clarification → nhận diện là HITL resume turn
          → KHÔNG chạy lại CatalogDraftTool
          → Lấy draft payload từ lượt trước (qua thread_id/checkpoint)
          → Gọi Spring API POST để confirm draft với user's clarification
          → Trả final_answer "Đã tạo sản phẩm X thành công"
```

---

## 2. Phạm vi (Scope)

**Trong phạm vi:**
- Nhận diện HITL resume turn trong Strangler routing
- Forward `clarification_response` vào harness path đúng
- `CatalogDraftTool` / `InventoryDraftTool` xử lý clarification (confirm → POST Spring) thay vì generate lại draft
- Lưu `resume_token` (thread_id) để tool kế tiếp biết draft nào đang pending

**Ngoài phạm vi:**
- Timeout / expiry của pending HITL (để v2)
- Multi-step HITL (nhiều form liên tiếp trước khi confirm)
- HITL cho tool khác ngoài catalog_draft / inventory_draft

---

## 3. Thiết kế

### 3.1 Nhận diện HITL resume turn

Một request là HITL resume khi **có `clarification_response` không null** trong `request.options`. Strangler routing kiểm tra điều kiện này **trước** `_quick_classify_harness_intent`:

```python
# app/api/runtime.py — _should_use_harness_loop (cập nhật)

def _should_use_harness_loop(request: ChatRequest, graph_settings: Any) -> bool:
    if not bool(getattr(graph_settings, "harness_loop_enabled", False)):
        return False
    # HITL resume turn — luôn route sang harness nếu có pending clarification
    if getattr(request.options, "clarification", None) is not None:
        return True
    allowed = { ... }
    intent = _quick_classify_harness_intent(request.message)
    return intent in allowed
```

### 3.2 Lưu `pending_hitl_state` trong TurnScratchpad

Khi Turn N kết thúc với `pending_hitl`, orchestrator cần lưu đủ context để Turn N+1 biết phải làm gì. Thông tin này được ghi vào LangGraph checkpointer (dưới `thread_id`) dưới dạng một key đặc biệt trong `AgentState`:

```python
# app/graph/state.py — thêm key
pending_hitl_tool: str | None     # "catalog_draft" | "inventory_draft"
pending_hitl_payload: dict | None # draft payload đã generate ở Turn N
```

`pending_hitl_tool` và `pending_hitl_payload` là **persistent** (KHÔNG nằm trong `_TRANSIENT_KEYS`) để checkpointer giữ qua turns.

### 3.3 Cập nhật orchestrator — ghi pending state

```python
# app/harness/orchestrator.py — sau khi yield PendingHitlEvent
if result.pending_hitl:
    if result.sse_payload:
        yield SsePayloadEvent(result.pending_hitl.event_name, result.sse_payload)
    # Ghi context vào harness state để Turn N+1 đọc
    yield PersistHitlEvent(
        tool_name=tool_inp.tool_name,
        payload=result.sse_payload or {},
        resume_token=result.pending_hitl.resume_token,
    )
    yield PendingHitlEvent(result.pending_hitl)
    return
```

`PersistHitlEvent` là event mới → `_event_to_stream_chunk` trong `runtime.py` map nó thành chunk cập nhật `pending_hitl_tool` và `pending_hitl_payload` trong state (qua legacy graph checkpoint, hoặc in-memory store đơn giản keyed by thread_id).

**Phương án đơn giản hơn (recommended cho v1)**: dùng in-memory dict trong `LangHarnessRuntime` keyed by `thread_id`:

```python
# app/api/runtime.py
class LangHarnessRuntime:
    def __init__(self, ...):
        ...
        self._pending_hitl: dict[str, PendingHitlRecord] = {}
        # thread_id → {tool_name, payload, created_at}
```

### 3.4 Tool adapter nhận clarification — xử lý confirm path

```python
# app/graph/tools/catalog_draft.py — CatalogDraftTool.invoke (cập nhật)

async def invoke(self, args: dict[str, Any], ctx: TurnContext) -> ToolResult:
    # Nếu có clarification → đây là confirm turn, không generate lại
    if ctx.clarification_response is not None:
        return await self._confirm(ctx)

    # Normal path: generate draft
    ...

async def _confirm(self, ctx: TurnContext) -> ToolResult:
    """Gọi Spring API để POST draft đã xác nhận."""
    pending = ctx.pending_hitl_payload  # truyền vào từ orchestrator
    if not pending:
        return ToolResult(ok=False, ..., observation_text="No pending draft found.")
    # POST đến Spring endpoint catalog confirm
    result = await self._deps.sql_executor.aexecute(...)  # hoặc HTTP POST riêng
    return ToolResult(ok=True, ..., observation_text=f"Đã tạo {pending.get('name', 'sản phẩm')} thành công.")
```

### 3.5 Cập nhật `TurnContext` — thêm clarification fields

```python
@dataclass(frozen=True)
class TurnContext:
    ...
    clarification_response: dict | None = None  # từ request.options.clarification
    pending_hitl_payload: dict | None = None    # từ LangHarnessRuntime._pending_hitl
```

### 3.6 Cập nhật `_build_turn_context` trong runtime.py

```python
def _build_turn_context(request, *, correlation_id, bearer_token, pending_hitl_payload=None):
    clar = getattr(request.options, "clarification", None)
    return TurnContext(
        ...
        clarification_response=clar.model_dump(mode="json") if clar else None,
        pending_hitl_payload=pending_hitl_payload,
    )
```

---

## 4. Luồng hoàn chỉnh sau SRS-003

```
Turn N — "tạo sản phẩm Áo thun size M":
  1. _should_use_harness_loop → True (intent = catalog_draft)
  2. HarnessOrchestrator.run()
     step 0: LLM decide → call_tool(catalog_draft, {request: "Áo thun size M"})
     step 1: policy.check OK
     step 2: CatalogDraftTool.invoke → pending_hitl + draft_sse
     step 3: yield SsePayloadEvent("draft", payload) → FE hiện form
     step 4: LangHarnessRuntime lưu _pending_hitl[thread_id] = {tool: "catalog_draft", payload}
     step 5: yield PendingHitlEvent → suppress_done=True → stream kết thúc không có "done"

Turn N+1 — user submit form (clarification = {name: "Áo thun size M", price: 150000, ...}):
  1. _should_use_harness_loop → True (có clarification → bypass classifier)
  2. _build_turn_context với pending_hitl_payload từ _pending_hitl[thread_id]
  3. HarnessOrchestrator.run()
     step 0: LLM decide → call_tool(catalog_draft, {request: "confirm"})
     [hoặc orchestrator nhận diện clarification và gọi thẳng catalog_draft]
     step 1: CatalogDraftTool.invoke → ctx.clarification_response != None → _confirm path
     step 2: POST Spring → thành công
     step 3: ToolResult(ok=True, "Đã tạo Áo thun size M")
     step 4: LLM decide → final_answer
     step 5: yield FinalAnswerEvent → SSE "delta_full"
     step 6: yield "done"
  4. Xóa _pending_hitl[thread_id]
```

---

## 5. Yêu cầu chức năng

- **FR-1**: Request có `clarification_response != null` luôn route vào harness khi `harness_loop_enabled=True`, bất kể classifier result.
- **FR-2**: Khi tool trả `pending_hitl`, `LangHarnessRuntime` lưu `{tool_name, payload}` keyed by `thread_id`.
- **FR-3**: Lượt resume, `TurnContext` nhận được `clarification_response` và `pending_hitl_payload`.
- **FR-4**: `CatalogDraftTool` và `InventoryDraftTool` có hai path: **generate** (không có clarification) và **confirm** (có clarification).
- **FR-5**: Sau khi confirm thành công, xóa entry khỏi `_pending_hitl` store.
- **FR-6**: Nếu `_pending_hitl[thread_id]` không tồn tại khi resume (expired / server restart), trả lỗi rõ ràng cho FE thay vì crash.

## 6. Yêu cầu phi chức năng

- **NFR-1**: `_pending_hitl` là in-memory dict — chấp nhận mất state khi restart (v1). V2 persist vào Redis/DB.
- **NFR-2**: Entry trong `_pending_hitl` có TTL tối đa 30 phút (dùng `created_at` + kiểm tra khi lookup).
- **NFR-3**: SSE contract với FE không đổi — `draft`/`inventory_draft` event vẫn phát đúng.
- **NFR-4**: Legacy graph path (harness disabled) không bị ảnh hưởng.

---

## 7. Implementation slices

| Slice | File | Nội dung |
| :-- | :-- | :-- |
| H-1 | `app/api/runtime.py` | `_pending_hitl: dict` trong `LangHarnessRuntime`; cập nhật `_should_use_harness_loop`; lưu/xóa pending entry; `_build_turn_context` nhận `pending_hitl_payload` |
| H-2 | `app/harness/tool_registry.py` | Thêm `clarification_response` và `pending_hitl_payload` vào `TurnContext` |
| H-3 | `app/harness/orchestrator.py` | Thêm `PersistHitlEvent`; emit sau `SsePayloadEvent` khi `pending_hitl`; cập nhật `_event_to_stream_chunk` |
| H-4 | `app/graph/tools/catalog_draft.py` | Tách `invoke` thành generate path và `_confirm` path |
| H-5 | `app/graph/tools/inventory_draft.py` | Tương tự H-4 |

**Depends on**: SRS-002 / Tech Spec 001 hoàn thành (đã done).

---

## 8. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
| :-- | :-- | :-- |
| `_pending_hitl` mất khi server restart | Trung bình | Chấp nhận v1; FE hiển thị "phiên hết hạn" + hướng dẫn tạo lại |
| Thread_id không unique (collision) | Thấp | thread_id là UUID từ FE; collision thực tế không xảy ra |
| Clarification confirm gọi Spring endpoint nào | Cao | Cần xác nhận endpoint Spring cho POST catalog/inventory confirm trước khi code H-4/H-5 |

---

## 9. Open Questions

- **OQ-1**: Spring endpoint để POST confirm catalog draft là gì? (cần Team Backend confirm trước khi implement H-4)
- **OQ-2**: Spring endpoint để POST confirm inventory draft là gì?
- **OQ-3**: Khi `_pending_hitl` entry hết TTL (30 phút), trả FE error code gì? `HITL_EXPIRED`?

---

## 10. Acceptance Criteria

- **AC-1**: Turn N gửi "tạo sản phẩm X" → SSE `draft` phát, không có `done`.
- **AC-2**: Turn N+1 gửi `clarification_response` → route vào harness, không chạy lại draft generation, gọi Spring confirm API, trả `final_answer` và `done`.
- **AC-3**: Nếu restart server giữa N và N+1, FE nhận error message rõ ràng (không crash 500).
- **AC-4**: Legacy graph path (flag OFF) không thay đổi hành vi.
- **AC-5**: `_pending_hitl` entry bị xóa sau confirm thành công.
