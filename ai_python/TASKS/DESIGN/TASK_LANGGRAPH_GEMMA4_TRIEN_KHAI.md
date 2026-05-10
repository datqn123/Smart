# Task triển khai — LangGraph + Gemma 4 (`ai_python`)

**Phạm vi:** Thiết kế danh sách công việc (task) để cài đặt orchestration **LangGraph** và tích hợp LLM **Gemma 4** qua API OpenAI-compatible; **chưa** bao gồm code chi tiết.

**Tham chiếu:**

- `docs/plan/feature/ai_chatbot_da_agent_v1.plan.md` — đặc tả graph (state, subgraph `sql_query`, `sql_review`, retry `gen_sql` tối đa 3, registry intent, checkpointer/streaming tuỳ chọn).
- Plan stack (Cursor): `ai_chatbot_stack_phân_tích_2a2c5a12` — LangChain/LangGraph trong process FastAPI; MCP không bắt buộc v1; Spring làm cổng quyền.

**Nhóm task (theo thứ tự 1–4):**

| STT | Tên nhóm | Nội dung gộp |
| :-- | :-- | :-- |
| **1** | **Task 1** | Gemma 4 / OpenAI-compatible — cấu hình, factory, streaming, structured output, multimodal (tuỳ chọn). |
| **2** | **Task 2** | LangGraph nền + subgraph SQL + node agent + checkpointer/obs. |
| **3** | **Task 3** | FastAPI — endpoint, context Spring, invoke/stream. |
| **4** | **Task 4** | Kiểm thử — unit / integration. |

---

## Task 1 — Mẫu kết nối Gemma 4 (FPT Cloud — OpenAI-compatible)

**Bối cảnh triển khai:** Endpoint kiểu OpenAI (`chat.completions`), client Python dùng `openai.OpenAI(api_key=..., base_url=...)`.

| Tham số | Giá trị gợi ý (từ mẫu) | Ghi chú task |
| :-- | :-- | :-- |
| `BASE_URL` | `https://mkp-api.fptcloud.com` | Đưa vào biến môi trường (không hard-code trong repo). |
| `MODEL_NAME` | `gemma-4-31B-it` | Chuẩn hoá hằng số cấu hình; cho phép override qua env. |
| `API_KEY` | Secret | Chỉ env / secret manager; không commit. |

**Mẫu người dùng cung cấp** còn có **đa phương tiện** (ảnh base64 + `chat.completions` với `content` multi-part text + `image_url`). **v1 chatbot theo plan** tập trung **văn bản**; task đa phương tiện có thể **tách phase 2** (intent hình ảnh, đính kèm báo cáo, v.v.).

**Task LLM từ mẫu:**

- **TASK-LM-01** — Định nghĩa contract cấu hình: `base_url`, `api_key`, `model`, `default_temperature`, `max_tokens`, `top_p`, `top_k`, `streaming` (map sang tham số API nếu gateway hỗ trợ).
- **TASK-LM-02** — Quyết định lớp tích hợp LangChain: dùng `ChatOpenAI` (hoặc wrapper tương đương) trỏ `base_url` + `model` tới Gemma, để **mọi node LangGraph** gọi thống nhất một factory (tránh rải `OpenAI()` thủ công).
- **TASK-LM-03** — Path **streaming**: graph/server dùng stream chunk → map sang `astream` / `astream_events` của LangGraph (khớp mục streaming trong plan feature).
- **TASK-LM-04** — **Structured output** cho `Agent_Intent` và các node cần JSON (vd. `sql_review`): kiểm tra Gemma + gateway có hỗ trợ `response_format` / tool schema; nếu không, task fallback **prompt + parse JSON** + retry nhẹ (giới hạn lần).
- **TASK-LM-05** (tuỳ chọn, sau v1 text) — Multimodal: tái sử dụng pattern `image_url` + base64 như mẫu; chỉ bật khi có yêu cầu sản phẩm + policy bảo mật ảnh.

---

## Task 2 — Nền LangGraph (khớp plan feature)

### Task 2.1 Phụ thuộc & khung dự án

