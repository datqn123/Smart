# Design — Conversation Memory cho Agentic AI (ai_python)

**Ngày:** 2026-06-11
**Trạng thái:** Approved (brainstorming với user)
**Phạm vi:** `ai_python/app` — thay placeholder `app/memory/` bằng memory thật.

## Mục tiêu

Agentic AI nhớ được hội thoại theo `thread_id`: giữ **10 lượt (user → answer) gần nhất** verbatim;
quá 10 lượt thì **compact** phần cũ thành rolling summary bằng LLM; summary + lịch sử được
inject vào context để xử lý câu hỏi nối tiếp (ví dụ *"còn tháng trước thì sao?"*).

## Quyết định đã chốt (với user)

| Quyết định | Lựa chọn |
|---|---|
| Storage | **In-memory dict** (chấp nhận mất khi restart; không cần SQLite/Postgres vòng này) |
| Compaction | **LLM tóm tắt rolling** (merge summary cũ + lượt tràn → summary mới, tiếng Việt) |
| Ngữ cảnh cho tool | **SM viết lại câu hỏi** (`resolved_require`) + **mọi tool đều nhận summary** |
| Window | 10 lượt, config `MEMORY_WINDOW_TURNS=10` |

## Kiến trúc

### 1. Module `app/memory/` — `ConversationMemory`

```python
class ThreadMemory(TypedDict):
    turns: list[dict]      # [{"user": str, "answer": str}], tối đa window (10)
    summary: str | None    # rolling summary, None khi chưa compact

class ConversationMemory:
    def get_context(self, thread_id) -> ThreadMemory      # copy, không leak ref
    def append_turn(self, thread_id, user, answer) -> None
    def needs_compact(self, thread_id) -> bool             # len(turns) > window
    def compact(self, thread_id, *, llm) -> None           # LLM rolling summary
```

- `_store: dict[str, ThreadMemory]` — **singleton module-level** (hoặc `app.state`).
  KHÔNG tạo trong `get_deps()` vì hàm này chạy mỗi request (FastAPI Depends) —
  store sẽ bị reset liên tục. (PendingStore sống được vì backed bởi file SQLite.)
- Compaction: lấy các lượt tràn ra ngoài window (cũ nhất) + summary hiện tại →
  1 LLM call (role `default`, Qwen) → summary mới; giữ lại đúng 10 lượt gần nhất.
- Prompt compaction đặt tại `app/memory/compact_prompt.md` (theo idiom skill.md).
- **Degrade an toàn:** LLM compact lỗi → giữ summary cũ, vẫn drop lượt tràn, log warning,
  không crash request.
- Thread-safety: mutate dict dưới `asyncio.Lock` per-store (event loop đơn, đủ dùng).

#### Nội dung `compact_prompt.md` (đã chốt với user)

- **Output: plain text tiếng Việt — KHÔNG JSON** (compact không bao giờ chết vì lỗi
  parse, hợp với degrade path). Code chỉ strip + cắt theo `memory_summary_max_chars`.
- **Phải GIỮ** (ưu tiên từ trên xuống):
  1. Chủ đề user đang phân tích (doanh thu, tồn kho, công nợ, khách hàng...)
  2. Tham số đã chốt — khoảng thời gian, bộ lọc, kênh bán, chi nhánh... (để câu
     nối tiếp "còn tháng trước?" resolve được)
  3. Số liệu kết quả chính trong answer — vd "doanh thu tháng 5/2026 = 15.000.000đ"
     (phục vụ câu hỏi so sánh nối tiếp)
  4. Việc còn dang dở — yêu cầu chưa trả lời trọn vẹn, clarification còn treo
- **Phải BỎ**: chào hỏi/đưa đẩy; bảng dữ liệu chi tiết, danh sách rows dài (chỉ giữ
  con số tổng hợp + nhận xét chính); chi tiết kỹ thuật (tên cột, SQL, tên tool).
- **Quy tắc merge**: summary cũ được nén tiếp (thông tin càng cũ càng gọn), lượt mới
  tràn vào giữ chi tiết hơn; KHÔNG bịa thông tin không có trong input; đích ≤ ~1500
  ký tự (dưới bound `memory_summary_max_chars=2000`).
