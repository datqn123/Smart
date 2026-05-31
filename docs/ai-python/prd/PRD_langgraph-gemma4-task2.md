# PRD (FINAL) — Task 2: LangGraph foundation + SQL subgraph (không gồm thiết kế Agent node)

**Track:** `ai_python` only  
**Slug:** `langgraph-gemma4-task2`  
**Trạng thái:** **FINAL**  
**Quyết định kiến trúc (Owner):** **SQL execution — Option C** (port `SqlExecutor`: `stub` | `python_ro` | `http_spring`, CI ưu tiên `stub`, prod hướng `http_spring`). **Checkpoint — Option C** (factory MemorySaver mặc định; SqliteSaver khi set `CHECKPOINT_SQLITE_PATH`).  
**Tham chiếu thiết kế:** `ai_python/TASKS/DESIGN/TASK_LANGGRAPH_GEMMA4_TRIEN_KHAI.md` (Task 2 — **chỉ** TASK-LG-01 … LG-14; TASK-AG-* thuộc task thiết kế Agent riêng).  
**Căn chỉnh Task 1:** `ai_python/docs/prd/PRD_langgraph-gemma4-task1.md` — nodes LangGraph gọi **`LlmClient` / registry role** (Option B đã chốt), không tạo `ChatOpenAI` rải rác.

**Phạm vi PRD này:** **Khung** LangGraph trong Task 2 DESIGN: state, graph routing, subgraph SQL + retry, registry, **placeholder/stub** cho các node tên (intent, chat, gen_sql, …), checkpointer/streaming/observability. **Không** gồm PRD chi tiết prompt/structured output/hành vi nghiệp vụ từng node Agent (TASK-AG-* — task khác).  
**Ngoài scope:** chỉnh `backend/`, `frontend/`; endpoint FastAPI hoàn chỉnh & wiring Spring chi tiết (**Task 3**); bộ QA đầy đủ (**Task 4** — chỉ liệt kê dependency nếu cần cho acceptance Task 2).

---

## Assumptions (mặc định — sửa nếu Owner khác)

1. **Contract node LLM / Agent** (prompt, schema JSON intent/sql_review, v.v.) do **task Agent / Task 1 LLM** định nghĩa; Task 2 chỉ **gắn callable stub hoặc adapter** vào cạnh graph theo tên node đã chốt ở task đó.  
2. **Intent v1 (routing graph):** giả định tối thiểu literal `system_data_query` | `general_chat` để `route_by_intent` hoạt động; chi tiết phân loại intent → task Agent khác.  
3. **`MAX_SQL_ATTEMPTS` = 3** (hằng số một nơi). Đếm **`sql_attempt_count` tăng khi bắt đầu mỗi lượt `gen_sql`** (trước gọi LLM) — dễ reasoning “lần thử thứ k”; ghi comment trong code.  
4. **Metadata:** `correlation_id`, `tenant_id`, `schema_version`, `thread_id` (optional) — một phần trong `config["configurable"]` và/hoặc state; DEV tài liệu hoá một chỗ (khớp LG-03.4 trong DESIGN).  
5. **Artifact schema** (nếu subgraph cần): có thể mock file JSON/YAML theo `schema_version` cho test graph; loader đầy đủ có thể thuộc task meta DB / Agent.  
6. **Header tương quan:** đồng bộ `X-Correlation-Id` giữa Spring và FastAPI khi Task 3 nối; Task 2 chuẩn bị helper/log context theo id này.

---

## 4.1. Project Overview

**Core goal:** Xây **LangGraph** trong `ai_python`: **state** có reducer tin nhắn; **main graph** `START → intent → route_by_intent`; nhánh **`general_chat`** (stub/callable) → `END`; nhánh **`system_data_query`** qua **subgraph** `sql_query` với chuỗi cạnh `gen_sql → sql_review → validate_sql → execute_sql → validate_result`, **retry về `gen_sql`** tối đa 3 lần với `validation_feedback` chuẩn hoá; **registry** intent → runnable/subgraph; node **`fail_max_attempts`**; **checkpointer**, **astream/astream_events** và **policy log**. **Triển khai logic bên trong từng node** (prompt, LLM, review SQL chi tiết) nằng task Agent / LLM — không nằm trong checklist PRD này.

**Target users / actors:**

- **Developer / Code agents:** triển khai graph, test mock LLM/SQL executor.  
- **Hệ thống downstream (Task 3):** FastAPI sẽ truyền `thread_id`, context Spring; Task 2 cung cấp graph compiled + contract stream/checkpoint.

