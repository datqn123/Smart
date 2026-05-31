# PRD (FINAL) — Task 3: Triển khai Agents v1 trên LangGraph + Gemma 4

**Track:** `ai_python` only  
**Slug:** `langgraph-gemma4-task3-agents`  
**Trạng thái:** **FINAL** — **2026-05-10**  
**Owner choice:** **`pick optimal` → Option C** (Planner chốt). **Lý do:** đồng nhất pattern port Task 1 (`LlmClient`) + Task 2 (`SqlExecutor`); structured-dict feedback cho retry `gen_sql` sạch hơn string concat; không phụ thuộc DB / CLI scanner / `python_ro` trong v1 — ship Agent logic trước, nối infra sau.

**Tham chiếu PRD trước (FINAL):**

- `docs/ai-python/prd/PRD_langgraph-gemma4-task1.md` — Option B: port `LlmClient` + registry role. **Mọi node Agent gọi qua `get_llm_client(role)`**, không tạo `ChatOpenAI` thủ công.
- `docs/ai-python/prd/PRD_langgraph-gemma4-task2.md` — Skeleton LangGraph + subgraph SQL + retry cap 3 + port `SqlExecutor` (Option C) + checkpointer factory. **Task 3 build tiếp lên skeleton, KHÔNG sửa topology graph.**

**Tham chiếu DESIGN:**

- `docs/ai-python/tasks/DESIGN/TASK_AGENTS_V1_DESIGN.md`
- `docs/ai-python/tasks/DESIGN/TASK_LANGGRAPH_GEMMA4_TRIEN_KHAI.md` (§6 `TASK-AG-*`, `SUM-*`, `REG-*`, `CTX-*`)

**Codebase scaffold (Task 1 + Task 2):** `ai_python/app/llm/*`, `ai_python/app/graph/{state,main_graph,sql_subgraph,registry,retry,checkpointing,validate_sql,sql_executor,logging_policy,correlation,feedback,deps,constants,streaming}.py`, `ai_python/app/graph/nodes/{intent,chat_normal,sql_pipeline,summarize}.py` (stub → thay implementation), `ai_python/tests/` (fake LLM).

---

## 4.1. Project Overview

**Core goal:** Triển khai logic nội bộ các Agent node v1 trên skeleton Task 2: `intent`, `chat_normal`, `gen_sql`, `sql_review`, nâng cấp `validate_sql` deterministic, wiring `execute_sql` chỉ qua `SqlExecutor` **stub**, `validate_result`, `summarize_answer`; **registry hardening**; **DBM artifact loader** qua **`SchemaLoader` Protocol** + implementation `FileSchemaLoader`. Giữ nguyên topology graph Task 2 (`gen_sql → sql_review → validate_sql → execute_sql → validate_result`, retry về `gen_sql`, `MAX_SQL_ATTEMPTS=3`), port `SqlExecutor`, port `LlmClient`/registry — không động kiến trúc graph/checkpointer.

**Target users / actors:**

- **Developer / code agents:** triển khai nodes, loader, tests.
- **Downstream Task 3/API:** FastAPI invoke/stream (PRD riêng).
- **Downstream Task 4/QA:** E2E, integration (PRD riêng).

**Goals**

- Thay stub nodes bằng hành vi Agent v1 theo DESIGN + bundle đã chốt (Trục α=β=γ=**C**).
- `validation_feedback` dạng **structured dict** bucket: `{ intent_review, policy, exec, result, attempts, extras? }`.
- Schema snapshot chỉ qua **file YAML** + `SchemaLoader.load(schema_version)` — không mở DB mỗi turn.

**Non-goals**

- Sửa cạnh/thứ tự node LangGraph, đổi `MAX_SQL_ATTEMPTS`, refactor checkpointer distributed.
- FastAPI route hoàn chỉnh, QA E2E đầy đủ, multimodal LM-05.
- CLI quét `information_schema`, implementation `python_ro` / `http_spring` cho `SqlExecutor`.

---

## 4.2. Specifications

### Functional requirements — theo nhóm Agent

**AG-01 — `intent`**

- Prompt phân loại VI/EN; output structured Pydantic **`IntentLabel`** (đồng bộ enum registry): `system_data_query` | `general_chat` (tận dụng Task 1 LM-04 + schema trong `app/llm/schemas.py` hoặc tương đương).
- **D1 — Fallback ambiguous:** → `general_chat` (an toàn, không gọi DB nhầm).
- Không nhét full schema bảng vào prompt intent.