- **TASK-LG-01** — Khai báo dependency: `langgraph`, `langchain-core`, integration chat model (OpenAI-compatible), phiên bản Python khớp repo.
- **TASK-LG-02** — Module layout gợi ý: `state.py` (schema), `graph/main.py`, `graph/sql_subgraph.py`, `nodes/*.py`, `registry.py`, `llm/factory.py`.
- **TASK-LG-03** — Định nghĩa **state** (`AgentState`): `messages` + reducer; `intent`, `schema_version`, `generated_sql`, `sql_attempt_count`, `validation_feedback`, `query_result`, `final_answer`; metadata `correlation_id`, `tenant_id`, … (theo bảng plan §4.1).

### Task 2.2 Graph gốc & định tuyến

- **TASK-LG-04** — `StateGraph`: `START → intent → route_by_intent`.
- **TASK-LG-05** — Nhánh `general_chat` → node `chat_normal` → `END` (LLM Gemma, không tool DB v1).
- **TASK-LG-06** — Nhánh `system_data_query` → **subgraph** `sql_query` → node `summarize_answer` (hoặc gộp tóm tắt trong subgraph) → `END`.
- **TASK-LG-07** — **Registry** `INTENT_HANDLERS`: map intent string → subgraph / runnable; stub intent mở rộng sau.

### Task 2.3 Subgraph SQL & retry

- **TASK-LG-08** — Cài đặt chuỗi: `gen_sql` → `sql_review` → `validate_sql` → `execute_sql` → `validate_result` (đúng thứ tự plan §4.3).
- **TASK-LG-09** — Điều kiện **`can_regen_sql`**: `sql_attempt_count < MAX_SQL_ATTEMPTS` (3); **mỗi lần vào `gen_sql`** tăng đếm trước/sau gọi LLM theo quy ước đã chốt (khớp §2.1 plan).
- **TASK-LG-10** — Mọi nhánh fail ghi `validation_feedback` trước khi quay `gen_sql`.
- **TASK-LG-11** — Node `fail_max_attempts` trả lỗi có cấu trúc cho tầng API.

### Task 2.4 Agent nghiệp vụ (mapping node)

- **TASK-AG-01** — `intent`: prompt + structured output → `system_data_query` | `general_chat`.
- **TASK-AG-02** — `chat_normal`: Gemma, không bind execute DB.
- **TASK-AG-03** — `gen_sql`: đọc artifact schema theo `schema_version` (từ Agent_DB_Meta — có thể mock file trước).
- **TASK-AG-04** — `sql_review` (Agent_SQL_Review): output `ok` / `issues[]`; fail không execute.
- **TASK-AG-05** — `validate_sql`: deterministic — SELECT-only, allowlist, LIMIT, chặn DDL/DML.
- **TASK-AG-06** — `execute_sql`: read-only connection hoặc gọi Spring (quyết định kiến trúc trong task riêng tích hợp BE).
- **TASK-AG-07** — `validate_result`: kích thước payload, shape tối thiểu; policy retry như plan.

### Task 2.5 Checkpointer, streaming, quan sát

- **TASK-LG-12** — (Khuyến nghị) MemorySaver / SqliteSaver + `thread_id` từ Spring để hội thoại đa lượt.
- **TASK-LG-13** — `astream` / `astream_events` + gắn `correlation_id` vào metadata log theo node.
- **TASK-LG-14** — Policy log: không log full SQL/payload nếu policy cấm; correlation xuyên Spring–Python.

---

## Task 3 — Tích hợp Spring / FastAPI (điểm chạm)

- **TASK-API-01** — Endpoint FastAPI nhận context đã được Spring kiểm tra quyền AI; forward `user_id`, `tenant_id`, `correlation_id`, `schema_version`, `thread_id` (optional).
- **TASK-API-02** — `invoke` vs stream response; không expose `API_KEY` ra client.

---

## Task 4 — Kiểm thử & tiêu chí xong

- **TASK-QA-01** — Unit test: routing intent; mock LLM cho subgraph; retry đếm đủ 3 lần `gen_sql`; đường fail `sql_review` / `validate_sql` / execute.
- **TASK-QA-02** — Integration nhẹ: một round-trip `general_chat` và một `system_data_query` với DB mock / SQLite dev.

**Định nghĩa “xong” giai đoạn thiết kế task:** Tất cả task trên được gán owner/ước lượng; dependency Task 1 / TASK-LM-* làm trước hoặc song song với skeleton Task 2 / TASK-LG-01–03.