**Goals**

- Hoàn thành checklist **TASK-LG-01 … LG-14** trong phạm vi Python (không checklist TASK-AG-*).  
- Tách boundary: **graph package không import FastAPI route** (khớp LG-02.3).  
- **Topology SQL:** mọi `execute_sql` graph-level phải đi sau `validate_sql` trên cạnh; chi tiết rule validate/review → task Agent + policy chung.

**Non-goals (Task 2 PRD này)**

- Thiết kế chi tiết từng **Agent node** (TASK-AG-01 … AG-07): prompt, few-shot, schema response, policy ambiguous intent — **task / PRD khác**.  
- UI, Spring controller, JWT validation đầy đủ (Task 3).  
- Multimodal intent (LM-05 / phase 2).  
- Redis/distributed checkpointer (có thể ADR sau).

---

## 4.2. Specifications

### Functional requirements — map TASK-ID

**Nền & layout (TASK-LG-01 … LG-03)**

- [ ] **TASK-LG-01** — Khai báo dependency: `langgraph`, `langchain-core`, `langchain-openai` (hoặc tương đương đã dùng Task 1), phiên bản cố định; Python khớp README (3.11+, khuyến nghị 3.12).  
- [ ] **TASK-LG-02** — Layout module gợi ý: `state.py`, graph entry (vd. `main_graph.py`), `sql_subgraph.py`, `nodes/*.py`, `registry.py`; `llm` tái sử dụng `app/llm/` Task 1; graph không phụ thuộc FastAPI.  
- [ ] **TASK-LG-03** — **`AgentState`**: `messages` + reducer (`add_messages`); `intent`, `schema_version`, `generated_sql`, `sql_attempt_count`, `validation_feedback`, `query_result`, `final_answer`; metadata (`correlation_id`, `tenant_id`, …) theo quy ước LG-03.4; default ban đầu rõ ràng.

**Graph & routing (TASK-LG-04 … LG-07)**

- [ ] **TASK-LG-04** — `StateGraph`: `START → intent → route_by_intent`.  
- [ ] **TASK-LG-05** — Nhánh `general_chat` → `chat_normal` → `END`.  
- [ ] **TASK-LG-06** — Nhánh `system_data_query` → subgraph `sql_query` → `summarize_answer` (hoặc tóm tắt trong subgraph) → `END`.  
- [ ] **TASK-LG-07** — **`INTENT_HANDLERS`**: map intent string → subgraph / runnable; stub mở rộng; intent unknown → hành vi đã giả định (general_chat).

**Subgraph SQL & retry (TASK-LG-08 … LG-11)**

- [ ] **TASK-LG-08** — Thứ tự node trong subgraph: `gen_sql` → `sql_review` → `validate_sql` → `execute_sql` → `validate_result`; conditional edges pass/fail đúng DESIGN.  
- [ ] **TASK-LG-09** — `can_regen_sql`: `sql_attempt_count < 3`; mọi retry chỉ tới `gen_sql` khi còn lượt.  
- [ ] **TASK-LG-10** — Mọi nhánh fail ghi **`validation_feedback`** trước khi route retry.  
- [ ] **TASK-LG-11** — Node `fail_max_attempts`: payload lỗi có cấu trúc (vd. `error`, `attempts`) để Task 3 map HTTP.

**Ngoài scope PRD này — thiết kế Agent (TASK-AG-*):** Prompt, structured output, policy ambiguous, chi tiết `sql_review` (LLM), loader schema đầy đủ cho `gen_sql`, v.v. — **không** liệt kê checklist tại đây; graph chỉ cần **tên node + cạnh** khớp TASK-LG-08 và stub inject được.

**Checkpointer, streaming, observability (TASK-LG-12 … LG-14)**

- [ ] **TASK-LG-12** — Checkpointer: **MemorySaver** và/hoặc **SqliteSaver** theo § Options; `thread_id` trong `configurable`.  
- [ ] **TASK-LG-13** — `astream` / `astream_events`; filter event theo node; gắn `correlation_id` vào log context.  
- [ ] **TASK-LG-14** — Policy log: danh sách field được phép; mask/truncate SQL và payload nhạy; không log secrets.

### Non-functional requirements (NFRs)