- File prompt kèm 1-2 few-shot ví dụ merge (summary cũ + lượt tràn → summary mới).

### 2. Inject vào Session Manager + query rewriting

- `run_session(ctx, ..., memory_context: ThreadMemory | None)` — orchestrator nhận context.
- `analyze()` thêm vào prompt SM 2 khối:
  - `[Tom tat hoi thoai cu]: {summary}` (nếu có)
  - `[Cac luot gan nhat]: {turns dạng JSON}` (nếu có)
- `Decision` thêm field `resolved_require: str | None` — SM viết lại câu hỏi nối tiếp
  thành câu tự-đủ-nghĩa (*"còn tháng trước?"* → *"doanh thu tháng 5/2026"*).
- `session_manager/skill.md`: thêm hướng dẫn — khi require tham chiếu hội thoại cũ,
  PHẢI điền `resolved_require`; nếu require đã tự đủ nghĩa thì để null.

### 3. Truyền ngữ cảnh xuống tool — 2 kênh

**Kênh 1 — resolved_require:** orchestrator dispatch bằng
`decision.resolved_require or state["raw_require"]` → mọi tool nhận câu hỏi đã resolve.

**Kênh 2 — memory_summary:** mọi tool đều nhận summary:

```
run_session(memory_context)
  → dispatch(..., memory_summary=summary)        # dispatcher: thêm vào payload
  → new_tool_state(..., memory_summary=...)      # state.py: thêm field ToolState
  → _PROMPT mỗi tool thêm khối:
      [Boi canh hoi thoai truoc]: {memory_summary}   (bỏ qua nếu None)
```

- Chỉ summary (ngắn) xuống tool — KHÔNG nhét 10 lượt verbatim (prompt tool không phình).
- SM là nơi duy nhất thấy 10 lượt đầy đủ.
- Cập nhật `skill.md` của `sql_execute`, `data_validator`, `answer_composer`:
  hướng dẫn dùng bối cảnh khi require tham chiếu hội thoại cũ.

### Phân công context

| Thành phần | Nhận gì |
|---|---|
| Session Manager | summary + 10 lượt verbatim + raw_require gốc |
| sql_execute / data_validator / answer_composer | resolved_require + summary |

### 4. Ghi memory (write path — `api/app.py`)

- Trong `stream()`: capture text từ event `answer`; sau event `done` →
  `append_turn(thread_id, raw_require, answer)`.
- Nếu `needs_compact` → **`asyncio.create_task(compact(...))`** fire-and-forget
  (log lỗi) — user không phải chờ thêm 1 LLM call sau khi đã nhận answer.
- **Lượt clarify (pause) KHÔNG ghi** — chỉ ghi khi phiên kết thúc có answer.
  Phiên resume ghi 1 lượt gộp: `raw_require` (đã append phần bổ sung từ user) → answer cuối.
- Phiên `aborted`/`error` không ghi.

### 5. Config (settings.py)

```python
memory_window_turns: int = 10
memory_summary_max_chars: int = 2000   # bound độ dài summary trong prompt
```

## Testing

- **Unit `ConversationMemory`:** window giữ đúng 10; compact gọi FakeLLM với summary cũ +
  lượt tràn, kết quả thay summary; LLM lỗi → degrade (giữ summary cũ, vẫn drop tràn);
  thread cô lập nhau; get_context không leak reference.
- **Orchestrator/SM:** prompt SM chứa khối summary + turns khi có memory_context;
  `resolved_require` được dùng khi dispatch (assert raw_require tool nhận = resolved).
- **Dispatcher/tool:** `memory_summary` chảy xuống ToolState; prompt tool chứa khối
  bối cảnh khi summary tồn tại, không chứa khi None.
- **E2E:** 2 request cùng thread (FakeLLM + stub executor) — câu 2 dạng nối tiếp,
  assert SM nhận lịch sử lượt 1; assert sau `done` memory có 1 lượt mới.

## Trade-offs chấp nhận

- Restart server mất memory (đã chốt in-memory).
- Memory phình theo số thread — chưa cap LRU (YAGNI vòng này; thêm sau nếu cần).
- Compact fire-and-forget: nếu process chết giữa chừng thì mất 1 lần compact —
  chấp nhận được vì lần compact kế tiếp sẽ gom tiếp.
