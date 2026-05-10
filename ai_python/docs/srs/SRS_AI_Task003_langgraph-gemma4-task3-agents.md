# SRS — AI Python — Task003 / LangGraph Gemma4 Task3 Agents

**Status:** Approved  
**Date:** 2026-05-10  
**MCP_PHASE:** 0  
**PRD:** `ai_python/docs/prd/PRD_langgraph-gemma4-task3-agents.md`  
**Task ID:** `Task003`  
**Slug:** `langgraph-gemma4-task3-agents`

---

## 1. Tóm tắt & phạm vi

**Quyết định khóa:** Task 3 triển khai theo **Option C** đã FINAL trong PRD: trục **α=C** dùng fixture YAML + `SchemaLoader` Protocol; trục **β=C** dùng feedback bucket dạng structured dict `{intent_review, policy, exec, result, attempts, extras?}`; trục **γ=C** giữ `execute_sql` ở mode **stub**.

**In-scope (`ai_python/`):**

- Thay stub nodes Task 2 bằng hành vi Agent v1: `intent`, `chat_normal`, `gen_sql`, `sql_review`, `validate_sql`, `execute_sql`, `validate_result`, `summarize_answer`.
- Thêm DBM artifact loader: schema YAML, `SchemaLoader` Protocol, `FileSchemaLoader`, allowlist dùng lại cho prompt và validate SQL.
- Registry hardening: unknown intent fallback `general_chat`, checklist thêm intent mới.
- Unit tests/fake LLM, retry tests, empty-result tests, log/correlation checks theo NFR.

**Out-of-scope:**

- FastAPI route Task 3/API, HTTP/SSE, JWT/Spring gateway contract.
- QA E2E Task 4, multimodal LM-05, distributed checkpointer, CLI scanner, `python_ro` / `http_spring` implementation cho `SqlExecutor`.
- Sửa `backend/` hoặc `frontend/`; nếu phát sinh drift contract thì handoff `AI_BRIDGE`.

---

## 2. Stakeholder & luồng

| Actor | Vai trò |
| :-- | :-- |
| Developer triển khai | Code agents, loader, registry, tests trong `ai_python/`. |
| Code agents / PM_RUN | Dùng SRS này để sinh task DEV, ADR và checklist test. |
| Spring gateway | Downstream cung cấp context/correlation sau này; Task 3 Agents chưa thiết kế HTTP. |
| End-user qua FE | Nhận câu trả lời cuối qua các task API/FE sau; không là interface trực tiếp của SRS này. |

**Luồng chính — `system_data_query` happy path:**

```text
user_text → intent (Agent_Intent) → route_by_intent="system_data_query"
  → sql_query subgraph: gen_sql → sql_review.ok=true → validate_sql.pass → execute_sql (stub) → validate_result.pass
  → summarize_answer → END
```

**Luồng chính — `general_chat`:**

```text
user_text → intent → route="general_chat" → chat_normal → END
```

**Luồng alt — retry SQL:**

```text
gen_sql → sql_review.ok=false (or validate_sql.fail / execute_sql.error / validate_result.fail-non-empty)
  → append vào bucket validation_feedback theo source
  → can_regen_sql? (sql_attempt_count < 3) → quay gen_sql
  → khi sql_attempt_count == 3 → fail_max_attempts → END với payload error có structure
```

**Luồng alt — empty result:**

```text
execute_sql.pass → validate_result.empty → KHÔNG retry (D4) → summarize_answer ("không có dữ liệu phù hợp") → END
```

**Luồng lỗi:**

- Gateway LLM down: `AG-01`/`AG-02`/`AG-03`/`AG-04` raise lỗi có kiểm soát để graph trả `error_payload` theo Task 2 `LG-11`/`LG-13`.
- `SchemaLoader` không load được file: `AG-03` raise hoặc early-fail có structure; DEV chốt một strategy và test missing file.
- `SqlExecutor` stub trả lỗi giả: map thành exec error path, append bucket `exec`, retry nếu còn attempt.