| ID | Yêu cầu | Mục tiêu / ngưỡng | Ghi chú |
| :-- | :-- | :-- | :-- |
| NFR-REL-01 | Retry cap SQL | **Tối đa 3** lần `gen_sql` mỗi invocation | Không “vô hạn” do LLM loop |
| NFR-PERF-01 | Thời gian subgraph SQL (không tính LLM provider) | **p95 < 500 ms** khi executor là stub/local SQLite nhỏ | Đo sau khi có harness |
| NFR-PERF-02 | Gọi executor thật (HTTP/DB) | **Timeout ≤ 30 s** mỗi query; có cancel/close connection | Tránh treo worker |
| NFR-SEC-01 | SQL surface | **100%** câu execute phải qua `validate_sql` | Không bypass |
| NFR-SEC-02 | Log | **0** log full SQL/payload khi policy `MASK_SQL=1` (env) | Mặc định dev có thể tắt mask |
| NFR-OBS-01 | Trace correlation | **100%** log dòng graph trong một request có cùng `correlation_id` khi được cấp | ContextVar hoặc tương đương |
| NFR-TEST-01 | Unit graph | **≥ 90%** nhánh routing + retry được cover bởi test mock (mục tiêu) | Task 4 mở rộng |

---

## 4.3. Tech stack & tech approach

**Tech approach (tóm tắt):** Dùng **LangGraph `StateGraph`** với **main graph** định tuyến theo `intent` và **subgraph** `sql_query` biên dịch riêng, ghép vào main graph như một node. **Call LLM trong node** gắn qua contract **Task 1 / task Agent** (không mô tả chi tiết tại PRD này). **Validate SQL deterministic** (nếu có trong repo graph) là Python thuần hoặc do task Agent chọn triển khai — PRD này chỉ yêu cầu **cạnh graph** không bypass `validate_sql` trước `execute_sql`. **Thực thi SQL** tách qua abstraction (§ Options). **Trạng hội thoại** qua checkpointer (§ Options); **quan sát** dùng `astream_events` + log có `correlation_id` và mask theo env.

| Lớp | Lựa chọn |
| :-- | :-- |
| **Runtime** | Python 3.11+ (khuyến nghị 3.12) |
| **Orchestration** | LangGraph `StateGraph`, subgraph compile |
| **LLM / Agent node** | Contract Task 1 + task Agent (PRD này: stub/wire) |
| **State / messages** | `langchain_core.messages`, reducer `add_messages` |
| **Persistence (conv)** | MemorySaver và/hoặc SqliteSaver (§ Options) |
| **SQL validate** | Thư viện/thủ công deterministic trong Python (không LLM) |
| **SQL execute** | Theo § Options (stub / RO DB / HTTP Spring) |
| **UI / Spring / FE** | Ngoài scope Task 2 |

---

## § Options — Thực thi SQL (cạnh `execute_sql` / SqlExecutor) — chọn **một**

### Option A — In-process read-only DB (Python)

**Mô tả:** Node `execute_sql` dùng SQLAlchemy/psycopg với **URL read-only** (env `DATABASE_URL_RO` hoặc tương đương), pool giới hạn.

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Latency thấp; dễ dev/local; ít dependency Task 3. |
| **Cons** | Rủi ro phân tán quyền/tenant nếu không khớp Spring; duplicate policy. |
| **Risks** | Lệch RLS/tenant so với cổng Spring. |
| **Cost-to-change** | Trung bình khi bắt buộc chuyển hết quyền về Spring. |
| **When to choose** | Prototype / nội bộ; DB RO đã có RLS đủ tin cậy. |

### Option B — HTTP delegation tới Spring (“run query”)

**Mô tả:** Python gọi **API nội bộ** Spring (contract JSON: SQL đã validate, `tenant_id`, limits); Spring thực thi và trả rows/metadata lỗi.

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | **Một cổng quyền**; đồng nhất audit/tenant với ERP. |
| **Cons** | Cần Task 3 + contract; latency mạng; stub phức tạp hơn cho unit test. |
| **Risks** | Chưa có endpoint → blocker; cần m2m auth. |
| **Cost-to-change** | Thấp sau khi contract ổn định. |
| **When to choose** | **Production** khớp plan “Spring làm cổng quyền”. |

### Option C — Port `SqlExecutor` + nhiều backend (stub / RO / HTTP)

**Mô tả:** Interface trong `ai_python`; env `SQL_EXECUTOR_MODE=stub|python_ro|http_spring`. CI dùng `stub`; dev có thể `python_ro`; staging/prod `http_spring`.

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Test không mạng; không chặn DEV; migration dần sang B. |
| **Cons** | Nhiều code path; phải giữ parity hành vi. |
| **Risks** | Drift giữa stub và Spring nếu không có integration test (Task 4). |
| **Cost-to-change** | Cao hơn A lúc đầu; thấp dài hạn. |
| **When to choose** | **Khuyến nghị mặc định** khi Task 2 cần merge sớm mà endpoint Spring chưa xong. |