**AG-02 — `chat_normal`**

- Gọi **`get_llm_client("chat")`** (hoặc role đã đăng ký trong registry — DEV đồng bộ tên role với `ai_python/app/llm/registry.py`).
- Không bind tool DB v1; append assistant message vào `messages`; set `final_answer`.
- System prompt: không leak schema nội bộ.

**AG-03 — `gen_sql`**

- Load artifact schema qua **`SchemaLoader.load(schema_version)`** (Trục α = C): implementation v1 **`FileSchemaLoader`** đọc YAML dưới `ai_python/app/data/schema/<schema_version>.yaml` (path cuối DEV chốt).
- Prompt nhận **structured-dict feedback** (Trục β = C): `{ intent_review: list[str], policy: list[str], exec: list[str], result: list[str], attempts: int, extras?: dict }` — lồng từng bucket vào prompt retry.
- Ép **một** câu `SELECT` statement; không batch SQL.
- **Tăng `sql_attempt_count` trước khi gọi LLM** (đồng bộ Task 2 LG-09).

**AG-04 — `sql_review`**

- Structured output **`{ ok: bool, issues: list[str] }`** qua **`get_llm_client("sql_review")`** + Task 1 LM-04 fallback JSON.
- Khi `ok=False`: append issues vào bucket **`intent_review`** hoặc **`policy`** tùy bản chất lỗi (semantic/schema → `intent_review`; keyword/policy overlap → `policy`) — DEV ghi quy ước một dòng trong code/SRS.

**AG-05 — `validate_sql` (deterministic, upgrade `app/graph/validate_sql.py`)**

- SELECT-only; **allowlist** bảng/cột từ artifact DBM (reuse AGENT-DBM); **LIMIT** bắt buộc hoặc inject an toàn; deny DDL/DML keywords.
- Parser DEV chốt — **gợi ý:** `sqlparse`.
- Map lỗi → bucket **`policy`** của `validation_feedback`.
- Không gọi LLM.

**AG-06 — `execute_sql` wiring**

- Gọi port **`SqlExecutor`** với mode **`stub`** (Trục γ = C). **`python_ro`** và **`http_spring`** — **ngoài scope** Task 3 PRD này.
- Timeout / log theo Task 2 LG-14; map lỗi runtime → bucket **`exec`**.

**AG-07 — `validate_result`**

- Ngưỡng **`max_rows`** / **`max_bytes`** (giá trị số trong Settings hoặc constants — DEV chốt).
- **D4 — Empty result:** **không** retry vòng SQL; để **`summarize_answer`** giải thích "không có dữ liệu phù hợp".

**SUM-01..02 — `summarize_answer`**

- Prompt tóm tắt từ `query_result` + câu hỏi user; **không bịa số** ngoài rows.
- **D6 — Locale** mặc định **`vi-VN`** (field `locale` từ state/config nếu có).
- **SUM-02 / empty:** khi không có row hoặc toàn null — câu trả lời cố định kiểu "Không có dữ liệu phù hợp với yêu cầu" (không retry SQL).

**REG-01..03 — Registry hardening**

- **D5 — Unknown intent:** route → **`general_chat`** (đồng bộ Task 2 assumption).
- Thêm **một trang** `docs/ai-python/intent_registry_howto.md`: checklist cách đăng ký intent mới + đồng bộ enum/Pydantic `IntentLabel`.
- `INTENT_HANDLERS` / factory không yêu cầu sửa lõi `route_by_intent` cồng kềnh — chỉ đăng ký.

**AGENT-DBM-01..04 — Artifact + loader**

- Format YAML có **`schema_version`** + danh sách bảng/cột được phép + FK gợi ý (theo DESIGN).
- **`SchemaLoader`** Protocol + **`FileSchemaLoader`** impl.
- Allowlist reuse cho AG-05 (một nguồn truth).
- **Không** mở connection DB runtime mỗi turn — chỉ đọc file.

**CTX-01..02 — Context (cite Task 2, không redefine)**

- **Tham chiếu:** Task 2 PRD §Assumptions #4 + LG-03.4 — `correlation_id`, `tenant_id`, `schema_version`, `thread_id` trong **state** và/hoặc **`config["configurable"]`**.
- Bảng vị trí đọc field — xem mục checklist **CTX cite** §4.4 (bảng canonical).