---

## 3. Functional requirements

| ID | Requirement test được | Trace / acceptance ngắn |
| :-- | :-- | :-- |
| **FR-AG-01** | Intent classification dùng input/output Pydantic/TypedDict; `IntentLabel = "system_data_query" \| "general_chat"`; ambiguous hoặc unknown từ LLM fallback `general_chat`; không đưa full schema DB vào prompt. | PRD `AG-01`, D1; test fake LLM ambiguous + snapshot prompt không có bảng/cột. |
| **FR-AG-02** | `chat_normal` gọi `get_llm_client("chat")`; không gọi DB/schema/sql tool; append assistant message vào `messages` và set `final_answer`. | PRD `AG-02`; test fake LLM và assert không import/call executor. |
| **FR-AG-03** | `gen_sql` gọi `SchemaLoader.load(schema_version)`; prompt nhận `validation_feedback` bucket dict; tăng `sql_attempt_count` trước khi gọi LLM; output một câu `SELECT`. | PRD `AG-03`, Task 2 `LG-09`; test counter, loader call, prompt feedback. |
| **FR-AG-04** | `sql_review` dùng structured `{ok, issues[]}` qua `get_llm_client("sql_review")`; `ok=false` append bucket `intent_review` cho lỗi semantic/schema hoặc `policy` cho lỗi structural/policy. | PRD `AG-04`; test ok/fail và bucket đúng. |
| **FR-AG-05** | `validate_sql` deterministic: SELECT-only, deny DDL/DML, allowlist bảng/cột từ DBM artifact, LIMIT bắt buộc hoặc inject an toàn theo strategy DEV chốt; fail append bucket `policy`; không gọi LLM. | PRD `AG-05`, D3; tests DROP/INSERT, table/column ngoài allowlist, LIMIT. |
| **FR-AG-06** | `execute_sql` wiring chỉ qua `SqlExecutor` mode `stub`; respect timeout config; runtime error append bucket `exec`; không bypass `validate_sql`. | PRD `AG-06`, Task 2 `SqlExecutor`; graph edge test. |
| **FR-AG-07** | `validate_result` kiểm `max_rows` và `max_bytes`; empty result không retry; non-empty invalid append bucket `result` và retry nếu còn attempt. | PRD `AG-07`, D4; empty fixture và oversized fixture. |
| **FR-SUM-01** | `summarize_answer` dùng locale mặc định `vi-VN`; chỉ tóm tắt số liệu có trong rows; empty/null trả câu mẫu "Không có dữ liệu phù hợp với yêu cầu". | PRD `SUM-01..02`, D6; snapshot/fake LLM không bịa số. |
| **FR-REG-01** | Registry hardening: unknown intent route `general_chat`; thêm `ai_python/docs/intent_registry_howto.md` với checklist thêm intent mới. | PRD `REG-01..03`, D5; registry test + doc exists. |
| **FR-DBM-01** | Schema artifact YAML có `schema_version`, danh sách bảng/cột allowlist, `pk`, FK chọn lọc, `updated_at?`. | PRD `AGENT-DBM-01`; loader fixture validates schema. |
| **FR-DBM-02** | Thêm `SchemaLoader` Protocol và `FileSchemaLoader` implementation: `load(schema_version: str) -> SchemaArtifact`. | PRD `AGENT-DBM-02`; happy path + missing file test. |
| **FR-DBM-03** | `validate_sql` và `gen_sql` dùng cùng `SchemaArtifact`/allowlist; không có nguồn allowlist thứ hai drift với artifact. | PRD `AGENT-DBM-03`; test column ngoài artifact fail. |
| **FR-CTX-01** | Context cite: lập bảng vị trí Agent đọc field từ `state` vs `config["configurable"]`, cite Task 2 `LG-03.4`; không redefine topology/context model. | PRD `CTX-01..02`, Task 2 `LG-03.4`; doc/table present. |