---

## 5. Thứ tự gợi ý

1. **Task 1:** TASK-LM-01 … LM-03 + **Task 2:** TASK-LG-01 … LG-03 (nền + LLM factory).  
2. **Task 2:** TASK-LG-04 … LG-07 + TASK-AG-01 … AG-02 (đường chat hoạt động end-to-end tối thiểu).  
3. **Task 2:** TASK-LG-08 … LG-11 + TASK-AG-03 … AG-07 (nhánh SQL + retry).  
4. **Task 1:** TASK-LM-04 (structured output ổn định cho intent/sql_review).  
5. **Task 2** + **Task 3:** TASK-LG-12 … LG-14 + TASK-API-01 … API-02.  
6. **Task 4:** TASK-QA-01 … QA-02; Task 1 / TASK-LM-05 khi cần multimodal.

---

## 6. Phân rã task nhỏ (chi tiết)

Dưới đây là **task con** cho từng **TASK-*** trong **Task 1–4**; ID con dùng hậu tố `.n` để theo dõi trong board/issue.

### Task 1 — Phân rã TASK-LM-* (Gemma / LLM)

| Task cha | Task nhỏ | Mô tả ngắn |
| :-- | :-- | :-- |
| **LM-01** | LM-01.1 | Liệt kê biến môi trường: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TOP_P`, `LLM_TOP_K`, cờ `LLM_STREAMING_DEFAULT`. |
| | LM-01.2 | File `.env.example` / mục README chỉ **tên** biến, không giá trị secret. |
| | LM-01.3 | Module load config (vd. Pydantic `Settings`) + fail fast nếu thiếu `API_KEY` khi bật LLM. |
| | LM-01.4 | Map `top_k` / tham số khác: chỉ gửi nếu gateway FPT hỗ trợ (tránh 400). |
| **LM-02** | LM-02.1 | Chọn lớp tích hợp: `ChatOpenAI` (`langchain-openai`) với `base_url`, `model`, `api_key`. |
| | LM-02.2 | Hàm `get_chat_model(model_overrides: dict \| None)` — một điểm tạo model cho toàn app. |
| | LM-02.3 | Tách **model chính** vs **model nhỏ** (tuỳ chọn sau): cùng factory, khác env prefix. |
| | LM-02.4 | Smoke test thủ công/script: một `invoke` text đơn, không LangGraph. |
| **LM-03** | LM-03.1 | Wrapper stream từ `ChatOpenAI.stream()` → iterator chunk văn bản thuần. |
| | LM-03.2 | Nối FastAPI `StreamingResponse` (hoặc SSE) với stream graph (sau TASK-LG-13). |
| | LM-03.3 | Định dạng chunk gửi FE (plain delta vs JSON envelope có `correlation_id`). |
| **LM-04** | LM-04.1 | Thử `with_structured_output` / tool calling trên gateway Gemma; ghi nhận hỗ trợ hay không. |
| | LM-04.2 | Schema Pydantic cho intent (`system_data_query` \| `general_chat`) + parse an toàn. |
| | LM-04.3 | Schema cho `sql_review` (`ok`, `issues[]`) + parse + retry parse tối đa N lần. |
| | LM-04.4 | Fallback: prompt “chỉ trả về JSON trong khối ```” + `json.loads` + xử lý lỗi. |
| **LM-05** | LM-05.1 | Hàm `encode_image(path) -> base64` + MIME type. |
| | LM-05.2 | Builder message multimodal (text + `image_url` data URI) tương thích chat completions. |
| | LM-05.3 | Policy: kích thước ảnh tối đa, loại file được phép, không log base64. |

### Task 2 — Phân rã TASK-LG-* (LangGraph nền)

