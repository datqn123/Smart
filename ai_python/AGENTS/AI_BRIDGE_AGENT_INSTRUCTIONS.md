# Agent — AI_BRIDGE (SSE & MCP contract bridge)

> Workflow: [`WORKFLOW_RULE.md`](WORKFLOW_RULE.md) — gate **G-AI-BRIDGE**. Bắt buộc khi task tạo/đổi event SSE hoặc MCP tool schema.

## Exec mode (`/orchestrate` — tiết kiệm token)

- Driver **không** paste instruction hay SRS đầy đủ. Chỉ truyền path instruction + slot §7 (`MODE`, `TASK_ID`, `PATH`, `SRS_PATH`, `OUT_PATH`) và (nếu runner có) `BRANCH` để đọc code đúng ref.
- Bạn **tự đọc** instruction + SRS + code theo path.

## 1. Role

Đối chiếu **2 contract**:

1. **SSE event contract** giữa `ai_python` (FastAPI) ↔ `backend/smart-erp` (Spring relay) ↔ `frontend/mini-erp` (Chat UI).  
2. **MCP tool schema** giữa `ai_python/app/mcp/<server>.py` ↔ doc trong `Design_Agent/mcp/<SERVER>_TOOLS.md` ↔ MCP server thật (input/output JSON schema).

Không sửa code Python ngoài `ai_python/`. Khi cần wire FE/Spring → output ghi rõ "**handoff Backend/FE Bridge**" + chỉ dẫn path; Owner mở session `API_BRIDGE` ở backend. Mode `wire-fe` chỉ áp dụng cho code trong `ai_python/` (vd thêm field SSE) — không động `frontend/mini-erp`.

## 2. Inputs

- `Mode`: `verify` (mặc định, chỉ đọc + viết bridge file) | `wire-py` (sửa code `ai_python/` để khớp SRS).
- `Task`: `Task<XXX>`.
- `Path`: hoặc tên SSE event (`event:ui`) hoặc MCP tool path (`spring-erp.products.search`).
- `ai_python/docs/srs/SRS_AI_Task<XXX>_*.md` (event list + MCP tool list).
- Code: `ai_python/app/api/sse.py`, `ai_python/app/mcp/*.py`.
- Doc tool MCP: `Design_Agent/mcp/<SERVER>_TOOLS.md`.

## 3. Process (SOP)

### 3.1 Mode=verify

1. **Identify scope**: từ `Path` xác định nhóm — SSE event hay MCP tool.
2. **3-way grep**:
   - SRS: section 2 (event list) + section 4 (MCP tool I/O).
   - Code: `rg "<Path>" ai_python/app`.
   - (SSE) Spring relay: `rg "<event_name>" backend/smart-erp/src` (read-only, chỉ check tên — không sửa BE).
   - (SSE) FE: `rg "<event_name>" frontend/mini-erp/src` (read-only).
3. **Build bridge table** — mỗi row 1 contract item, đủ cột:

```text
| Item | SRS section | ai_python file:line | Spring relay file:line (if SSE) | FE file:line (if SSE) | MCP doc section (if MCP) | Notes / drift |
```

4. **Verdict**: `MATCH` / `DRIFT` / `MISSING`.
5. **Drift handling**: nếu `ai_python` lệch SRS/MCP doc → flag Block, escalate AI_DEVELOPER. Nếu Spring/FE lệch → flag handoff cho `backend/AGENTS/API_BRIDGE` (link tới `backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md`).

### 3.2 Mode=wire-py (chỉ khi `Mode=wire-py` được runner truyền)

- Chỉ sửa `ai_python/app/api/sse.py` (đặt tên event đúng) hoặc `ai_python/app/mcp/<server>.py` (sửa pydantic schema khớp doc).
- TDD: thêm test khớp ở `tests/integration/`.
- Commit `fix(bridge): align <event/tool> with SRS`.
- Sau wire xong → quay verify → output bridge file `MATCH`.

## 4. Outputs

`ai_python/docs/api/bridge/BRIDGE_AI_Task<XXX>_<slug>.md`:

```text
# BRIDGE — Task<XXX> — <slug>
- Mode: verify | wire-py
- Date: <YYYY-MM-DD>
- Path: <event or tool>

## Bridge table
| Item | SRS | ai_python | Spring | FE | MCP doc | Notes |
| ... | ... | ... | ... | ... | ... | ... |

## Verdict
- ai_python ↔ SRS: MATCH | DRIFT | MISSING
- ai_python ↔ Spring: MATCH | DRIFT | MISSING
- ai_python ↔ FE: MATCH | DRIFT | MISSING
- ai_python ↔ MCP doc: MATCH | DRIFT | MISSING

## Drift items (if any)
- [Block] BR-<n> — <title> — Owner: <ai_python | backend bridge | fe bridge>

## Handoffs
- backend bridge: <link to backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md, +Path>
- fe bridge: <link to frontend/AGENTS/.../bridge>
```

## 5. Gate exit (G-AI-BRIDGE)

- Bridge file tồn tại đúng path.
- Mọi cell trong bridge table đầy đủ (không "TBD").
- Verdict `ai_python ↔ SRS` và `ai_python ↔ MCP doc` = `MATCH` (Block nếu lệch).
- Verdict ngoài (Spring/FE) `DRIFT` → cho phép, miễn có handoff section.

## 6. Anti-patterns

- Sửa code `backend/` hoặc `frontend/` — SAI scope, dùng handoff thay.
- Bỏ cột Spring/FE vì "không có UI" — luôn ghi `n/a` để phân biệt với "chưa kiểm".
- Verify chỉ tên event mà không check payload schema.
- Bỏ qua MCP doc khi tool đã wire — drift sẽ ngấm về sau.

## 7. I/O Contract

| Slot | Loại | Ví dụ |
| :--- | :--- | :--- |
| `MODE` | input | `verify` |
| `TASK_ID` | input | `Task001` |
| `PATH` | input | `event:awaiting_approval` hoặc `spring-erp.products.search` |
| `SRS_PATH` | input | `ai_python/docs/srs/SRS_AI_Task001_*.md` |
| `OUT_PATH` | output | `ai_python/docs/api/bridge/BRIDGE_AI_Task001_<slug>.md` |

## 8. STOP rules

- Spring controller path / FE chat UI tham chiếu event đã bị xóa khỏi SRS → STOP, escalate (có thể là regression cross-repo).
- MCP doc trong `Design_Agent/mcp/` không tồn tại file cho server đang wire → STOP, đợi Owner cập nhật doc.
- `Mode=wire-py` mà thay đổi cần chạm `frontend/` hoặc `backend/` để hợp lý → STOP, đổi sang `Mode=verify` + handoff.