### Non-functional requirements (NFRs) — định lượng

| ID | Requirement | Mục tiêu / ngưỡng | Ghi chú |
| :-- | :-- | :-- | :-- |
| NFR-PERF-01 | Latency node `intent` (mock LLM) | p95 **< 50 ms** | Đo qua test fake LLM |
| NFR-PERF-02 | Latency `validate_sql` deterministic | p95 **< 20 ms** | Parser local, không LLM |
| NFR-PERF-03 | Latency `validate_result` | p95 **< 5 ms** | Pure Python checks |
| NFR-REL-01 | Retry cap `gen_sql` | Tối đa **3** (đồng bộ Task 2) | Không vượt `MAX_SQL_ATTEMPTS` |
| NFR-REL-02 | Empty result không retry SQL | **0** retry vòng SQL khi empty (D4) | Chuyển summarize |
| NFR-SEC-01 | SQL không bypass `validate_sql` | **100%** (khớp Task 2 NFR-SEC-01) | Test cạnh graph |
| NFR-SEC-02 | LLM không tạo `ChatOpenAI` rải rác | **100%** qua `get_llm_client(role)` | Grep/lint hoặc test |
| NFR-OBS-01 | Mỗi Agent log có `correlation_id` khi inject | **100%** | Khớp Task 2 NFR-OBS-01 |
| NFR-TEST-01 | Coverage `app/graph/nodes/*` (phần mới/touch) | **≥ 85%** line (mục tiêu DEV; CR có thể nới nhẹ) | Task 4 mở rộng E2E |
| NFR-TEST-02 | Mỗi Agent ≥ 1 unit test fake LLM | **100%** (8 nhánh: intent, chat, gen_sql, sql_review, validate_sql, execute_stub, validate_result, summarize) | Pattern `tests/fake_llm` |

---

## 4.3. Tech stack & approach

| Lớp | Lựa chọn |
| :-- | :-- |
| **Runtime** | Python 3.11+ (khuyến nghị 3.12) |
| **Orchestration** | LangGraph — **tái dùng skeleton Task 2**, không sửa topology graph |
| **LLM** | `LlmClient` qua `get_llm_client(role)` (Task 1); structured + JSON fallback (Task 1 LM-04) |
| **Schema artifact** | YAML dưới `ai_python/app/data/schema/<schema_version>.yaml` (hoặc path tương đương — DEV chốt); **`SchemaLoader` Protocol** — gợi ý module `ai_python/app/graph/dbmeta.py` (DEV chốt path file cuối) |
| **SQL deterministic** | `sqlparse` (gợi ý) — DEV có thể đổi nếu có lý do kỹ thuật |
| **Execute** | `SqlExecutor` mode **`stub`** only (v1 PRD này) |
| **Test** | pytest + fake LLM Task 1 |

---

## 4.4. Task breakdown & dependency graph

Mỗi mục checklist `[ ]`; Acceptance Criteria kiểm tra được.

- [ ] **AG-01 intent — prompt + structured + fallback**
  - **Description:** Prompt VI/EN; structured `IntentLabel`; ambiguous → `general_chat` (D1); không nhét schema DB vào prompt.
  - **Input/Output:** Input: `messages`, optional `locale`. Output: `state["intent"]` literal khớp registry.
  - **Acceptance Criteria:** Unit test với fake LLM; enum đồng bộ registry keys; không gọi DB.

- [ ] **AG-02 chat_normal**
  - **Description:** `get_llm_client("chat")`; không tool DB; append assistant; `final_answer`.
  - **Input/Output:** Input: `messages`. Output: `final_answer`, `messages` updated.
  - **Acceptance Criteria:** Fake LLM test; module không import execute/sql tools.

- [ ] **AG-03 gen_sql — SchemaLoader + bucket feedback + đếm attempt**
  - **Description:** `SchemaLoader.load(schema_version)`; prompt có structured-dict feedback buckets + `attempts`; một SELECT; **`sql_attempt_count++` trước LLM**.
  - **Input/Output:** Input: user text, `schema_version`, `validation_feedback`, `sql_attempt_count`. Output: `generated_sql`.
  - **Acceptance Criteria:** Test với fixture YAML + fake LLM; đếm attempt đúng quy ước Task 2.