---

## 4. API / integration

SRS này chỉ định **contract trong-Python** và state shape; **không** thiết kế HTTP, SSE, OpenAPI hoặc Spring endpoint.

**LLM port kế thừa Task 1:**

- Conceptual contract: `LlmClient.invoke(...)`, `LlmClient.stream(...)`, `LlmClient.with_structured_output(schema)`.
- Scaffold hiện có tương đương: `invoke_text(...)`, `stream_text(...)`, `structured_predict(messages, schema, max_retries=3)`.
- Agent nodes chỉ gọi qua `get_llm_client(role)`; không tạo `ChatOpenAI` trực tiếp ngoài `app/llm/*`.

**Executor port kế thừa Task 2:**

- `SqlExecutor.execute(sql, ctx) -> ExecuteResult` hoặc shape tương đương hiện có trong `app/graph/sql_executor.py`.
- Task 3 chỉ dùng mode `stub`; `python_ro` và `http_spring` là out-of-scope.

**Schema loader mới:**

- `SchemaLoader.load(schema_version: str) -> SchemaArtifact`.
- `FileSchemaLoader` đọc YAML fixture dưới path DEV chốt, khuyến nghị `ai_python/app/data/schema/<schema_version>.yaml`.

**State/config integration:**

- `validation_feedback` là Pydantic model hoặc `TypedDict` serializable theo shape mục 5.
- `schema_version`, `locale`, `correlation_id`, `tenant_id`, `thread_id` đọc theo bảng CTX, ưu tiên đồng bộ Task 2 `LG-03.4`.

---

## 5. Data / state

```python
IntentLabel = Literal["system_data_query", "general_chat"]

class IntentDecision(TypedDict, total=False):
    intent: IntentLabel
    confidence: float
    reason_short: str

class SqlReviewVerdict(TypedDict):
    ok: bool
    issues: list[str]

class TableMeta(TypedDict, total=False):
    name: str
    columns: list[str]
    pk: list[str]
    fks: list[dict[str, str]]

class SchemaArtifact(TypedDict, total=False):
    schema_version: str
    tables: list[TableMeta]
    updated_at: str

class ValidationFeedback(TypedDict, total=False):
    intent_review: list[str]
    policy: list[str]
    exec: list[str]
    result: list[str]
    attempts: int
    extras: dict[str, object] | None

class ExecuteResult(TypedDict, total=False):
    rows: list[dict[str, object]] | None
    error: str | None
    row_count: int
    byte_size: int | None
```

**AgentState refine từ Task 2:** hiện scaffold có `validation_feedback: list[str]`; Task 3 migrate cẩn trọng sang `ValidationFeedback` hoặc adapter helper để không break tests Task 2. Nếu cần bổ sung field (`locale`, structured feedback, schema artifact cache), DEV phải giữ defaults tương thích `default_initial_state()`.

**CTX field table (cite Task 2 `LG-03.4`):**

| Field | Nguồn đọc ưu tiên | Dùng bởi |
| :-- | :-- | :-- |
| `correlation_id` | `config["configurable"]`, fallback state | log mọi node, executor stub |
| `tenant_id` | `config["configurable"]` hoặc state metadata | trace/policy placeholder v1 |
| `schema_version` | state hoặc configurable; DEV chốt một ưu tiên | `SchemaLoader.load` |
| `thread_id` | `config["configurable"]` | checkpointer Task 2 |
| `locale` | state hoặc configurable; default `vi-VN` | intent/chat/summarize |

---

## 6. NFR