| Task cha | Task nhỏ | Mô tả ngắn |
| :-- | :-- | :-- |
| **LG-01** | LG-01.1 | Cập nhật `requirements.txt` / `pyproject.toml`: `langgraph`, `langchain-core`, `langchain-openai`, phiên bản cố định. |
| | LG-01.2 | Kiểm tra Python version đã chọn với wheel của deps. |
| **LG-02** | LG-02.1 | Tạo package `app.graph` (hoặc tên đã chốt) + `__init__.py`. |
| | LG-02.2 | Tạo file rỗng/stub: `state.py`, `main_graph.py`, `sql_subgraph.py`, `registry.py`, `llm/factory.py`. |
| | LG-02.3 | Quy ước import và boundary (graph không import FastAPI route). |
| **LG-03** | LG-03.1 | Định nghĩa type state (TypedDict hoặc Pydantic) khớp plan. |
| | LG-03.2 | Gắn `messages` với `add_messages` / reducer đúng chuẩn LangGraph. |
| | LG-03.3 | Default ban đầu: `sql_attempt_count=0`, `validation_feedback=None`, v.v. |
| | LG-03.4 | Trường metadata: quyết định trong state vs `config["configurable"]` và tài liệu hoá. |
| **LG-04** | LG-04.1 | Node `intent` gọi runnable (stub trả cố định trước). |
| | LG-04.2 | Hàm `route_by_intent(state) -> Literal["general_chat","system_data_query"]`. |
| | LG-04.3 | `add_conditional_edges` từ `intent` tới hai nhánh. |
| **LG-05** | LG-05.1 | Node `chat_normal`: nhận `messages`, gọi LLM, ghi `final_answer`. |
| | LG-05.2 | Đảm bảo không import tool DB trong module này. |
| **LG-06** | LG-06.1 | Compile subgraph `sql_query` (có thể rỗng + một node pass-through trước). |
| | LG-06.2 | Nối output subgraph → `summarize_answer` (hoặc placeholder copy `query_result`). |
| | LG-06.3 | Main graph: `sql_sub` → `summarize_answer` → END. |
| **LG-07** | LG-07.1 | `Dict[str, Runnable]` hoặc compiled graph — key là intent. |
| | LG-07.2 | Đăng ký tối thiểu hai intent v1 + intent “unknown” → `chat_normal` hoặc lỗi có cấu trúc. |
| | LG-07.3 | Điểm mở rộng: thêm intent mới chỉ đăng ký, không sửa `route_by_intent` cồng kềnh. |
| **LG-08** | LG-08.1 | Trong subgraph: `add_node` từng bước theo đúng thứ tự. |
| | LG-08.2 | `add_edge` tuyến tính `gen_sql` → `sql_review` → … |
| | LG-08.3 | Conditional edges từ `sql_review`, `validate_sql`, `execute_sql`, `validate_result` (pass/fail). |
| **LG-09** | LG-09.1 | Hằng `MAX_SQL_ATTEMPTS = 3` một nơi. |
| | LG-09.2 | Trong node `gen_sql`: tăng `sql_attempt_count` đúng quy ước (trước/sau LLM — **chốt một** và viết comment). |
| | LG-09.3 | Hàm `can_regen_sql(state) -> bool`. |
| | LG-09.4 | Mọi nhánh retry chỉ đi `gen_sql` khi `can_regen_sql`; không thì `fail_max_attempts`. |
| **LG-10** | LG-10.1 | Chuẩn hoá format `validation_feedback` (string hoặc dict serializable). |
| | LG-10.2 | Helper `append_feedback(source: str, detail: str)` để các node fail gọi thống nhất. |
| **LG-11** | LG-11.1 | Node trả `{ "error": "max_sql_attempts", "attempts": … }` (hoặc tương đương). |
| | LG-11.2 | Map sang HTTP/status cho FastAPI (TASK-API). |
| **LG-12** | LG-12.1 | Chọn backend: `MemorySaver` (dev) vs `SqliteSaver` (path file). |
| | LG-12.2 | Truyền `thread_id` vào `configurable` khi `invoke`/`stream`. |
| | LG-12.3 | Kiểm tra resume conversation hai lượt liên tiếp. |
| **LG-13** | LG-13.1 | Gọi `graph.astream_events` hoặc `astream` với config checkpointer. |
| | LG-13.2 | Filter event theo tên node để log/debug. |
| | LG-13.3 | Middleware/contextVar gắn `correlation_id` vào log mỗi lần vào node. |
| **LG-14** | LG-14.1 | Danh sách field được phép log; mask SQL nếu policy. |
| | LG-14.2 | Đồng bộ header `X-Correlation-Id` Spring ↔ FastAPI. |

