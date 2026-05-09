# PLAN — MCP Server Smart ERP (multi-agent, intent routing) — v1

> **Mục đích**: Tài liệu kế hoạch **sau khi đã trao đổi** (RAG vs real-time, Agent Read + SQL từ schema RAG, single Write Agent).  
> **Phạm vi file**: chỉ mô tả kiến trúc, ranh giới, contract khái niệm và **todo triển khai** — **không** chứa mã nguồn.  
> **Ghi chú scope repo**: Luồng `/orchestrate` hiện tại giới hạn thay đổi mã trong `ai_python/`; phần tích hợp Spring/FE nên được tách **hợp đồng** trong plan và có thể là task ngoài `ai_python` hoặc handoff riêng — todo bên dưới đánh dấu rõ.

---

## 1) Những điểm plan **cần cập nhật** so với mô tả MCP “thuần điều phối dev agent”

| Chủ đề trao đổi | Cập nhật vào plan |
| :--- | :--- |
| **Đối tượng** | MCP phục vụ **User Smart ERP** (chat + UI), không phải chuỗi AI_PLANNER/BA/PM của repo dev. |
| **Agent Read + RAG** | RAG là **ngữ cảnh schema/nghiệp vụ** và có **độ trễ so với DB**; không dùng RAG làm **nguồn sự thật duy nhất** cho số live. |
| **Real time** | Số liệu “đúng lúc hỏi” → bắt buộc **đường đọc live** (`read.*` / API Spring / MCP read-only template), có thể kèm WebSocket/SSE sau. |
| **SQL do Agent Read sinh** | **Cho phép** draft SQL dựa trên metadata từ RAG, nhưng **bắt buộc** chuỗi: **catalog live (grounding)** → **validator** (SELECT-only, allowlist bảng/cột, LIMIT, timeout) → **thực thi read-only**; tránh SQL tự do thả vào DB. |
| **Agent UI (Form/Table)** | Pre-fill và validate cho **cập nhật** phải dùng **read live**, không pre-fill từ vector chunk. |
| **Single Write** | Chỉ **một** agent/toolchain gọi `write.*` / API ghi; có HITL + idempotency + audit. |
| **Intent** | MCP (hoặc subgraph) **`intent.analyze`** phân loại → gọi nhóm tool/agent phù hợp (RAG QA vs read vs viz vs transactional). |

---

## 2) Kiến trúc MCP server (đề xuất cố định v1)

- **Tên server (gợi ý)**: `smart-erp-ai` (một process MCP; tách read/write server là tùy chọn vận hành sau).
- **Nhóm tool (namespace)**:

| Nhóm | Vai trò | Ghi chú sau trao đổi |
| :--- | :--- | :--- |
| `intent.*` | Phân tích intent User → route + `risk_flags` / `hitl_required` | Không đọc DB trực tiếp. |
| `rag.*` | Trả lời theo tài liệu/index; citation | **Không** thay thế read live cho số. |
| `read.*` | Đọc **live** (API Spring hoặc executor SQL read-only sau validate) | Nguồn sự thật cho số, form, chart data. |
| `sql.*` (hoặc gộp trong `read.*`) | `propose_select` → validate → `execute_read` | Input schema hint từ RAG; **grounding** bằng catalog live bắt buộc. |
| `ui.*` | `build_form_spec` / `build_table_spec` JSON cho FE | Default từ `read.*`, không từ `rag.*` cho field số. |
| `viz.*` | `build_chart_spec` sau aggregate | Dữ liệu series từ `read.*`. |
| `write.*` | Chỉ mount cho **Write Executor** | `commit` cần token HITL + idempotency; backend transaction. |

- **Luồng “Read hybrid” (chuẩn sau trao đổi)**:

```text
User → intent.analyze
  → (nếu cần ngữ nghĩa/schema) rag.retrieve
  → (nếu cần số/rows live) read.* hoặc sql.propose_select → validate → execute_read
  → (nếu cập nhật) ui.* + HITL → write.commit (một cửa)
```

- **Tách plane dữ liệu** (bắt buộc ghi trong SRS/ADR sau này):

  - **Plane A — RAG**: mô tả bảng, quan hệ khái niệm, glossary, policy text.  
  - **Plane B — Live read**: snapshot/query đã kiểm soát.  
  - Agent “Read RAG” và “Read SQL/live” có thể là **hai capability** trong cùng product, do **intent** chọn; không gộp một nguồn.

---

## 3) Phi chức năng & an toàn (tối thiểu v1)

- RBAC (ví dụ Admin) forward từ session → Spring; MCP không giữ credential dài hạn trong prompt.
- SQL: chỉ SELECT; allowlist; max rows; timeout; parameterized literals; AST denylist.
- Write: optimistic concurrency / version row; audit log; không bypass UI confirmation.
- Minh bạch User: timestamp hoặc `data_as_of` trên câu trả lời có số.

---

## 4) Rủi ro còn mở (ghi để SRS/PM chốt, không chặn plan v1)