#### **Recommendation:** **Option C** (port + `stub` mặc định CI; **prod target = `http_spring`**; `python_ro` tuỳ chọn dev).  
**Đã chọn (Owner):** **Option C** (khớp recommendation).

---

## § Options — Checkpoint & persistence (TASK-LG-12)

### Option A — MemorySaver only

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Đơn giản; không file I/O. |
| **Cons** | Mất state khi restart process. |
| **Risks** | Không đủ cho demo “đa lượt” bền. |
| **When to choose** | Unit test / CI. |

### Option B — SqliteSaver (file path cấu hình)

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | **Hội thoại bền** qua restart; phù hợp single-instance dev/stage. |
| **Cons** | File locking / backup khi scale multi-worker. |
| **Risks** | Concurrent writers nếu nhiều process. |
| **When to choose** | **Dev/stage mặc định** có `thread_id`. |

### Option C — Pluggable factory (Memory default, Sqlite optional)

| Khía cạnh | Nội dung |
| :-- | :-- |
| **Pros** | Linh hoạt env; giống pattern `SqlExecutor`. |
| **Cons** | Thêm factory nhỏ. |
| **Risks** | Ít nếu scope rõ. |
| **When to choose** | Team muốn một chỗ cấu hình. |

#### **Recommendation:** **Option C** với **mặc định dev = SqliteSaver** khi có `CHECKPOINT_SQLITE_PATH`; ngược lại **MemorySaver** cho test nhanh.

**Đã chọn (Owner):** **Option C** (factory; Sqlite khi có path env, còn lại Memory).

---

## 4.4. Task breakdown & dependency graph

Mỗi mục checklist `[ ]`; acceptance criteria kiểm tra được.

- [ ] **TASK-LG-01 — Dependencies LangGraph**
  - **Description:** Pin `langgraph`, `langchain-core`, integration chat đã dùng Task 1; ghi Python tối thiểu.  
  - **Input/Output:** Input: `requirements.txt`/`pyproject.toml`. Output: cài đặt tái lập được.  
  - **Acceptance Criteria:** `pip install -r requirements.txt` thành công trên Python repo; không thêm deps ngoài scope Task 2.

- [ ] **TASK-LG-02 — Package layout graph**
  - **Description:** Tạo package (vd. `app/graph/`) với stub file theo DESIGN; boundary không import FastAPI.  
  - **Input/Output:** Input: DESIGN paths. Output: import graph từ tests được.  
  - **Acceptance Criteria:** `python -c "import app.graph"` (hoặc path tương đương) không lỗi; rule “no FastAPI in graph” có comment/README một dòng.

- [ ] **TASK-LG-03 — `AgentState`**
  - **Description:** Typed state + `messages` reducer + defaults + quy ước metadata configurable vs state.  
  - **Input/Output:** Input: plan fields. Output: type được dùng khi compile graph.  
  - **Acceptance Criteria:** State khởi tạo không crash; `messages` append đúng qua invoke một bước giả lập.

- [ ] **TASK-LG-04 — Main graph skeleton**
  - **Description:** `START → intent → route_by_intent` với `intent` stub có thể inject.  
  - **Input/Output:** Input: mock intent. Output: route đúng literal.  
  - **Acceptance Criteria:** Unit test: forced `general_chat` vs `system_data_query` đi đúng cạnh.

- [ ] **TASK-LG-05 — Branch general_chat**
  - **Description:** `chat_normal` → `END`; node có thể là **stub** hoặc callable inject — chi tiết LLM/prompt → task Agent.  
  - **Input/Output:** Input: messages. Output: `final_answer` (hoặc message cuối) được set khi stub/agent trả.  
  - **Acceptance Criteria:** Stub/mock: không đi nhánh SQL executor; graph kết thúc `END`.

- [ ] **TASK-LG-06 — Branch system_data_query + subgraph**
  - **Description:** Nối subgraph `sql_query` rồi `summarize_answer` → `END`.  
  - **Input/Output:** Input: user query + schema_version. Output: `final_answer` sau SQL path thành công (khi stub/agent đầy đủ).  
  - **Acceptance Criteria:** Subgraph **compile** được với stub node; một happy-path mock (không yêu cầu hành vi Agent production) trả kết quả.

