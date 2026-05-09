# BRIDGE — Task005 — db_rag_agent_context

- **Mode**: verify  
- **Date**: 2026-05-09  
- **Path**: Task005 corpus batch — MCP `db-readonly` (`sql.describe`, `sql.query_readonly`) + SRS §2/§10 SSE **REFERENCE_ONLY** (no runtime UI stream)  
- **Inputs**: `SRS_PATH` = `ai_python/docs/srs/SRS_AI_Task005_db_rag_agent_context.md` · `ADR_PATH` = `ai_python/docs/adr/ADR-003-db_rag_agent_context.md` · `BRANCH` = `feature/ai-task005` · `OUT_PATH` = `ai_python/docs/api/bridge/BRIDGE_AI_Task005_db_rag_agent_context.md`

## Bridge table

| Item | SRS | ai_python | Spring relay | FE | MCP doc | Notes / drift |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SSE `token` | §2, §10.1 — **Không** phát trong Task005 v1 | **n/a** — slice không mở SSE; không có emitter Task005 | **n/a** — batch corpus không qua `/api/v1/ai/chat/stream` | **n/a** — không UI Task005 | **n/a** | Vocabulary chuẩn cho Agent sau; MATCH SRS. |
| SSE `tool_call` | §2, §10.1 — **Không** | **n/a** | **n/a** | **n/a** | **n/a** | MATCH. |
| SSE `tool_result` | §2, §10.1 — **Không** | **n/a** | **n/a** | **n/a** | **n/a** | MATCH. |
| SSE `ui` | §2, §10.1 — **Không** | **n/a** | **n/a** | **n/a** | **n/a** | MATCH. |
| SSE `awaiting_approval` | §2, §10.1 — **Không** | **n/a** | **n/a** | **n/a** | **n/a** | MATCH. |
| SSE `approval_resolved` | §2, §10.1 — **Không** | **n/a** | **n/a** | **n/a** | **n/a** | MATCH. |
| SSE `committed` | §2, §10.1 — **Không** | **n/a** | **n/a** | **n/a** | **n/a** | MATCH. |
| SSE `error` (stream) | §2, §10.1 — **Không (SSE)**; lỗi → exit code + log | **n/a** (Task005 job) | **n/a** | **n/a** | **n/a** | Relay chat generic có `error` (`AiChatRelayController.java:97`) — **ngoài** phạm vi Task005. |
| SSE `done` | §2, §10.1 — **Không** | **n/a** (Task005 job) | **n/a** | **n/a** | **n/a** | Relay đóng stream khi `event` = `done` (`AiChatRelayController.java:66-68`) — luồng chat, không corpus. |
| MCP `sql.describe` | §4.1 | `app/contracts/task005.py:54-75` · `app/mcp/db_readonly_port.py:35-36` · `app/tools/task005_describe.py:50-64` | **n/a** (MCP, không SSE) | **n/a** | `Design_Agent/mcp/DB_READONLY_TOOLS.md` § Tool 2 (`sql.describe`) | I/O khớp doc (object_name, columns+nullable, summary, correlation_id). MATCH. |
| MCP `sql.query_readonly` | §4.2 | `app/contracts/task005.py:87-114` · `app/mcp/db_readonly_port.py:38-41` · `app/tools/task005_smoke.py:47-65` | **n/a** | **n/a** | `DB_READONLY_TOOLS.md` § Tool 1 (`sql.query_readonly`) | template_id+params; columns, rows, row_count, summary, correlation_id. Cap `row_count` ≤ 50 trong contract. MATCH. |
| MCP `sql.query_readonly_raw` | §1 explicit non-capability | **n/a** — không implement trong Task005 | **n/a** | **n/a** | `DB_READONLY_TOOLS.md` § Optional | Cả SRS và code đều không bật raw path. MATCH. |

## Verdict

- **ai_python ↔ SRS**: **MATCH** (contracts + describe/smoke loops + job context theo SRS §3–§4; không SSE runtime cho slice).  
- **ai_python ↔ Spring**: **MATCH** (không yêu cầu relay Spring cho Task005 v1; cột relay **n/a** theo scope).  
- **ai_python ↔ FE**: **MATCH** (không UI; **n/a**).  
- **ai_python ↔ MCP doc**: **MATCH** (hai tool + error codes DB trong doc khớp pydantic/Task005).

## Drift items

- **[Minor] BR-001** — Luồng chat tồn tại `app/main.py:26-34` emit SSE `delta` / `done` (payload string `[DONE]`) thay vì từ vựng Design §4 `token` / JSON `done` trong SRS §10 REFERENCE — **ngoài Task005**; không chặn G-AI-BRIDGE Task005. **Owner**: `backend/AGENTS/API_BRIDGE` + `frontend/AGENTS/...` **chỉ khi** scope mở rộng đồng bộ Chat SSE vocabulary (handoff tùy roadmap).

## Handoffs

- **backend bridge**: Khi Task005+ mở rộng qua relay — [`backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md`](../../../../backend/AGENTS/API_BRIDGE_AGENT_INSTRUCTIONS.md) · Path: *chưa áp dụng* (batch không đi Spring).  
- **fe bridge**: [`frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md`](../../../../frontend/AGENTS/docs/FE_API_CONNECTION_GUIDE.md) — *chưa áp dụng* (không runtime SSE/UI Task005).

---

## Gate G-AI-BRIDGE (§5)

| Check | Result |
| :--- | :--- |
| Bridge file tại `OUT_PATH` | **Yes** |
| Bảng đủ cột, không `TBD` | **Yes** |
| `ai_python ↔ SRS` = MATCH | **Yes** |
| `ai_python ↔ MCP doc` = MATCH | **Yes** |
| Spring/FE | **n/a** slice; không DRIFT bắt buộc handoff cho Task005 |

**Gate exit**: **PASS**  
**Drift severity (Task005 scope)**: **Minor** (chỉ BR-001 informational, không Block/Major đối với MCP factory + corpus pipeline).

**Loop scope**: Không cần vòng `wire-py` — không có lệch Block/Major giữa `ai_python` và SRS/MCP doc cho Task005.