- Danh mục bảng/view được phép trong `sql.execute_read`.
- JSON Schema chính thức của `FormSpec` / `TableSpec` / `ChartSpec` trên FE.
- Task003 hiện chỉ read trong `ai_python` — mở rộng `write.*` có thể cần thay đổi `backend/` / `frontend/`: **handoff** ngoài scope auto-orchestrate nếu không được Owner mở rộng.

---

## 5) Todo triển khai (checklist — gọi `/orchestrate` theo từng cụm)

> Cách dùng: mỗi **cụm** có thể là một lần gọi `/orchestrate` với `Brief` tương ứng (hoặc gộp nếu Owner chấp nhận scope lớn).  
> Gợi ý `Task`: xếp tiếp sau `Task003` → **`Task004`** (hoặc để AI_PM cấp ID khi chạy orchestrate).

### Cụm A — Tài liệu & hợp đồng (ưu tiên trước code)

- [x] **A1** — PRD/SRS khái niệm: định nghĩa các vai Agent (Intent, Assistant, RAG Reader, UI Composer, Chart, Read-live/SQL constrained, Write-only), sơ đồ luồng hybrid RAG + live.
- [x] **A2** — Đặc tả tool MCP: bảng tên tool, input/output JSON Schema (stub), lỗi chuẩn (`FORBIDDEN`, `VALIDATION_FAILED`, `SCOPE_VIOLATION`).
- [x] **A3** — Bảng mapping `intent` → allowed tool groups (ma trận ACL agent ↔ tool).
- [x] **A4** — ADR: chọn một stack triển khai MCP trong `ai_python` (SDK), và quyết định gọi Spring qua HTTP vs MCP `db-readonly` hiện có — **một lựa chọn** + trade-off.

### Cụm B — Intent + RAG (chỉ `ai_python` nếu giữ nguyên quy tắc orchestrate)

- [x] **B1** — Stub `intent.analyze`: contract cố định + test đơn vị schema output.
- [x] **B2** — Wire `rag.retrieve` tới vector store / client hiện có (theo Task003 pattern nếu tái sử dụng).
- [ ] **B3** — Prompt/policy: RAG không trả lời “số chắc chắn” nếu không có `read.*` trong cùng turn (guardrail ứng dụng).

### Cụm C — Read live + SQL có ràng buộc

- [x] **C1** — Spec validator SQL (SELECT-only, allowlist, LIMIT) + test golden deny/allow.
- [x] **C2** — `catalog.snapshot` (live) — có thể là tool MCP gọi Spring hoặc mock trong `ai_python` cho đến khi có API.
- [x] **C3** — Pipeline `sql.propose_select` → merge identifiers với catalog → `sql.execute_read` (hoặc tên tương đương trong `read.*`).
- [x] **C4** — Observability: log intent, tool, latency; không log payload nhạy cảm.

### Cụm D — UI & Viz

- [x] **D1** — Contract `ui.build_form_spec` / `ui.build_table_spec` (fields, validation, default từ `read.*`).
- [x] **D2** — Contract `viz.build_chart_spec` (input series từ `read.*` aggregate).

### Cụm E — Write (có thể vượt `ai_python` — cần Owner cho phép mở scope)

- [x] **E1** — Thiết kế `write.commit`: HITL token, idempotency key, mapping sang API Spring transaction.
- [ ] **E2** — Đảm bảo chỉ một execution path gọi write (CI lint hoặc allowlist tool theo agent id).

### Cụm F — Kiểm thử & vận hành

- [x] **F1** — Bộ eval intent + red-team SQL injection / query lớn.
- [x] **F2** — Runbook: cấu hình MCP trong Cursor, biến môi trường, healthcheck.

---

## 6) Gợi ý lệnh `/orchestrate` (copy khi triển khai)

**Lần 1 — Khóa tài liệu & contract (Cụm A):**

```text
/orchestrate Task=004 Brief="Smart ERP MCP server v1: cập nhật SRS/ADR + tool contract (intent, rag, read/sql constrained, ui, viz, write ACL) theo PLAN_Smart_ERP_MCP_server_v1.md — hybrid RAG + live read, single write path. Chỉ artifact dưới ai_python/docs/ và TASKS; tham chiếu plan path ai_python/docs/plan/PLAN_Smart_ERP_MCP_server_v1.md"
```

**Lần 2 — Intent + RAG stub (Cụm B):** điều chỉnh Brief sau khi có SRS/ADR từ lần 1.

**Lần 3 — Read/SQL validator (Cụm C):** tách Brief nếu cần giảm scope mỗi sprint.

> Nếu PRD đã có sẵn từ planner trước: thêm `SkipPlanner=true` và truyền path PRD tương ứng theo quy ước driver trong `.cursor/commands/orchestrate.md`.

---

## 7) Tổng kết

- Plan MCP đã **cập nhật** theo trao đổi: Read **hybrid** (RAG + live), SQL **có grounding/validation**, real time qua **read live**, Write **một cửa**.
- File này đồng thời là **todo list** triển khai (mục 5–6).
- **Trạng thái triển khai (2026-05-09)**: cụm A/C/D/F và phần lớn B/E đã có mã + tài liệu trong `ai_python/` (Task004); còn **B3** (guardrail “số chắc chắn” xuyên turn) và **E2** (CI enforce single write path) — xem `TASKS/Task004.md`.
