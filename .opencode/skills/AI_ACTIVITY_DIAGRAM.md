# AI Activity Diagrams — Smart ERP

> Tài liệu mô tả chi tiết từng luồng xử lý AI: từ giao diện → Spring Boot → Python FastAPI (LangGraph) → Database → Phản hồi về giao diện.

---

## Mục lục

1. [AI Chat Stream (SSE)](#1-ai-chat-stream-sse)
2. [AI SQL Query (Describe → Generate → Execute → Response)](#2-ai-sql-query)
3. [AI Catalog Draft (Generate → Validate → Commit)](#3-ai-catalog-draft)
4. [AI Inventory Draft (Generate → Validate → Commit)](#4-ai-inventory-draft)
5. [AI Transcribe — Speech to Text (STT)](#5-ai-transcribe-stt)
6. [AI Synthesize — Text to Speech (TTS)](#6-ai-synthesize-tts)
7. [AI Domain Guard + Intent Classification](#7-domain-guard--intent)

---

## 1. AI Chat Stream (SSE)

### Overview
- **Mục đích**: Người dùng chat với AI, nhận phản hồi streaming qua Server-Sent Events (SSE). Hỗ trợ nhiều chế độ: chat thường, hỏi dữ liệu SQL, tạo biểu đồ, tạo bảng nhập catalog, tạo phiếu kho.
- **Actors**: User, Frontend (React), Spring Boot (Java), Python FastAPI (LangGraph), PostgreSQL
- **Protocol**: SSE (Server-Sent Events)
- **Endpoint**: `POST /api/v1/ai/chat/stream`

### Activity Flow

#### Step 1: Frontend gửi request
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `startAiChatPostStream()`
- **File UI**: `frontend/src/features/ai/pages/ChatBotPage.tsx` → `startAssistantStream()`
- **Xử lý**:
  - Lấy `accessToken` từ `sessionStorage`
  - Tạo `X-Correlation-Id` (UUID)
  - Build payload: `{ message, conversationId, interactionMode? }`
  - `fetch()` POST tới Spring (dev: `http://127.0.0.1:8080`, prod: `VITE_API_BASE_URL`)
  - Mở `ReadableStream` reader để đọc SSE chunk-by-chunk
- **Input**: User typed text + conversationId + interactionMode
- **Output**: HTTP POST request với Bearer token tới Spring

#### Step 2: Spring Controller nhận request
- **File**: `backend/.../ai/controller/AiChatRelayController.java` → `streamPost()`
- **Xử lý**:
  1. Tạo `SseEmitter` (timeout vô hạn `0L`)
  2. Validate `Authorization: Bearer ...` → nếu thiếu, gửi SSE `error` event rồi complete
  3. Extract `user_id`, `tenant_id` từ JWT claim
  4. Build JSON payload gửi Python:
     ```json
     {
       "message": "...",
       "metadata": { "user_id": "...", "tenant_id": "...", "thread_id": "...", "schema_version": "v1" },
       "options": { "interaction_mode": "..." }
     }
     ```
  5. Tạo `X-Correlation-Id` UUID mới
  6. Forward HTTP POST tới Python: `http://<python-base>/api/v1/ai/chat/stream`
     - Headers: `Authorization` (giữ nguyên Bearer), `X-Correlation-Id`, `Accept: text/event-stream`
     - Timeout: 5 phút
  7. Đọc SSE stream từ Python, parse `event:` + `data:` lines, re-emit lại tới browser qua `emitter.send()`
  8. Khi gặp `event: done` → `emitter.complete()`
- **Input**: JSON body + JWT
- **Output**: SSE stream tới browser (relay từ Python)
- **Branch cases**:
  - **Thiếu Bearer token** → SSE `error: "Thiếu Authorization Bearer."` → complete
  - **Python trả về HTTP error (4xx/5xx)** → SSE `error: "Python AI HTTP <code> ..."` → complete
  - **Connection timeout / Python không chạy** → SSE `error: <chi tiết lỗi>` → `completeWithError()`
  - **JSON build thất bại** → SSE `error: "Không thể dựng payload AI."` → complete

#### Step 3: Python FastAPI nhận request
- **File**: `ai_python/app/api/routes.py` → `stream_chat()`
- **Xử lý**:
  1. Validate JWT qua `_validate_auth()` (HS256 shared secret hoặc JWKS)
  2. Enforce identity context: so sánh `user_id`/`tenant_id` trong JWT với request metadata → 403 nếu không khớp
  3. Trả về `StreamingResponse` với generator `_iter_chat_sse_events()`
- **Input**: JSON body + Bearer token + X-Correlation-Id
- **Output**: SSE stream generator

#### Step 4: Python LangGraph — Main Graph Pipeline
- **File**: `ai_python/app/graph/main_graph.py` → `build_main_graph()`
- **Xử lý** (theo thứ tự node):

| Node | File | Xử lý | Output cho node tiếp theo |
|------|------|-------|---------------------------|
| `domain_guard` | `nodes/domain_guard.py` | Kiểm tra query có thuộc ERP domain không. Nếu lạc đề → trả lời từ chối + END | `continue` hoặc `stop` |
| `context_compact` | `nodes/context_compact.py` | Quản lý context window, trim history nếu vượt quá token limit | State với messages đã compact |
| `classify_intent` | `nodes/intent.py` | Phân loại intent: `chat_normal`, `sql_branch`, `agent_idea`, `catalog_draft_branch`, `inventory_draft_branch` | `intent` string → route tới nhánh phù hợp |

- **Branch cases tại `classify_intent`**:
  - `chat_normal` → Node `chat_normal` → END (chat trò chuyện thường)
  - `sql_branch` → Subgraph SQL (xem mục 2)
  - `agent_idea` → Node `agent_idea` → `sql_branch` (tạo biểu đồ)
  - `catalog_draft_branch` → Subgraph Catalog Draft (xem mục 3)
  - `inventory_draft_branch` → Subgraph Inventory Draft (xem mục 4)

#### Step 5: Python SSE Event Emission
- **File**: `ai_python/app/api/routes.py` → `_iter_chat_sse_events()`
- **Xử lý**: Lặp qua từng chunk từ `runtime.stream()`, phát hiện loại sự kiện và yield SSE event:

| SSE Event | Trigger | Payload |
|-----------|---------|---------|
| `progress` | Node emit `progress_text` | Text trạng thái (VD: "Đang truy vấn dữ liệu...") |
| `clarify` | Domain guard cần làm rõ | JSON `{ questions: [...], assistantIntro: "..." }` |
| `chart` | SQL branch sinh biểu đồ | Vega-Lite JSON spec |
| `draft` | Catalog draft branch | `{ draftId, entityType, rows: [...], columns: [...] }` |
| `inventory_draft` | Inventory draft branch | `{ draftId, entityType, receipt: {...}, lines: [...] }` |
| `data_table` | SQL query kết quả dạng bảng | `{ columns: [...], rows: [...], rowCount }` |
| `delta` | Text streaming (incremental) | String delta (phần mới của final_answer) |
| `error` | Lỗi không recover được | Error message (Vietnamese) |
| `done` | Graph hoàn thành | Empty string |

- **Input**: Chunk từ LangGraph runtime
- **Output**: SSE text events stream

#### Step 6: Frontend nhận và render SSE events
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `startAiChatPostStream()`
- **File UI**: `frontend/src/features/ai/pages/ChatBotPage.tsx`
- **Xử lý**:
  - Parse SSE block (`event:` + `data:`)
  - `onDelta` → Append text vào assistant message (dùng `appendDeltaSmart()` để xử lý khoảng cách thông minh)
  - `onChart` → Gắn `chartSpec` vào message metadata → render `AiChatChartCard`
  - `onDraft` → Gắn `draftTable` → render `AiChatDraftTableCard`
  - `onInventoryDraft` → Gắn `inventoryDraft` → render `AiChatReceiptDraftCard`
  - `onDataTable` → Gắn `queryTable` → render `AiChatQueryTableCard`
  - `onClarify` → Gắn `domainClarify` → render `AiChatClarifyCard`
  - `onProgress` → Hiển thị progress bar text
  - `onDone` → Ẩn typing indicator
  - `onError` → Hiển thị lỗi trong message bubble
- **Input**: SSE events từ Spring
- **Output**: UI update (text, chart, table, draft card)

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `appendDeltaSmart()` | `ChatBotPage.tsx` | Ghép delta text thông minh: xử lý dấu câu, khoảng trắng giữa từ, không thêm space trong số |
| `parseSseBlock()` | `aiChatSse.ts` | Parse SSE block text thành `{ event, data }` |
| `resolveAiChatStreamUrl()` | `aiChatSse.ts` | Resolve URL: dev → thẳng Spring 8080, prod → `VITE_API_BASE_URL` |
| `normalizePythonBaseUrl()` | `AiChatRelayController.java` | Chuẩn hóa Python base URL (thêm `http://`, trim slash) |
| `relayErrorDetail()` | `AiChatRelayController.java` | Extract error message từ exception (fallback nếu message null) |
| `should_emit_stream_error()` | `routes.py` | Quyết định có emit SSE `error` không (skip nếu đã có `final_answer`) |

---

## 2. AI SQL Query

### Overview
- **Mục đích**: AI nhận câu hỏi tự nhiên, sinh SQL, thực thi read-only, trả về bảng dữ liệu + tóm tắt + (tuỳ chọn) biểu đồ.
- **Actors**: User, Frontend, Spring, Python LangGraph, PostgreSQL
- **Trigger**: Intent = `sql_branch` hoặc `agent_idea` (cho biểu đồ)

### Activity Flow

#### Step 1: Intent Classification → SQL Branch
- **File**: `ai_python/app/graph/nodes/intent.py` → `make_intent_node()`
- **Xử lý**: LLM phân loại → `route_after_intent()` route tới `sql_branch`
- **Output**: `state["intent"] = "sql_branch"`

#### Step 2: SQL Subgraph — Schema Explore (tuỳ chọn)
- **File**: `ai_python/app/graph/nodes/schema_explore.py` → `make_schema_explore_node()`
- **Xử lý**:
  - Nếu chưa có schema context → gọi Spring `POST /api/v1/ai/db/sql/describe`
  - **Spring file**: `backend/.../ai/dbreadonly/AiDbReadonlyController.java` → `sqlDescribe()`
  - **Spring service**: `AiDbReadonlyService.java` → `describe()` — đọc metadata từ bảng allowlisted + `ai_table_description`
  - Python nhận column names, types, comments
- **Input**: Table names cần explore
- **Output**: Schema metadata gán vào state
- **Branch cases**:
  - **Schema load thất bại** → Route tới `gen_sql` luôn (fallback)
  - **Table không trong allowlist** → Spring trả về 400

#### Step 3: SQL Subgraph — Generate SQL
- **File**: `ai_python/app/graph/nodes/sql_pipeline.py` → `make_gen_sql_node()`
- **Xử lý**:
  - LLM sinh SQL từ natural language + schema context + conversation history
  - Prompt template: `ai_python/app/graph/sql_prompts.py`
  - Áp dụng enum literals, column labels tiếng Việt
- **Input**: User query + schema + history
- **Output**: `state["sql_query"] = "SELECT ..."`
- **Branch cases**:
  - **Quá số lần thử tối đa** → `fail_max_attempts` → END

#### Step 4: SQL Subgraph — SQL Review (tuỳ chọn)
- **File**: `ai_python/app/graph/nodes/sql_pipeline.py` → `make_sql_review_node()`
- **Xử lý**: LLM review SQL vừa sinh, kiểm tra logic, join đúng không, filter có hợp lý
- **Output**: `state["sql_review_passed"] = true/false`
- **Branch cases**:
  - **Review fail** → Quay lại `gen_sql` (retry)
  - **Quá số lần retry** → `fail_max_attempts` → END

#### Step 5: SQL Subgraph — Validate SQL (Safety)
- **File**: `ai_python/app/graph/nodes/sql_pipeline.py` → `make_validate_sql_node()`
- **Xử lý**:
  - Kiểm tra SQL chỉ chứa SELECT (không DML/DDL)
  - **File**: `ai_python/app/graph/sql_safety.py` — safety rules
  - **File**: `ai_python/app/graph/sql_allowlist.py` — kiểm tra table trong allowlist
- **Input**: SQL query
- **Output**: `valid = true/false` + error message nếu fail
- **Branch cases**:
  - **SQL không an toàn** (INSERT/UPDATE/DELETE/DROP) → Quay lại `gen_sql`
  - **Table không trong allowlist** → Quay lại `gen_sql`
  - **Quá số lần retry** → `fail_max_attempts` → END

#### Step 6: SQL Subgraph — Execute SQL
- **File**: `ai_python/app/graph/nodes/sql_pipeline.py` → `make_execute_sql_node()`
- **Xử lý**:
  - Gọi Spring `POST /api/v1/ai/db/sql/query-readonly` (template-based) hoặc `/sql/query-readonly-raw` (raw SQL)
  - **Spring file**: `AiDbReadonlyController.java` → `sqlQueryReadonly()` hoặc `sqlQueryReadonlyRaw()`
  - **Spring service**: `AiDbReadonlyService.java` → `queryReadonly()` — thực thi qua JDBC, giới hạn max rows
  - Python nhận kết quả: `{ columns: [...], rows: [...] }`
- **Input**: SQL query
- **Output**: Query result rows gán vào state
- **Branch cases**:
  - **SQL execution error** → Quay lại `gen_sql` để sửa
  - **Quá số lần retry** → `fail_max_attempts` → END

#### Step 7: SQL Subgraph — Validate Result
- **File**: `ai_python/app/graph/nodes/sql_pipeline.py` → `make_validate_result_node()`
- **Xử lý**: Kiểm tra kết quả có dữ liệu không, format có đúng không
- **Branch cases**:
  - **Kết quả rỗng / lỗi** → Quay lại `gen_sql`
  - **OK** → Route tới `chart_readiness` hoặc `done`

#### Step 8: SQL Subgraph — Chart Readiness (tuỳ chọn)
- **File**: `ai_python/app/graph/nodes/chart_readiness.py` → `make_chart_readiness_node()`
- **Xử lý**: Kiểm tra dữ liệu có phù hợp để vẽ biểu đồ không (số cột, loại dữ liệu)
- **Branch cases**:
  - **Có thể vẽ chart** → `done` (SQL subgraph kết thúc, main graph route tới `agent_chart`)
  - **Không cần chart** → `done`

#### Step 9: Main Graph — Route After SQL Branch
- **File**: `ai_python/app/graph/nodes/query_table.py` → `route_after_sql_branch()`
- **Xử lý**: Quyết định output type dựa trên intent + data:
  - `agent_chart` → Vẽ biểu đồ
  - `emit_query_table` → Trả bảng dữ liệu
  - `summarize_answer` → Tóm tắt bằng text
  - `stop_clarify` → Hỏi lại user

#### Step 10a: Emit Query Table
- **File**: `ai_python/app/graph/nodes/query_table.py` → `make_emit_query_table_node()`
- **Xử lý**:
  - Format kết quả SQL thành `query_table_sse` payload
  - Áp dụng Vietnamese column labels (`column_labels_vi.py`)
  - Format datetime hiển thị (`datetime_display.py`)
  - Emit SSE `data_table` event
- **Output**: SSE `data_table` → Frontend render `AiChatQueryTableCard`

#### Step 10b: Generate Chart (nếu route tới `agent_chart`)
- **File**: `ai_python/app/graph/nodes/chart_report.py` → `make_agent_chart_node()`
- **Xử lý**:
  - LLM sinh Vega-Lite chart spec từ dữ liệu SQL
  - Merge với schema để确定 chart type (`chart_schema_merge.py`)
  - Profile dữ liệu để chọn chart phù hợp (`chart_data_profile.py`)
- **Output**: `state["chart_spec_final"]` → Emit SSE `chart` event

#### Step 11: Chart Review
- **File**: `ai_python/app/graph/nodes/chart_report.py` → `make_agent_review_node()`
- **Xử lý**: LLM review chart spec, kiểm tra tính hợp lý
- **Output**: Chart spec đã review → END

#### Step 12: Summarize Answer
- **File**: `ai_python/app/graph/nodes/summarize.py` → `make_summarize_answer_node()`
- **Xử lý**: LLM tóm tắt kết quả SQL thành văn bản tiếng Việt
- **Output**: `state["final_answer"]` → Emit SSE `delta` events

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `make_gen_sql_node()` | `sql_pipeline.py` | Tạo node LLM sinh SQL từ natural language |
| `make_validate_sql_node()` | `sql_pipeline.py` | Tạo node kiểm tra SQL safety (chỉ SELECT, allowlist) |
| `make_execute_sql_node()` | `sql_pipeline.py` | Tạo node thực thi SQL qua Spring HTTP |
| `is_safe_sql()` | `sql_safety.py` | Kiểm tra SQL không chứa DML/DDL/dangerous patterns |
| `check_table_allowlist()` | `sql_allowlist.py` | Kiểm tra tất cả tables trong query đều được phép |
| `describe_table()` | `spring_describe_client.py` | HTTP client gọi Spring `/api/v1/ai/db/sql/describe` |
| `apply_column_labels_vi()` | `column_labels_vi.py` | Ánh xạ column names → nhãn tiếng Việt hiển thị |
| `format_datetime_display()` | `datetime_display.py` | Format datetime values cho hiển thị UI |

---

## 3. AI Catalog Draft

### Overview
- **Mục đích**: AI sinh nháp dữ liệu catalog (product, category, supplier, customer) → user chỉnh sửa trên UI → commit vào database thật.
- **Actors**: User, Frontend, Spring, Python LangGraph, PostgreSQL
- **Trigger**: Intent = `catalog_draft_branch` hoặc `interaction_mode = "catalog_draft"`

### Activity Flow

#### Step 1: Frontend gửi chat request với interaction_mode
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `startAiChatPostStream()`
- **Xử lý**: Gửi `{ message, conversationId, interactionMode: "catalog_draft" }` tới Spring
- **Output**: HTTP POST tới Spring

#### Step 2: Spring Relay tới Python
- **File**: `backend/.../ai/controller/AiChatRelayController.java` → `streamPost()`
- **Xử lý**: Như mục 1, Step 2 — relay SSE tới Python với `options.interaction_mode = "catalog_draft"`
- **Output**: HTTP POST tới Python

#### Step 3: Python — Catalog Draft Subgraph
- **File**: `ai_python/app/graph/catalog_draft_subgraph.py` → `build_catalog_draft_subgraph()`

##### Step 3.1: Classify Catalog Entity
- **File**: `ai_python/app/graph/nodes/catalog_draft.py` → `make_classify_catalog_entity_node()`
- **Xử lý**: LLM xác định entity type từ query: `product`, `category`, `supplier`, `customer`
- **Output**: `state["catalog_entity_type"]`

##### Step 3.2: Resolve Catalog Draft (Entity Resolution)
- **File**: `ai_python/app/graph/nodes/draft_resolve.py` → `make_resolve_catalog_draft_node()`
- **Xử lý**:
  - Trích xuất thông tin từ query (tên, mô tả, giá, v.v.)
  - Resolve references: tìm category_id, supplier_id từ tên
  - Gọi Spring `POST /api/v1/ai/db/sql/query-readonly-raw` để tra cứu
  - **File helper**: `draft_entity_resolution.py`, `draft_reference_messages.py`
- **Output**: Resolved entities với FK IDs
- **Branch cases**:
  - **Không resolve được reference** → `stop` → END (emit clarify message)
  - **Thiếu thông tin bắt buộc** → `stop` → END

##### Step 3.3: Generate Catalog Draft
- **File**: `ai_python/app/graph/nodes/catalog_draft.py` → `make_generate_catalog_draft_node()`
- **Xử lý**:
  - LLM sinh draft data theo schema (`catalog_draft_schema.py`)
  - Build payload: `{ entity_type, rows: [{...}], columns: [...] }`
  - Validate structure
- **Output**: `state["catalog_draft_payload"]`
- **Branch cases**:
  - **Generate thất bại** → `stop` → END

##### Step 3.4: Persist Catalog Draft to Spring
- **File**: `ai_python/app/graph/nodes/catalog_draft.py` → `make_persist_catalog_draft_node()`
- **Xử lý**:
  - HTTP POST tới Spring `POST /api/v1/ai/catalog-drafts`
  - **Spring file**: `AiCatalogDraftController.java` → `create()`
  - **Spring service**: `AiCatalogDraftService.java` → `create()`
    - Lưu draft vào bảng `ai_catalog_draft` với `status = "draft"`
    - Payload JSONB chứa toàn bộ rows
  - Python nhận response: `{ id, draftId, ... }`
  - Emit SSE `draft` event với `draftId`
- **Input**: Draft payload
- **Output**: SSE `draft` event → Frontend nhận draftId

#### Step 4: Frontend nhận và hiển thị Draft Table
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `onDraft` callback
- **File UI**: `frontend/src/features/ai/components/AiChatDraftTableCard.tsx`
- **Xử lý**:
  - Parse `draft` SSE event → lấy `draftId`, `rows`, `columns`
  - Render bảng editable (HITL — Human In The Loop)
  - User chỉnh sửa rows trên UI

#### Step 5: User chỉnh sửa draft trên UI
- **File**: `frontend/src/features/ai/api/aiCatalogDraftApi.ts`
- **Xử lý**:
  - User edit cells → Frontend track changes
  - **PATCH** `/api/v1/ai/catalog-drafts/{id}` → Spring cập nhật draft payload
  - **POST** `/api/v1/ai/catalog-drafts/validate` → Spring validate FK references
    - **Spring service**: `AiCatalogDraftService.java` → `validateReferences()`
    - **File helper**: `CatalogDraftReferenceValidator.java` — kiểm tra category_id, supplier_id tồn tại
  - **POST** `/api/v1/ai/catalog-drafts/{id}/commit` → Spring commit draft vào catalog thật
    - **Spring service**: `AiCatalogDraftService.java` → `commit()`
    - **File helper**: `AiCatalogDraftCommitter.java` — gọi ProductService, CategoryService, v.v. để tạo records thật
    - Cập nhật `ai_catalog_draft.status = "committed"`, lưu `commit_result`
- **Branch cases**:
  - **Validate fail** → Hiển thị lỗi, user sửa lại
  - **Commit fail** (FK violation, duplicate code) → Hiển thị lỗi, rollback
  - **Thành công** → Hiển thị kết quả commit (số records tạo thành công)

#### Step 6: Spring trả kết quả commit về Frontend
- **Xử lý**: Response `{ success: true, data: { outcomes: [...] }, message: "Đã xử lý commit" }`
- **Output**: Frontend hiển thị kết quả (VD: "Đã tạo 5 sản phẩm, 2 danh mục")

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `make_classify_catalog_entity_node()` | `catalog_draft.py` | LLM phân loại entity type (product/category/supplier/customer) |
| `make_resolve_catalog_draft_node()` | `draft_resolve.py` | Resolve entity references (tên → ID) qua Spring SQL query |
| `make_generate_catalog_draft_node()` | `catalog_draft.py` | LLM sinh draft data theo schema |
| `make_persist_catalog_draft_node()` | `catalog_draft.py` | HTTP POST draft tới Spring `ai_catalog_draft` table |
| `validateReferences()` | `CatalogDraftReferenceValidator.java` | Kiểm tra FK references tồn tại trong DB |
| `commit()` | `AiCatalogDraftCommitter.java` | Commit draft → gọi catalog services tạo records thật |
| `spring_catalog_draft_client.py` | Python HTTP client | Gọi Spring catalog draft API (create, validate, patch) |

---

## 4. AI Inventory Draft

### Overview
- **Mục đích**: AI sinh nháp chứng từ kho (stock receipt) → user chỉnh sửa → commit tạo phiếu nhập kho thật.
- **Actors**: User, Frontend, Spring, Python LangGraph, PostgreSQL
- **Trigger**: Intent = `inventory_draft_branch` hoặc `interaction_mode = "inventory_draft"`

### Activity Flow

#### Step 1: Frontend gửi chat request với interaction_mode
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `startAiChatPostStream()`
- **Xử lý**: Gửi `{ message, conversationId, interactionMode: "inventory_draft" }` tới Spring
- **Output**: HTTP POST tới Spring

#### Step 2: Spring Relay tới Python
- **File**: `backend/.../ai/controller/AiChatRelayController.java` → `streamPost()`
- **Xử lý**: Relay SSE tới Python với `options.interaction_mode = "inventory_draft"`
- **Output**: HTTP POST tới Python

#### Step 3: Python — Inventory Draft Subgraph
- **File**: `ai_python/app/graph/inventory_draft_subgraph.py` → `build_inventory_draft_subgraph()`

##### Step 3.1: Classify Inventory Document
- **File**: `ai_python/app/graph/nodes/inventory_draft.py` → `make_classify_inventory_doc_node()`
- **Xử lý**: LLM xác định loại chứng từ: `stock_receipt` (hiện tại chỉ hỗ trợ phiếu nhập)
- **Output**: `state["inventory_entity_type"]`

##### Step 3.2: Resolve Inventory Draft (Entity Resolution)
- **File**: `ai_python/app/graph/nodes/draft_resolve.py` → `make_resolve_inventory_draft_node()`
- **Xử lý**:
  - Trích xuất thông tin: supplier name, product names, quantities, prices
  - Resolve references: tìm supplier_id, product_id từ tên
  - Gọi Spring SQL query để tra cứu
  - **File helper**: `draft_entity_resolution.py`, `draft_reference_messages.py`, `inventory_draft_schema.py`
- **Output**: Resolved entities với FK IDs
- **Branch cases**:
  - **Không resolve được supplier/product** → `stop` → END (emit clarify)
  - **Thiếu thông tin bắt buộc** (quantity, price) → `stop` → END

##### Step 3.3: Generate Inventory Draft
- **File**: `ai_python/app/graph/nodes/inventory_draft.py` → `make_generate_inventory_draft_node()`
- **Xử lý**:
  - LLM sinh draft theo schema (`inventory_draft_schema.py`)
  - Build payload: `{ entity_type: "stock_receipt", receipt: { supplierId, note, ... }, lines: [{ productId, quantity, unitPrice }] }`
- **Output**: `state["inventory_draft_payload"]`

##### Step 3.4: Persist Inventory Draft to Spring
- **File**: `ai_python/app/graph/nodes/inventory_draft.py` → `make_persist_inventory_draft_node()`
- **Xử lý**:
  - HTTP POST tới Spring `POST /api/v1/ai/inventory-drafts`
  - **Spring file**: `AiInventoryDraftController.java` → `create()`
  - **Spring service**: `AiInventoryDraftService.java` → `create()`
    - Lưu draft vào bảng `ai_inventory_draft` với `status = "draft"`
    - Payload JSONB chứa receipt + lines
  - Python nhận response: `{ id, draftId, ... }`
  - Emit SSE `inventory_draft` event với `draftId`
- **Output**: SSE `inventory_draft` event → Frontend nhận draftId

#### Step 4: Frontend nhận và hiển thị Receipt Draft
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `onInventoryDraft` callback
- **File UI**: `frontend/src/features/ai/components/AiChatReceiptDraftCard.tsx`
- **Xử lý**:
  - Parse `inventory_draft` SSE event
  - Render form phiếu nhập editable (supplier, lines, quantities, prices)
  - User chỉnh sửa trên UI

#### Step 5: User chỉnh sửa và Commit
- **File**: `frontend/src/features/ai/api/aiInventoryDraftApi.ts`
- **Xử lý**:
  - **PATCH** `/api/v1/ai/inventory-drafts/{id}` → Cập nhật draft
  - **POST** `/api/v1/ai/inventory-drafts/validate` → Validate FK references
    - **Spring service**: `AiInventoryDraftService.java` → `validateReferences()`
    - **File helper**: `InventoryDraftFkResolver.java` — resolve supplier/product IDs
  - **POST** `/api/v1/ai/inventory-drafts/{id}/commit` → Commit tạo stock receipt thật
    - **Spring service**: `AiInventoryDraftService.java` → `commit()`
    - **File helper**: `AiInventoryDraftCommitter.java` — gọi `StockReceiptLifecycleService.create()` tạo phiếu nhập + cập nhật inventory
    - Cập nhật `ai_inventory_draft.status = "committed"`, lưu `commit_result`
- **Branch cases**:
  - **Validate fail** → Hiển thị lỗi (VD: "Không tìm thấy sản phẩm 'ABC'")
  - **Commit fail** → Hiển thị lỗi, rollback
  - **Thành công** → Hiển thị kết quả ("Đã tạo phiếu nhập SP-001, cập nhật tồn kho 5 sản phẩm")

#### Step 6: Spring trả kết quả commit về Frontend
- **Output**: Response `{ success: true, data: { receiptId, updatedInventory: [...] }, message: "Đã xử lý commit" }`

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `make_classify_inventory_doc_node()` | `inventory_draft.py` | LLM phân loại chứng từ kho |
| `make_resolve_inventory_draft_node()` | `draft_resolve.py` | Resolve supplier/product references |
| `make_generate_inventory_draft_node()` | `inventory_draft.py` | LLM sinh draft phiếu nhập |
| `make_persist_inventory_draft_node()` | `inventory_draft.py` | HTTP POST draft tới Spring |
| `validateReferences()` | `AiInventoryDraftService.java` | Validate FK references cho inventory draft |
| `commit()` | `AiInventoryDraftCommitter.java` | Commit draft → tạo stock receipt thật + update inventory |
| `spring_inventory_draft_client.py` | Python HTTP client | Gọi Spring inventory draft API |

---

## 5. AI Transcribe (STT)

### Overview
- **Mục đích**: Chuyển giọng nói thành văn bản (Speech-to-Text) qua FPT Whisper.
- **Actors**: User, Frontend, Spring, Python FastAPI, FPT Whisper API
- **Endpoint**: `POST /api/v1/ai/chat/transcribe`

### Activity Flow

#### Step 1: Frontend ghi âm và gửi audio
- **File**: `frontend/src/features/ai/pages/ChatBotPage.tsx` → `toggleRecording()`
- **Xử lý**:
  1. Request microphone permission (`getUserMedia`)
  2. Tạo `MediaRecorder` (mimeType: `audio/webm;codecs=opus`)
  3. User nhấn giữ mic → ghi âm
  4. User thả → `recorder.stop()`
  5. `onstop` callback:
     - Convert webm → wav qua `convertToWav()` (`audioUtils.ts`)
     - Kiểm tra: duration >= 1s, peak amplitude đủ lớn
     - Nếu không đạt → hiển thị lỗi, không gửi
  6. Gọi `transcribeAudio(wavBlob, { language: "vi" })`
- **Input**: Audio recording từ microphone
- **Output**: WAV Blob

#### Step 2: Frontend gửi audio tới Spring
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `transcribeAudio()`
- **Xử lý**:
  - Tạo `FormData` với `file` (WAV Blob) + `language` ("vi")
  - `fetch()` POST tới `/api/v1/ai/chat/transcribe`
  - Headers: `Authorization: Bearer <token>`, `X-Correlation-Id`
- **Input**: WAV Blob + language
- **Output**: HTTP multipart POST tới Spring

#### Step 3: Spring Relay tới Python
- **File**: `backend/.../ai/controller/AiChatRelayController.java` → `transcribePost()`
- **Xử lý**:
  1. Validate Bearer token → 401 nếu thiếu
  2. Validate file không rỗng → 400 nếu thiếu
  3. Build multipart body thủ công (`buildTranscribeMultipart()`)
  4. Forward POST tới Python `POST /api/v1/ai/chat/transcribe`
     - Timeout: 120 giây
     - Headers: `Authorization`, `X-Correlation-Id`, `Content-Type: multipart/form-data`
  5. Trả response từ Python về frontend
- **Input**: Multipart form (audio file + language)
- **Output**: HTTP response từ Python (JSON: `{ transcript, language, correlation_id }`)
- **Branch cases**:
  - **Thiếu Bearer** → 401 `{ error: { code: "AI_AUTH_INVALID", message: "Thiếu Authorization Bearer." } }`
  - **Thiếu file** → 400 `{ error: { code: "AI_VALIDATION_FAILED", message: "Thiếu file audio." } }`
  - **Python không phản hồi** → 502 `{ error: { code: "AI_RELAY_ERROR", message: "<chi tiết>" } }`

#### Step 4: Python STT Service xử lý
- **File**: `ai_python/app/api/routes.py` → `transcribe_audio()`
- **Xử lý**:
  1. Validate JWT
  2. Kiểm tra STT service available → 503 nếu không
  3. Đọc audio bytes từ upload
  4. Gọi `stt.transcribe(audio_bytes, filename, content_type, language)`
     - **File**: `ai_python/app/stt/service.py` → `SttService`
     - **Implementation**: `ai_python/app/stt/fpt_whisper.py` → `FptWhisperStt`
       - Gửi audio tới FPT Whisper API
       - Nhận transcript text
  5. Trả về `TranscribeResponse { transcript, language, correlation_id }`
- **Input**: Audio bytes + language
- **Output**: JSON `{ transcript: "...", language: "vi" }`
- **Branch cases**:
  - **STT không khả dụng** → 503 `{ code: "AI_STT_UNAVAILABLE" }`
  - **Audio validation fail** → 400 `{ code: "AI_STT_VALIDATION" }`
  - **STT provider error** → 502 `{ code: "AI_STT_GATEWAY_ERROR" }`

#### Step 5: Frontend nhận transcript và gửi chat
- **File**: `frontend/src/features/ai/pages/ChatBotPage.tsx` → `toggleRecording()` → `onstop`
- **Xử lý**:
  - Nhận `{ transcript }` từ response
  - Gọi `handleSend(transcript, "voice", { voiceUrl })`
  - Transcript được hiển thị như user message type "voice"
  - Trigger `startAssistantStream(transcript)` → AI xử lý như chat thường
- **Input**: Transcript text
- **Output**: Voice message trong chat + AI reply stream

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `convertToWav()` | `audioUtils.ts` | Convert webm/opus → WAV, tính duration + peak amplitude |
| `transcribeAudio()` | `aiChatSse.ts` | Gửi audio multipart tới Spring, nhận transcript |
| `buildTranscribeMultipart()` | `AiChatRelayController.java` | Build multipart form body thủ công để relay |
| `transcribe()` | `fpt_whisper.py` | Gửi audio tới FPT Whisper API, nhận transcript |
| `get_stt_service()` | `stt/factory.py` | Factory tạo STT service instance (FPT Whisper hoặc mock) |

---

## 6. AI Synthesize (TTS)

### Overview
- **Mục đích**: Chuyển văn bản thành giọng nói (Text-to-Speech) qua FPT VITS.
- **Actors**: User, Frontend, Spring, Python FastAPI, FPT VITS API
- **Endpoint**: `POST /api/v1/ai/chat/synthesize`

### Activity Flow

#### Step 1: Frontend trigger TTS
- **File**: `frontend/src/features/ai/hooks/useTextToSpeech.ts` → `speak()`
- **File UI**: `frontend/src/features/ai/pages/ChatBotPage.tsx` → `handleSpeak()`
- **Xử lý**:
  - User nhấn nút Volume2 trên message
  - Gọi `synthesizeSpeech(msg.content, { voice })` 
- **Input**: Text content của message
- **Output**: Gọi TTS API

#### Step 2: Frontend gửi request tới Spring
- **File**: `frontend/src/features/ai/api/aiChatSse.ts` → `synthesizeSpeech()`
- **Xử lý**:
  - Build JSON body: `{ text: "...", voice?: "..." }`
  - `fetch()` POST tới `/api/v1/ai/chat/synthesize`
  - Headers: `Content-Type: application/json`, `Authorization: Bearer <token>`, `X-Correlation-Id`
- **Input**: JSON body
- **Output**: HTTP POST tới Spring

#### Step 3: Spring Relay tới Python
- **File**: `backend/.../ai/controller/AiChatRelayController.java` → `synthesizePost()`
- **Xử lý**:
  1. Validate Bearer token → 401 nếu thiếu
  2. Validate text không rỗng → 400 nếu thiếu
  3. Build JSON payload: `{ text, voice? }`
  4. Forward POST tới Python `POST /api/v1/ai/chat/synthesize`
     - Timeout: 120 giây
     - Headers: `Authorization`, `X-Correlation-Id`, `Content-Type: application/json`
  5. Nhận response bytes (audio/wav) từ Python
  6. Trả về `ResponseEntity<byte[]>` với `Content-Type: audio/wav`
- **Input**: JSON `{ text, voice }`
- **Output**: Audio WAV bytes
- **Branch cases**:
  - **Thiếu Bearer** → 401
  - **Thiếu text** → 400 `{ code: "AI_VALIDATION_FAILED", message: "Thiếu nội dung text." }`
  - **Python không phản hồi** → 502 `{ code: "AI_RELAY_ERROR" }`

#### Step 4: Python TTS Service xử lý
- **File**: `ai_python/app/api/routes.py` → `synthesize_speech()`
- **Xử lý**:
  1. Validate JWT
  2. Kiểm tra TTS service available → 503 nếu không
  3. Gọi `tts.synthesize(text, voice=voice)`
     - **File**: `ai_python/app/tts/service.py` → `TtsService`
     - **Implementation**: `ai_python/app/tts/fpt_vits.py` → `FptVitsTts`
       - Gửi text tới FPT VITS API
       - Nhận audio WAV bytes
  4. Trả về `Response(content=audio_bytes, media_type="audio/wav")`
- **Input**: Text + voice
- **Output**: WAV audio bytes
- **Branch cases**:
  - **TTS không khả dụng** → 503 `{ code: "AI_TTS_UNAVAILABLE" }`
  - **Text validation fail** → 400 `{ code: "AI_TTS_VALIDATION" }`
  - **TTS provider error** → 502 `{ code: "AI_TTS_GATEWAY_ERROR" }`
  - **Audio rỗng** → 502 `{ code: "AI_TTS_EMPTY_AUDIO" }`

#### Step 5: Frontend nhận audio và phát
- **File**: `frontend/src/features/ai/hooks/useTextToSpeech.ts` → `speak()`
- **Xử lý**:
  - Nhận WAV Blob từ response
  - Tạo `URL.createObjectURL(blob)`
  - Phát qua `new Audio(url).play()`
  - Khi dừng/hoàn thành → cleanup URL
- **Input**: WAV Blob
- **Output**: Audio playback trong browser

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `synthesizeSpeech()` | `aiChatSse.ts` | Gửi text tới Spring, nhận WAV Blob |
| `speak()` | `useTextToSpeech.ts` | Wrapper: gọi API → tạo Audio → play |
| `synthesize()` | `fpt_vits.py` | Gửi text tới FPT VITS API, nhận WAV bytes |
| `get_tts_service()` | `tts/factory.py` | Factory tạo TTS service instance |

---

## 7. Domain Guard + Intent Classification

### Overview
- **Mục đích**: Kiểm tra query có thuộc ERP domain không, nếu không thì từ chối. Sau đó phân loại intent để route đúng nhánh xử lý.
- **Vị trí**: Luôn chạy đầu tiên trong LangGraph pipeline (trước mọi nhánh).
- **Actors**: User, Python LangGraph (LLM)

### Activity Flow

#### Step 1: Domain Guard
- **File**: `ai_python/app/graph/nodes/domain_guard.py` → `make_domain_guard_node()`
- **Xử lý**:
  1. Lấy user query từ state
  2. LLM kiểm tra query có liên quan đến ERP không (inventory, sales, finance, products, customers, suppliers, v.v.)
  3. Nếu **trong domain** → `route_after_domain_guard()` → `continue` → node tiếp theo (`context_compact`)
  4. Nếu **ngoài domain** → `route_after_domain_guard()` → `stop` → END
     - Emit SSE `clarify` event với message từ chối + gợi ý câu hỏi ERP phù hợp
     - **File helper**: `erp_guide/` — retrieve/format ERP context cho gợi ý
- **Input**: User query
- **Output**: `continue` hoặc `stop` + clarify SSE event
- **Branch cases**:
  - **Trong domain** → Tiếp tục pipeline
  - **Ngoài domain** → Từ chối + gợi ý → END
  - **Không rõ** → Clarify questions → END

#### Step 2: Context Compact
- **File**: `ai_python/app/graph/nodes/context_compact.py` → `make_context_compact_node()`
- **Xử lý**:
  - Kiểm tra tổng tokens trong conversation history
  - Nếu vượt quá limit → trim old messages, giữ system prompt + recent messages
  - Giữ lại draft/chart context nếu có
- **Input**: Full conversation history
- **Output**: Compacted messages list

#### Step 3: Intent Classification
- **File**: `ai_python/app/graph/nodes/intent.py` → `make_intent_node()`
- **Xử lý**:
  1. LLM phân loại query thành intent:
     - `chat_normal` — Trò chuyện thường (VD: "Xin chào", "Cảm ơn")
     - `sql_branch` — Hỏi dữ liệu (VD: "Tổng doanh thu tháng này?", "Sản phẩm nào bán chạy?")
     - `agent_idea` — Yêu cầu biểu đồ (VD: "Vẽ biểu đồ doanh thu theo tháng")
     - `catalog_draft_branch` — Tạo dữ liệu catalog (VD: "Tạo danh sách 10 sản phẩm mới")
     - `inventory_draft_branch` — Tạo chứng từ kho (VD: "Tạo phiếu nhập kho cho supplier ABC")
  2. `route_after_intent()` route tới node/subgraph tương ứng
- **Input**: User query + conversation context
- **Output**: `intent` string → route decision
- **Branch cases**:
  - **Không rõ intent** → Route tới `chat_normal` (fallback an toàn)
  - **Multiple intents** → Ưu tiên: `catalog_draft` > `inventory_draft` > `sql_branch` > `chat_normal`

### Helper Functions Quan Trọng

| Hàm | File | Mô tả |
|-----|------|-------|
| `make_domain_guard_node()` | `domain_guard.py` | Tạo node LLM kiểm tra ERP domain |
| `route_after_domain_guard()` | `domain_guard.py` | Quyết định continue/stop |
| `make_context_compact_node()` | `context_compact.py` | Tạo node quản lý context window |
| `make_intent_node()` | `intent.py` | Tạo node LLM phân loại intent |
| `route_after_intent()` | `intent.py` | Route tới nhánh phù hợp dựa trên intent |
| `load_erp_guide_index()` | `erp_guide/load_index.py` | Load ERP domain knowledge index |
| `retrieve_erp_context()` | `erp_guide/retrieve.py` | Retrieve ERP context cho gợi ý khi query ngoài domain |

---

## Tổng quan kiến trúc

```
┌─────────────┐     HTTP/JSON      ┌─────────────┐     HTTP/JSON      ┌─────────────┐
│  Frontend   │ ──────────────────► │   Spring    │ ──────────────────► │   Python    │
│   (React)   │ ◄────────────────── │   Boot      │ ◄────────────────── │  FastAPI +  │
│             │   SSE Events        │  (Relay)    │   SSE Stream       │  LangGraph  │
└─────────────┘                     └──────┬──────┘                     └──────┬──────┘
                                           │                                   │
                                           │ JDBC                              │ HTTP
                                           ▼                                   ▼
                                   ┌──────────────┐                   ┌──────────────┐
                                   │ PostgreSQL   │                   │ Spring APIs  │
                                   │ (Read-only   │                   │ (describe,   │
                                   │  + Drafts)   │                   │  query, CRUD)│
                                   └──────────────┘                   └──────────────┘
```

## SSE Events Summary

| Event | Nguồn | Mục đích | Frontend Component |
|-------|-------|----------|-------------------|
| `progress` | Python nodes | Hiển thị trạng thái xử lý | Progress bar text |
| `delta` | Python `final_answer` | Streaming text | Chat message bubble |
| `clarify` | Domain guard / SQL clarify | Hỏi làm rõ user | `AiChatClarifyCard` |
| `chart` | SQL branch → chart | Biểu đồ Vega-Lite | `AiChatChartCard` |
| `draft` | Catalog draft branch | Bảng nhập catalog | `AiChatDraftTableCard` |
| `inventory_draft` | Inventory draft branch | Phiếu nhập kho | `AiChatReceiptDraftCard` |
| `data_table` | SQL branch → query table | Bảng dữ liệu SQL | `AiChatQueryTableCard` |
| `error` | Any node failure | Hiển thị lỗi | Chat message bubble |
| `done` | Graph complete | Kết thúc stream | Ẩn typing indicator |

## Spring → Python Callback APIs

| Endpoint | Method | Mục đích | Python Client |
|----------|--------|----------|---------------|
| `/api/v1/ai/db/sql/describe` | POST | Lấy schema metadata | `spring_describe_client.py` |
| `/api/v1/ai/db/sql/query-readonly` | POST | Template-based read-only query | `sql_executor.py` |
| `/api/v1/ai/db/sql/query-readonly-raw` | POST | Raw read-only SQL query | `sql_executor.py` |
| `/api/v1/ai/catalog-drafts` | POST/GET/PATCH/DELETE | Catalog draft CRUD | `spring_catalog_draft_client.py` |
| `/api/v1/ai/catalog-drafts/validate` | POST | Validate catalog draft FK | `spring_catalog_draft_client.py` |
| `/api/v1/ai/inventory-drafts` | POST/GET/PATCH/DELETE | Inventory draft CRUD | `spring_inventory_draft_client.py` |
| `/api/v1/ai/inventory-drafts/validate` | POST | Validate inventory draft FK | `spring_inventory_draft_client.py` |
