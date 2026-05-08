# PRD — App Layer Refactor — Task001
- Status: **Approved (Option B)**
- Approved date: 2026-05-08
- Date (draft): 2026-05-08
- Brief: Refactor `ai_python` tách layer/module (API, integrations, core, contracts/tools/agents-ready), tránh gom vào `main.py`, dễ mở rộng theo `../../Design_Agent/CHAT_AGENT_DESIGN.md` §1, §3, §5, §5.1.

## Assumptions (Phase 1 skipped — defaulted)
- Giữ FastAPI + SSE: `/health`, `/v1/chat/stream`; entry `uvicorn app.main:app ...` như README.
- MKP: OpenAI-compatible Chat Completions; stream delta text; không đổi hành vi nghiệp vụ.
- Chưa orchestrate Chat Agent đầy đủ; chỉ slot folder (agents/tools/mcp/contracts) theo design doc.
- Ưu tiên surgical refactor + import path nhất quán; không đổi API contract public; không sửa `backend/` / `frontend/`.
- **Phase 3 add:** Dev tooling cho quality gate: `pytest`, `pytest-asyncio`, `ruff`, `mypy` (dev-only; không bắt buộc vào runtime `requirements.txt` nếu repo chọn file tách `requirements-dev.txt` — nếu chỉ một file thì ghi rõ dev extras trong docs cài đặt).

## Phase 2 — Options (record, condensed)
**Owner choice: Option B — Agent-ready layered layout.**

- **Option A — Minimal modular FastAPI:** không chọn (ít layer, khó map agents/tools/MCP sớm).
- **Option B — Agent-ready layered layout:** **CHOSEN.** Cây mục tiêu: `app/main.py` + `app/api/routers/` + `app/contracts/` + `app/tools/` + `app/agents/chat_agent/` + `app/mcp/` + `app/core/` + `app/integrations/mkp/`.
- **Option C — Hexagonal:** không chọn (cost cao hơn nhu cầu MVP).

*(Chi tiết pros/cons Phase 2 lưu trong git history / transcript phiên trước.)*

---

## 4) PRD — Implementation (strict format)

### 4.1 Project Overview
- **Core goal:** Tái cấu trúc `ai_python` theo Option B để code dễ đọc, module có ranh giới rõ, sẵn sàng mở rộng state/intent/tools/MCP; giữ nguyên hành vi endpoint hiện tại.
- **Target users:** Team dev/maintainer `ai_python`; Spring Boot relay SSE (consumer); không có end-user UI trực tiếp trong service này.

### 4.2 Specifications
**Functional requirements**
- FR-1: `GET /health` trả `{"status":"ok"}` (JSON) như baseline.
- FR-2: `GET /v1/chat/stream?q=...` SSE: events `delta` (nội dung chunk), kết thúc `done` với payload `[DONE]`; lỗi stream qua event `error`; headers SSE (Cache-Control, Connection, X-Accel-Buffering) giữ tương đương.
- FR-3: `main.py` chỉ wiring (FastAPI app, include router); **không** `from .mkp_client import ...` — MKP nằm dưới `app/integrations/mkp/`; router ví dụ `from app.api.routers.chat import ...` (hoặc pattern tương đương package `app.api`).
- FR-4: Logic SSE format tách `app/core/sse.py` (pure helper); config env MKP tách `app/core/config.py`.
- FR-5: Skeleton (stub tối thiểu, import-safe): `contracts/`, `tools/stream_chat.py`, `agents/chat_agent/state.py` + `router.py`, `mcp/registry.py` — không yêu cầu đủ chức năng Chat Agent.

**Non-functional requirements (quantified)**
- NFR-1 **Latency:** p95 **TTFB** cho `/v1/chat/stream` (thời gian đến byte SSE đầu tiên sau request) ≤ **1.0 s** sau refactor — đo so với baseline trước refactor (cùng môi trường); ghi lại phương pháp đo (warm run, có/không cold start MKP).
- NFR-2 **Regression SSE:** Với cùng input `q`, chuỗi event SSE (thứ tự + loại event: `delta*`, `done`) trùng ý với baseline; `error` chỉ khi MKP/runtime lỗi như trước.
- NFR-3 **Tests:** Coverage (pytest) ≥ **70%** trên package `app/` (exclude skeleton chỉ pass-through nếu documented).
- NFR-4 **Lint/type:** `ruff check` và `mypy` **0 error** trên `app/` + `tests/`.
- NFR-5 **Imports:** Không còn import ad-hoc MKP trong `main.py`; public surface qua routers + integrations.