- [ ] **AG-04 sql_review — structured `{ok, issues[]}` + bucket fail**
  - **Description:** `get_llm_client("sql_review")`; parse structured/fallback; fail → append `intent_review`/`policy`.
  - **Input/Output:** Input: `generated_sql`, schema snippet. Output: cập nhật feedback buckets.
  - **Acceptance Criteria:** Fake LLM trả ok/issue; test route fail không execute.

- [ ] **AG-05 validate_sql upgrade — SELECT-only / allowlist / LIMIT / deny DDL-DML**
  - **Description:** Nâng `app/graph/validate_sql.py`; allowlist từ DBM artifact; LIMIT inject/deny; map lỗi → `policy`.
  - **Input/Output:** Input: `generated_sql`, allowlist config. Output: pass/fail + feedback.
  - **Acceptance Criteria:** Test parser với SQL hợp lệ/không hợp lệ; NFR-PERF-02.

- [ ] **AG-06 execute_sql wiring — SqlExecutor stub + log policy**
  - **Description:** Gọi `SqlExecutor` mode **stub**; không implement `python_ro`/`http_spring` trong Task 3; correlation + mask theo Task 2.
  - **Input/Output:** Input: SQL đã validate. Output: `query_result` hoặc lỗi có cấu trúc → bucket `exec`.
  - **Acceptance Criteria:** Test stub trả row cố định; không bypass validate_sql.

- [ ] **AG-07 validate_result — ngưỡng + empty không retry**
  - **Description:** `max_rows` / `max_bytes`; empty → không retry SQL (D4).
  - **Input/Output:** Input: `query_result`. Output: pass/fail + feedback bucket `result`.
  - **Acceptance Criteria:** Test empty không tăng `sql_attempt_count` / không route `gen_sql`.

- [ ] **SUM-01 summarize_answer — prompt locale + không bịa số**
  - **Description:** Tóm tắt từ rows + câu hỏi; locale `vi-VN`; giới hạn độ dài.
  - **Input/Output:** Input: `query_result`, question, `locale`. Output: `final_answer`.
  - **Acceptance Criteria:** Test assertion không hallucinate số không có trong rows (fake LLM hoặc snapshot).

- [ ] **SUM-02 empty handling — "không có dữ liệu phù hợp"**
  - **Description:** Khi empty/null rows → câu trả lời cố định/gợi ý người dùng đổi câu hỏi; không retry SQL.
  - **Input/Output:** Input: empty `query_result`. Output: `final_answer` text an toàn.
  - **Acceptance Criteria:** Test dedicated empty path; NFR-REL-02.

- [ ] **REG-01..03 registry hardening — unknown → general_chat + howto**
  - **Description:** Unknown intent → `general_chat` (D5); file `docs/ai-python/intent_registry_howto.md` checklist thêm intent.
  - **Input/Output:** Input: intent string. Output: handler đúng runnable.
  - **Acceptance Criteria:** Test unknown intent đi nhánh chat; doc tồn tại và đủ bước.

- [ ] **DBM-01 schema artifact format — YAML + schema_version**
  - **Description:** Định dạng YAML (bảng/cột/FK/version) khớp DESIGN AGENT-DBM.
  - **Input/Output:** File static trong repo; ít nhất một fixture `schema_version` cho test.
  - **Acceptance Criteria:** Loader đọc được; version string khớp path hoặc field trong file.

- [ ] **DBM-02 SchemaLoader Protocol + FileSchemaLoader**
  - **Description:** Protocol `load(schema_version) -> SchemaArtifact`; impl đọc file từ `app/data/schema/`.
  - **Input/Output:** Input: `schema_version`. Output: object cho prompt gen_sql + allowlist.
  - **Acceptance Criteria:** Unit test load/happy path missing file → lỗi có kiểm soát.

- [ ] **DBM-03 allowlist reuse cho AG-05**
  - **Description:** Một nguồn allowlist từ artifact cho `validate_sql` và gợi ý `gen_sql`.
  - **Input/Output:** Shared helper hoặc field trên `SchemaArtifact`.
  - **Acceptance Criteria:** Test: cột không trong allowlist → validate_sql fail.

- [ ] **CTX cite — bảng vị trí đọc field state vs configurable**