### Task 2 (tiếp) — Phân rã TASK-AG-* (Node nghiệp vụ)

| Task cha | Task nhỏ | Mô tả ngắn |
| :-- | :-- | :-- |
| **AG-01** | AG-01.1 | Prompt intent (tiếng Việt/Anh) + few-shot ngắn. |
| | AG-01.2 | Gắn LM-04 structured output; map kết quả → `state["intent"]`. |
| | AG-01.3 | Xử lý ambiguous: default an toàn (vd. `general_chat`). |
| **AG-02** | AG-02.1 | System prompt chat thường (không leak schema nội bộ). |
| | AG-02.2 | Ghép `messages` user + assistant trả lời vào state. |
| **AG-03** | AG-03.1 | Loader đọc file schema theo `schema_version` (path config). |
| | AG-03.2 | Mock file YAML/JSON nhỏ trong repo test. |
| | AG-03.3 | Prompt `gen_sql`: chỉ schema được phép + câu hỏi + `validation_feedback`. |
| **AG-04** | AG-04.1 | Prompt review + SQL + schema snippet. |
| | AG-04.2 | Parse output structured; nếu `ok=False` set feedback và route retry. |
| **AG-05** | AG-05.1 | Parser/phân tích statement: chỉ cho phép `SELECT`. |
| | AG-05.2 | Allowlist bảng/cột theo tenant (stub hoặc config). |
| | AG-05.3 | Bắt buộc `LIMIT` hoặc inject `LIMIT` an toàn (quyết định rõ). |
| | AG-05.4 | Deny DDL/DML keywords. |
| **AG-06** | AG-06.1 | Spike: Python SQLAlchemy/psycopg read-only URL. |
| | AG-06.2 | Hoặc HTTP client gọi Spring “run query” — contract JSON. |
| | AG-06.3 | Timeout + cancel query; không dùng connection pool không giới hạn. |
| **AG-07** | AG-07.1 | Giới hạn số dòng / bytes `query_result`. |
| | AG-07.2 | Kiểm tra empty vs lỗi nghiệp vụ tối thiểu; quyết định có retry `gen_sql` không. |

### Task 3 — Phân rã TASK-API-* (Spring / FastAPI)

| Task cha | Task nhỏ | Mô tả ngắn |
| :-- | :-- | :-- |
| **API-01** | API-01.1 | Schema request body: `message`, `thread_id?`, `schema_version?`, metadata. |
| | API-01.2 | Validate JWT/context do Spring truyền (hoặc shared secret service-to-service). |
| | API-01.3 | Build `configurable` + initial state từ request. |
| **API-02** | API-02.1 | Route POST đồng bộ `invoke` trả JSON `final_answer`. |
| | API-02.2 | Route GET/POST stream (SSE hoặc chunked) gọi graph stream. |
| | API-02.3 | Không trả lỗi raw từ LLM provider ra client; map sang mã ứng dụng. |

### Task 4 — Phân rã TASK-QA-* (Kiểm thử)

| Task cha | Task nhỏ | Mô tả ngắn |
| :-- | :-- | :-- |
| **QA-01** | QA-01.1 | Test `route_by_intent` với state giả. |
| | QA-01.2 | Mock LLM (fake responses) cho `gen_sql` / `sql_review`. |
| | QA-01.3 | Test retry: fail tại `validate_sql` lần 1–2, pass lần 3; và case hết 3 lần. |
| **QA-02** | QA-02.1 | E2E `general_chat` với LLM thật (flag integration). |
| | QA-02.2 | E2E `system_data` với SQLite in-memory + schema file fixture. |

---

## 7. Tóm tắt

- Đã bám **LangGraph** (state, subgraph SQL, `sql_review`, validate/retry cap 3, registry) theo `ai_chatbot_da_agent_v1.plan.md` và **vai trò stack** theo plan phân tích (Python orchestration, Spring cổng).  
- **Gemma 4** được gói qua **OpenAI-compatible** + env config; streaming và structured output là task bắt buộc kiểm chứng trên gateway thực tế.  
- **Multimodal** trong mẫu user là hướng mở rộng, không chặn v1 text-only.  
- **Mục 6** phân rã theo **Task 1–4**: task nhỏ có ID `.n` để treo sprint/issue tracker.