### 4.3 Tech stack
- **Frontend / UI:** N/A.
- **Backend / runtime (prod deps — `ai_python/requirements.txt`):** Python 3.x; **FastAPI**; **Uvicorn** [standard]; **OpenAI** SDK (MKP-compatible).
- **Database & storage:** N/A (service không đụng DB trong task này).
- **Dev-only (quality; allowed exception):** **pytest**, **pytest-asyncio**, **ruff**, **mypy** — cài qua `requirements-dev.txt` hoặc doc; không dùng làm runtime dependency.

### 4.4 Task breakdown & dependency graph
**Dependency (high level):** core/config + core/sse → integrations/mkp → tools/stream_chat → api/routers → main wiring → tests → eval smoke.

**Unit**
- [ ] **U1 — SSE helper tests**
  - Description: Unit test `_sse_event` / tương đương trong `app/core/sse.py` (multi-line data, event/done/error).
  - Input/Output: Input: helper function + sample strings; Output: pytest pass, stable string format.
  - Acceptance Criteria: Covers empty string, newline trong data, ít nhất 3 case.
- [ ] **U2 — Config loader tests**
  - Description: Test `app/core/config.py` đọc env `FPT_MKP_*` (required key, default base_url/model).
  - Input/Output: Mock `os.environ`; Output: raises khi thiếu key; defaults đúng.
  - Acceptance Criteria: Không gọi network; deterministic.
- [ ] **U3 — MKP streaming wrapper unit / contract**
  - Description: Test `integrations/mkp` wrapper với mock OpenAI client hoặc patch `chat.completions.create` — iterator yield content.
  - Input/Output: Fake stream chunks; Output: danh sách delta khớp.
  - Acceptance Criteria: Không cần real API key trong CI.

**Feature**
- [ ] **F1 — Layout Option B + move code**
  - Description: Tạo cây thư mục Option B; chuyển MKP từ `app/mkp_client.py` → `app/integrations/mkp/`; routers `health`, `chat`.
  - Input/Output: Source tree mới; Output: app importable.
  - Acceptance Criteria: `uvicorn app.main:app` khởi động không lỗi import.
- [ ] **F2 — Wire `main.py` + routers**
  - Description: `main.py` chỉ `FastAPI()` + `include_router`; chat import từ `app.api.routers.chat`.
  - Input/Output: Module graph sạch.
  - Acceptance Criteria: Đáp ứng FR-3, NFR-5.
- [ ] **F3 — `tools/stream_chat` + thin router**
  - Description: Router gọi tool layer stream; giữ query params `min_length=1`, `max_length=4000`.
  - Input/Output: HTTP SSE giống baseline.
  - Acceptance Criteria: FR-2, NFR-2.

**Eval**
- [ ] **E1 — Smoke API sau refactor**
  - Description: pytest hoặc script: `GET /health` 200 + body; `GET /v1/chat/stream` (optional marked integration / cần key) hoặc mock e2e.
  - Input/Output: Local server hoặc TestClient; Output: assertions.
  - Acceptance Criteria: Health luôn chạy CI; stream test chạy khi có key hoặc mock.
- [ ] **E2 — Baseline TTFB + regression note**
  - Description: Đo p95 TTFB trước/sau (manual hoặc script); ghi vào `ai_python/docs/` hoặc PR mô tả.
  - Input/Output: Số liệu; Output: NFR-1 chứng minh hoặc ghi rõ lệch nếu MKP ngoài tầm kiểm soát.
  - Acceptance Criteria: Có bảng/con số; NFR-2 checklist pass theo so sánh event.
- [ ] **E3 — Coverage + ruff + mypy gate**
  - Description: Cấu hình coverage threshold 70%; CI/local `ruff` + `mypy` zero.
  - Input/Output: Config files (.coveragerc, pyproject hoặc tương đương).
  - Acceptance Criteria: NFR-3, NFR-4.

---

**Design alignment (reference only):** `../../Design_Agent/CHAT_AGENT_DESIGN.md` §3 (state/intent), §4 (SSE event types future), §5 / §5.1 (tools, MCP).