- [ ] **TASK-LG-07 — Registry `INTENT_HANDLERS`**
  - **Description:** Dict/registry map intent → runnable; unknown intent theo assumption.  
  - **Input/Output:** Input: intent string. Output: runnable tương ứng.  
  - **Acceptance Criteria:** Thêm intent giả third-party chỉ bằng đăng ký (không sửa core route) — test nhỏ.

- [ ] **TASK-LG-08 — SQL subgraph chain**
  - **Description:** Nodes và edge theo thứ tự DESIGN + conditional fail.  
  - **Input/Output:** Input: state có messages. Output: cập nhật `generated_sql`, `query_result`, v.v.  
  - **Acceptance Criteria:** Graph diagram hoặc test duyệt cạnh: đúng thứ tự, không nhảy bước validate.

- [ ] **TASK-LG-09 — Retry cap 3**
  - **Description:** `can_regen_sql`, tăng `sql_attempt_count` khi vào `gen_sql` (trước LLM).  
  - **Input/Output:** Input: fail ở validate/review. Output: tối đa 3 lần gen.  
  - **Acceptance Criteria:** Test: fail liên tục → đúng 3 lần vào `gen_sql`; lần 4 không xảy ra.

- [ ] **TASK-LG-10 — `validation_feedback` on fail**
  - **Description:** Helper append feedback; mọi fail nhánh SQL ghi trước retry.  
  - **Input/Output:** Input: lỗi node. Output: state.feedback serializable.  
  - **Acceptance Criteria:** Sau mỗi fail, feedback không rỗng và được đọc ở lần `gen_sql` kế.

- [ ] **TASK-LG-11 — `fail_max_attempts`**
  - **Description:** Node trả cấu trúc lỗi cố định.  
  - **Input/Output:** Input: hết lượt. Output: payload lỗi.  
  - **Acceptance Criteria:** Test snapshot khóa keys tối thiểu (`error`, `attempts` hoặc tương đương đã doc).

- [ ] **TASK-LG-12 — Checkpointer**
  - **Description:** Cấu hình theo § Options checkpoint; `thread_id` trong configurable.  
  - **Input/Output:** Input: `thread_id`. Output: state có thể resume.  
  - **Acceptance Criteria:** Hai invoke cùng `thread_id` thấy messages tích lũy (với backend bền nếu chọn Sqlite).

- [ ] **TASK-LG-13 — Streaming hooks**
  - **Description:** Wrapper `astream`/`astream_events` + filter; correlation trong log.  
  - **Input/Output:** Input: graph compiled. Output: iterable events.  
  - **Acceptance Criteria:** Test: ít nhất 1 event có tên node mong đợi; log capture có `correlation_id` khi inject.

- [ ] **TASK-LG-14 — Logging policy**
  - **Description:** Allowlist field log; mask SQL theo env; tài liệu hoá.  
  - **Input/Output:** Input: state chứa SQL. Output: log đã mask.  
  - **Acceptance Criteria:** Với `MASK_SQL=1`, log fixture không chứa chuỗi SQL đầy đủ.

**Phụ thuộc gợi ý:** LG-01→02→03 trước LG-04; LG-05 song song LG-04 sau skeleton; LG-08 cần LG-06; LG-12…14 có thể song song sau compile graph đầu tiên. Triển khai node thật (Agent) nối sau khi có PRD/task Agent và Task 1 LLM.

---

## 4.5. Risks & mitigations

| Risk | Mitigation |
| :-- | :-- |
| Gateway structured / parse JSON không ổn định | Task 1 LM-04 + task Agent (intent/sql_review); không thuộc PRD graph-only này |
| Retry vô hạn / đếm sai | Một hằng `MAX_SQL_ATTEMPTS`; unit test đếm cạnh |
| Lộ dữ liệu qua log | LG-14 mask + review env prod |
| Executor Spring chưa sẵn | Option C stub; contract OpenAPI/Task 3 |

---

## 4.6. Out-of-scope

- Thiết kế chi tiết **Agent node** (TASK-AG-*) — PRD/task Agent riêng.  
- Sửa `backend/`, `frontend/`; triển khai đầy đủ Task 3 API và auth Spring.  
- Redis checkpointer, multimodal.  
- Đầy đủ Task 4 (PRD Task 2 chỉ đặt NFR-TEST-01 mục tiêu; test tối thiểu nằm trong acceptance từng task).

---

## Quyết định (đã khóa)

Đã ghi ở metadata đầu file và tại từng § Options tương ứng (**SQL = C**, **Checkpoint = C**).