| ID | Yêu cầu | Ngưỡng | Đo bằng |
| :-- | :-- | :-- | :-- |
| NFR-PERF-01 | Latency `intent` (mock) | p95 < 50ms | pytest-benchmark hoặc `time.perf_counter` |
| NFR-PERF-02 | Latency `validate_sql` deterministic | p95 < 20ms | local unit/benchmark |
| NFR-PERF-03 | Latency `validate_result` | p95 < 5ms | local unit/benchmark |
| NFR-REL-01 | Retry cap | đúng 3 lần `gen_sql` | unit test cạnh graph |
| NFR-REL-02 | Empty không retry | 0 retry SQL khi empty | test fixture empty |
| NFR-SEC-01 | SQL không bypass `validate_sql` | 100% | test cạnh + grep code |
| NFR-SEC-02 | LLM không tạo `ChatOpenAI` rải rác | 100% | grep test: chỉ `app/llm/*` import `ChatOpenAI` |
| NFR-OBS-01 | Mỗi node log có `correlation_id` khi inject | 100% | log capture test |
| NFR-TEST-01 | Coverage `app/graph/nodes/*` mới | ≥ 85% line | `pytest --cov=app.graph.nodes` |
| NFR-TEST-02 | Mỗi Agent ≥ 1 unit test fake LLM | 8/8 nodes | enumerate test files |
| NFR-PROMPT-01 | Không leak schema bảng vào prompt `intent` | 100% | prompt snapshot/review |
| NFR-INJ-01 | `validate_sql` chặn DDL/DML | 100% | tests `DROP`, `INSERT`, `UPDATE`, `DELETE`, `ALTER` |

---

## 7. Acceptance criteria

### FR-AG-01 — Intent classification

- **Given** fake LLM trả `system_data_query`, **When** node `intent` chạy, **Then** `state.intent` là `system_data_query` và registry route tới SQL subgraph.
- **Given** fake LLM trả ambiguous/invalid label, **When** node `intent` chạy, **Then** `state.intent` fallback `general_chat`.

### FR-AG-02 — Chat normal

- **Given** `state.intent="general_chat"` và fake `get_llm_client("chat")`, **When** `chat_normal` chạy, **Then** `final_answer` được set, assistant message được append, và không gọi `SqlExecutor`/`SchemaLoader`.

### FR-AG-03 — Generate SQL

- **Given** `state.schema_version="v1"`, `state.user_text="doanh số tháng này"`, `state.validation_feedback.policy=["thiếu LIMIT"]`, `attempts=1`, **When** `gen_sql` chạy, **Then** `sql_attempt_count` tăng `1→2` trước LLM, `SchemaLoader.load("v1")` được gọi, prompt include bucket `policy`, output là một `SELECT` có `LIMIT`.

### FR-AG-04 — SQL review

- **Given** fake sql_review trả `{ok:false, issues:["cột revenue không có trong schema"]}`, **When** `sql_review` chạy, **Then** issue được append vào `validation_feedback.intent_review` và route không đi `validate_sql`.

### FR-AG-05 — Validate SQL deterministic

- **Given** `generated_sql="DROP TABLE users"`, **When** `validate_sql` chạy, **Then** node fail, append bucket `policy`, và không gọi LLM hoặc executor.
- **Given** SQL dùng cột không có trong artifact allowlist, **When** `validate_sql` chạy, **Then** fail với message bucket `policy` chỉ rõ table/column bị chặn.

### FR-AG-06 — Execute SQL wiring

- **Given** `validate_sql.pass=true` và `SqlExecutor` stub trả lỗi timeout giả, **When** `execute_sql` chạy, **Then** append `validation_feedback.exec`, giữ error có structure, và route retry nếu `can_regen_sql`.

### FR-AG-07 — Validate result

- **Given** `query_result.rows=[]`, **When** `validate_result` chạy, **Then** không tăng `sql_attempt_count`, không route lại `gen_sql`, chuyển `summarize_answer`.
- **Given** `query_result.row_count > max_rows`, **When** `validate_result` chạy, **Then** append bucket `result` và route retry nếu còn attempt.

### FR-SUM-01 — Summarize