| Field | Khuyến nghị đọc | Ghi chú |
| :-- | :-- | :-- |
| `correlation_id` | `config["configurable"]` (ưu tiên), fallback state | Log context mọi node (Task 2 LG-13/14) |
| `tenant_id` | `config["configurable"]` hoặc state metadata | Filter policy sau này; v1 có thể chỉ log/trace |
| `schema_version` | `state` hoặc `configurable` — **một nơi ưu tiên** (DEV chốt) | Truyền vào `SchemaLoader.load` |
| `thread_id` | `config["configurable"]` | Checkpointer Task 2 |
| `locale` | `state` hoặc `configurable` | SUM / intent |

  - **Acceptance Criteria:** Một bảng này được nhắc trong SRS/ADR hoặc comment module graph entry; không định nghĩa lại Task 2.

- [ ] **TEST-01 unit test mỗi Agent với fake LLM**
  - **Description:** Cover 8 nhánh NFR-TEST-02.
  - **Input/Output:** pytest + `tests/fake_llm`.
  - **Acceptance Criteria:** NFR-TEST-02 đạt.

- [ ] **TEST-02 retry test (3 lần đúng)**
  - **Description:** Fail liên tục tại `validate_sql` hoặc `sql_review` → đúng 3 lần vào `gen_sql`; lần 4 → `fail_max_attempts`.
  - **Input/Output:** Mock fail deterministic.
  - **Acceptance Criteria:** Khớp Task 2 LG-09/LG-11.

- [ ] **TEST-03 empty result test**
  - **Description:** `query_result` rỗng → summarize empty message; không retry SQL.
  - **Input/Output:** Stub executor trả `[]`.
  - **Acceptance Criteria:** NFR-REL-02.

- [ ] **TEST-04 unknown intent test**
  - **Description:** Intent không trong enum → route `general_chat`.
  - **Input/Output:** Force state/registry test harness.
  - **Acceptance Criteria:** NFR-REL-02 / D5.

**Phụ thuộc:** AG-03 phụ thuộc DBM-02; AG-04/AG-05 phụ thuộc bucket feedback (đã chốt Option C); SUM phụ thuộc AG-07; REG hardening có thể song song; TEST-* sau các AG tương ứng.

---

## 4.5. Risks & mitigations

| Risk | Mitigation |
| :-- | :-- |
| Gateway Gemma không hỗ trợ structured native | Task 1 LM-04 fallback JSON + retry parse; ghi capability trong SRS/ADR |
| Drift fixture YAML ↔ DB ERP thật | Trục α=C: `SchemaLoader` Protocol — phase sau thêm `DbScanSchemaLoader` không sửa node |
| Retry tới max attempts mà SQL không cải thiện | Trục β=C: bucket feedback + **`extras`** khi bucket cố định không đủ granular |
| Bucket feedback cố định không đủ chi tiết semantic | Field **`extras: dict`** đệm key-value tự do cho prompt `gen_sql` |
| Lệch RLS khi sau này bật `python_ro`/`http_spring` | V1 chỉ stub; prod target Spring — contract Task 3/API + Task 4 integration |

---

## 4.6. Out-of-scope

- **FastAPI Task 3:** endpoint invoke/stream, JWT/Spring wiring đầy đủ — PRD/task riêng.
- **QA Task 4:** E2E đầy đủ, eval automation — PRD/task riêng.
- **TASK-LM-05 multimodal** — phase 2.
- **Chỉnh `backend/smart-erp` / `frontend/mini-erp`** — track-scope; handoff `AI_BRIDGE` nếu đổi contract.
- **Distributed checkpointer** (Redis/Postgres saver).
- **CLI scanner** `information_schema` — phase 2 (Option C chỉ fixture + Protocol).
- **Implementation `python_ro` / `http_spring`** cho `SqlExecutor` — ngoài scope PRD Task 3 Agents v1 này.

---

## Quyết định khoá

| | |
| :-- | :-- |
| **Owner choice** | `pick optimal` → Planner chốt **Option C** (Trục **α=C**, **β=C**, **γ=C**) |
| **Slug confirmed** | `langgraph-gemma4-task3-agents` |
| **Ngày chốt** | **2026-05-10** |
| **Hành động kế** | **AI_BA** → **AI_PM** → **AI_TECH_LEAD** → **AI_DEVELOPER** → **AI_CODE_REVIEWER** (lean `/orchestrate`) |
