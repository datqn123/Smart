# SRS_AI_Task001_app-layer-refactor

**PRD:** [`../prd/PRD_app-layer-refactor.md`](../prd/PRD_app-layer-refactor.md) · **Task:** Task001 · **MCP_PHASE:** 0 · **Slug:** app-layer-refactor

## 1. Scope & capability

Refactor kiến trúc `ai_python` theo Option B (agent-ready layers): API routers, `core` (SSE + config), `integrations/mkp`, skeleton `contracts/` · `tools/` · `agents/chat_agent/` · `mcp/`. **Không** thêm Chat Agent đầy đủ, **không** endpoint/SSE/event mới, **không** MCP server thực thi trong task này. Hành vi nghiệp vụ MKP streaming giữ như baseline.

## 2. SSE event list (table)

| Event | Payload (SSE `data:` body) | Khi phát |
| :--- | :--- | :--- |
| `delta` | Chunk text UTF-8 (có thể nhiều dòng → nhiều dòng `data:`) | Mỗi phần tử stream MKP |
| `done` | Literal `[DONE]` | Sau khi hết iterator delta thành công |
| `error` | Message string (`str(exception)`) | Bất kỳ exception trong generator |

**Headers (giữ tương đương baseline):** `Content-Type: text/event-stream`; `Cache-Control: no-cache`; `Connection: keep-alive`; `X-Accel-Buffering: no`.

**Naming vs Design Doc §4:** Design §4 dùng tên event `token`; implementation **chuẩn của task** theo PRD FR-2 là **`delta`**. Không đổi trong refactor này (zero regression — NFR-2). Rename `delta`→`token` = thay đổi contract công khai → follow-up có điều phối Spring relay, không trong Task001.

## 3. State extension (ChatState delta)

**N/A** — chưa có `ChatState` trong slice; skeleton `agents/chat_agent/state.py` chỉ placeholder import-safe.

## 4. MCP tools used

**N/A — skeleton only.** `app/mcp/registry.py` (hoặc tương đương) tồn tại, không đăng ký tool thật; không MCP server mới.

## 5. HITL flow

**N/A — pure refactor, không có mutation flow.** Không `awaiting_approval` / `committed` trong slice.

## 6. Eval criteria (≥ 5 smoke prompts)

| # | HTTP | Expected SSE sequence (success path) |
| :--- | :--- | :--- |
| E1 | `GET /health` | N/A (JSON); **200**, body `{"status":"ok"}` |
| E2 | `GET /v1/chat/stream?q=Hello` | `delta` (≥1) → `done` data `[DONE]` |
| E3 | `GET /v1/chat/stream?q=Say+one+word` | Cùng pattern; ít nhất một `delta` trước `done` nếu MKP trả content |
| E4 | `GET /v1/chat/stream?q=Line1%0ALine2` | `delta`* → `done`; kiểm tra helper SSE xử lý multiline trong payload |
| E5 | `GET /v1/chat/stream?q=Repeat+this+exact+phrase` | Baseline regression: so sánh thứ tự và loại event với pre-refactor (NFR-2) |
| E6 | (Tùy chọn / mock CI) Missing `FPT_MKP_API_KEY` hoặc lỗi MKP | Một `error` event; không `done` |

Gắn PRD **E1–E3** (smoke, TTFB note, coverage+ruff+mypy). Đo **TTFB** (NFR-1) theo cùng phương pháp pre/post refactor.

## 7. Acceptance Criteria (G/W/T)

- **AC-1 (FR-1):** Given server chạy, When `GET /health`, Then 200 và JSON `{"status":"ok"}`.
- **AC-2 (FR-2, NFR-2):** Given `q` hợp lệ và MKP OK, When `GET /v1/chat/stream`, Then stream có `delta*` rồi `done` với `[DONE]`; cùng `q` so baseline event order/kinds (trừ biến thiên MKP đã ghi nhận).
- **AC-3 (FR-3, NFR-5):** Given codebase mới, When inspect `main.py`, Then không import MKP trực tiếp; routers + integrations đúng package.
- **AC-4 (FR-4):** Given module `app/core/sse.py` và `app/core/config.py`, When gọi helper SSE và load config, Then format SSE ổn định; env `FPT_MKP_*` như PRD.
- **AC-5 (FR-5):** Given cây Option B, When import app, Then skeleton tồn tại và import-safe (không yêu cầu logic agent đầy đủ).
- **AC-6 (NFR-1):** Given đo đạc đồng nhất, When so sánh p95 TTFB, Then ≤ 1.0s hoặc ghi rõ lệch/lý do ngoài phạm vi.
- **AC-7 (NFR-3):** Given pytest + coverage config, When chạy CI/local, Then coverage `app/` ≥ 70% (exclude skeleton pass-through nếu documented).
- **AC-8 (NFR-4):** Given `ruff` + `mypy`, When chạy trên `app/` + `tests/`, Then 0 error.

## 8. NFR (concretize từ PRD §4.2)

- **NFR-1:** p95 TTFB `/v1/chat/stream` ≤ **1.0 s** vs baseline cùng môi trường; ghi phương pháp (warm run, cold MKP).
- **NFR-2:** Cùng `q`: chuỗi loại event `delta*`, `done` khớp baseline; `error` chỉ khi lỗi runtime/MKP như trước.
- **NFR-3:** Coverage pytest ≥ **70%** trên `app/` (exclude hợp lệ được ghi).
- **NFR-4:** `ruff check` + `mypy`: **0** error trên `app/`, `tests/`.
- **NFR-5:** Không import MKP ad-hoc trong `main.py`; surface công khai qua router + integrations.

## 9. Open Questions

- **[default-OK]** Design §4 SSE dùng `token`; slice giữ **`delta`** theo PRD — assumption: Spring/consumer đang căn PRD/refactor baseline; rename thành **`token`** là task điều phối riêng, không blocker Task001.

## 10. Sample JSON request/response

**Health**

```json
{"status":"ok"}
```

**SSE `/v1/chat/stream` (fragments illustrative)**

```http
GET /v1/chat/stream?q=Hi HTTP/1.1
```

```
event: delta
data: He
event: delta
data: llo

event: done
data: [DONE]

```

**Error path**

```
event: error
data: Missing required environment variable: FPT_MKP_API_KEY


```

(Không có `done` sau `error` trong luồng exception hiện tại.)

## 11. Approved by / Date

**Approved** — AI_BA (auto-mode), 2026-05-08. Open Questions: 0× `[CRITICAL]`.