- **Given** rows chứa `total=1200000` và không có số khác, **When** `summarize_answer` chạy với locale mặc định, **Then** câu trả lời tiếng Việt chỉ dùng số liệu từ rows.
- **Given** empty rows, **When** `summarize_answer` chạy, **Then** trả câu mẫu "Không có dữ liệu phù hợp với yêu cầu" hoặc biến thể được snapshot chấp nhận.

### FR-REG-01 — Registry hardening

- **Given** `state.intent="unknown_intent"`, **When** `route_by_intent` chạy, **Then** route là `general_chat`.
- **Given** repo sau implementation, **When** kiểm tra docs, **Then** tồn tại `ai_python/docs/intent_registry_howto.md` có checklist enum, schema, handler, tests.

### FR-DBM-01 — Schema artifact format

- **Given** YAML fixture `v1`, **When** validate schema artifact, **Then** có `schema_version`, `tables[].name`, `tables[].columns`, `pk`, và `fks` hợp lệ.

### FR-DBM-02 — SchemaLoader

- **Given** `schema_version="v1"`, **When** `FileSchemaLoader.load("v1")` chạy, **Then** trả `SchemaArtifact`.
- **Given** file không tồn tại, **When** loader chạy, **Then** raise/return early-fail có message kiểm soát để `gen_sql` không gọi LLM với schema rỗng.

### FR-DBM-03 — Allowlist reuse

- **Given** artifact không chứa bảng `secret_table`, **When** `gen_sql`/`validate_sql` dùng schema v1, **Then** prompt không expose bảng đó và SQL chứa bảng đó bị fail.

### FR-CTX-01 — Context cite

- **Given** implementation docs/ADR Task 3, **When** reviewer kiểm tra, **Then** có bảng state vs `config["configurable"]` cho `correlation_id`, `tenant_id`, `schema_version`, `thread_id`, `locale`, cite Task 2 `LG-03.4`.

---

## 8. Traceability

| FR | PRD / Design source | Task breakdown / Decision |
| :-- | :-- | :-- |
| FR-AG-01 | PRD §4.2 `AG-01`; `TASK_AGENTS_V1_DESIGN.md` §1 | `AG-01.1..3`, D1 |
| FR-AG-02 | PRD §4.2 `AG-02`; Design §2 | `AG-02.1..2` |
| FR-AG-03 | PRD §4.2 `AG-03`; Design §4 | `AG-03.1..3`, `LG-09`, Option C α/β |
| FR-AG-04 | PRD §4.2 `AG-04`; Design §5 | `AG-04.1..2`, bucket `intent_review`/`policy` |
| FR-AG-05 | PRD §4.2 `AG-05`; Design §6 | `AG-05.1..4`, D3 |
| FR-AG-06 | PRD §4.2 `AG-06`; Task 2 SRS `FR-08` | `AG-06`, Option C γ |
| FR-AG-07 | PRD §4.2 `AG-07`; Design §8 | `AG-07.1..2`, D4 |
| FR-SUM-01 | PRD §4.2 `SUM-01..02`; Design §9 | `SUM-01`, `SUM-02`, D6 |
| FR-REG-01 | PRD §4.2 `REG-01..03`; Design §10 | `REG-01..3`, D5 |
| FR-DBM-01 | PRD §4.2 `AGENT-DBM-01`; Design §3 | `AGENT-DBM-01` |
| FR-DBM-02 | PRD §4.2 `AGENT-DBM-02`; Design §3 | `AGENT-DBM-04`, Option C α |
| FR-DBM-03 | PRD §4.2 `AGENT-DBM-03`; Design §6 | `VAL-SQL-03` |
| FR-CTX-01 | PRD §4.2 `CTX-01..02`; Task 2 `LG-03.4` | Context table, no topology redefine |

**Gate exit:** PASS — PRD đã có NFR/acceptance đủ để không STOP; `OUT_PATH` đã ghi; SRS có đủ 8 mục theo `AI_BA` §2 và trạng thái `Approved`.
