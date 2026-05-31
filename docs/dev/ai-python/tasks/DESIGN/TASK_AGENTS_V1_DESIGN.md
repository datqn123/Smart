# Task design — các Agent cụ thể (chatbot đa agent v1)

**Phạm vi:** Thiết kế **task/nhiệm vụ** cho từng agent và lớp kiểm tra trong pipeline v1; **không** chứa code. Đồng bộ hai nguồn:

- `docs/plans/existing/feature/ai_chatbot_da_agent_v1.plan.md` — ánh xạ LangGraph, subgraph SQL (`gen_sql → sql_review → validate_sql → execute_sql → validate_result`), retry sinh SQL tối đa 3, registry intent.
- Plan stack phân tích (`ai_chatbot_stack_phân_tích_2a2c5a12`) — vai trò agent trong kiến trúc Spring + FastAPI, rủi ro text-to-SQL, nguyên tắc mở rộng registry.

**Quy ước tên:** Trong code có thể map `Agent_SQL` → node `gen_sql`; `Agent_SQL_Review` → node `sql_review`; hai lớp validate trong feature plan tách **policy SQL** (`validate_sql`) và **kết quả** (`validate_result`) — gộp trong stack plan dưới khái niệm “Agent_Validate”; dưới đây **tách rõ** để task không chồng lấn.

---

## 0. Ma trận agent ↔ node LangGraph

| Agent / lớp xử lý | Node graph (gợi ý) | LLM? | Ghi chú |
| :-- | :-- | :-- | :-- |
| **Agent_Intent** | `intent` | Có | Structured routing intent v1. |
| **Agent_Chat_Normal** | `chat_normal` | Có | Không tool DB v1. |
| **Agent_DB_Meta** | *(offline / artifact)* | Tuỳ (job quét) | Không chạy mỗi turn chat; output file schema version. |
| **Agent_SQL** | `gen_sql` | Có | Một câu SELECT; nhận feedback retry. |
| **Agent_SQL_Review** | `sql_review` | Có (hoặc hybrid deterministic) | Khớp schema/FK trước policy cứng. |
| **Validate SQL (policy)** | `validate_sql` | Không | SELECT-only, allowlist, LIMIT, DDL/DML chặn. |
| **Execute (read-only)** | `execute_sql` | Không | Python→DB hoặc Python→Spring. |
| **Validate kết quả** | `validate_result` | Không (v1) | Kích thước payload, shape, empty/error tối thiểu. |
| **Summarize answer** *(tuỳ chọn)* | `summarize_answer` | Có | NL từ `query_result` + câu hỏi. |
| **Intent registry** | `route_by_intent` + đăng ký handler | Không | Map intent → subgraph/handler. |

---

## 1. Agent_Intent

**Vai trò:** Đọc tin nhắn user (và ngữ cảnh ngắn) → **phân loại intent** để router không “đoán” bằng if-else khắp nơi.

**Intent v1 (tối thiểu):**

- `system_data_query` — cần dữ liệu ERP/DB (đi subgraph SQL).
- `general_chat` — kiến thức chung / không cần DB nội bộ.

**Reserved (design):** placeholder cho `chart_report`, `form_confirm`, … — chỉ đăng ký trong registry khi có subgraph.

### Contract (thiết kế)

| | |
| :-- | :-- |
| **Input** | `user_text` hoặc `messages[-1]`; tuỳ chọn `locale`; **không** cần full schema DB trong prompt intent (tránh leak + token). |
| **Output (structured)** | `intent: Literal["system_data_query","general_chat"]`; tuỳ chọn `confidence: float` hoặc `reason_short: str` để debug (không bắt buộc FE). |
| **State** | Ghi `state["intent"]`; router đọc conditional edge. |

### Task design

- **AGENT-INT-01** — Định nghĩa schema Pydantic/TypedDict cho output; ràng buộc enum đồng bộ với registry keys.
- **AGENT-INT-02** — Prompt phân loại: ví dụ phân biệt “doanh số hôm nay” vs “mấy giờ”; ngôn ngữ user (VI/EN).
- **AGENT-INT-03** — Fallback an toàn khi ambiguous: mặc định `general_chat` **hoặc** `system_data_query` — **chốt một** trong review kiến trúc (ảnh hưởng false positive DB).
- **AGENT-INT-04** — Không nhét schema bảng vào prompt intent; chỉ mô tả vai trò classifier.

### Ranh giới / không làm

- Không thực thi SQL; không gọi DB.
- Không thay Spring RBAC — chỉ routing trong Python.

---

## 2. Agent_Chat_Normal

**Vai trò:** Trả lời hội thoại **không** gắn dữ liệu nội bộ qua DB tool (giờ, thời tiết, FAQ chung) — đúng stack plan.

### Contract

| | |
| :-- | :-- |
| **Input** | `messages` (đoạn hội thoại); metadata `locale` nếu có. |
| **Output** | `final_answer` (text); có thể append assistant message vào `messages`. |
| **State** | `final_answer`; không set `generated_sql` / `query_result`. |

### Task design

- **AGENT-CHAT-01** — System prompt: bot là trợ lý ERP nhưng nhánh này **không** truy cập DB; không tiết lộ schema nội bộ.
- **AGENT-CHAT-02** — Policy nội dung (PII, chủ đề cấm) — mức tối thiểu v1.
- **AGENT-CHAT-03** — Rate limit / token budget (cấu hình chung LLM hoặc middleware).
- **AGENT-CHAT-04** — v1: không bind tool; ghi chú mở rộng sau (weather API, …) không làm trong sprint agent core.

### Ranh giới

- Không load file schema; không gọi execute_sql.

---

## 3. Agent_DB_Meta (offline / job)

**Vai trò:** **Quét / đồng bộ** metadata DB → **artifact** (YAML/JSON/MD) có **version** (migration hoặc hash) để `Agent_SQL` / `Agent_SQL_Review` chỉ đọc snapshot — stack plan + feature plan.

**Không** là node bắt buộc mỗi request; là pipeline định kỳ hoặc sau deploy.

### Contract (artifact)

| | |
| :-- | :-- |
| **Output file** | Danh sách bảng/cột được phép expose cho AI; FK/index chọn lọc; quy ước naming domain; **version** rõ ràng. |
| **Input job** | Connection read-only metadata (information_schema hoặc tương đương); có thể filter theo tenant/schema. |

### Task design

- **AGENT-DBM-01** — Định dạng file và schema version string (vd.Align migration id).
- **AGENT-DBM-02** — CLI hoặc cron: path output, logging, exit code.
- **AGENT-DBM-03** — Allowlist bảng/cột ngay từ bước meta (**giảm** surface text-to-SQL).
- **AGENT-DBM-04** — Runtime `ai_python`: loader đọc file theo `schema_version` từ request/state — không đọc DB trực tiếp mỗi turn (tuỳ chỉnh sau).

### Ranh giới

- Không sinh SQL; không trả lời user trực tiếp.

---

## 4. Agent_SQL (node `gen_sql`)

**Vai trò:** Sinh **đúng một** câu SQL ưu tiên `SELECT`, read-only, dựa trên câu hỏi user + **schema snapshot** + `validation_feedback` khi retry.

### Contract

| | |
| :-- | :-- |
| **Input** | `user_text`; nội dung schema (theo `schema_version`); `validation_feedback` (lần retry); `sql_attempt_count` (để prompt biết lượt). |
| **Output** | `generated_sql: str`; có thể kèm `reasoning` nội bộ không gửi FE. |
| **State** | Ghi `generated_sql`; mỗi lần vào node tăng `sql_attempt_count` theo quy ước đã chốt (feature plan §2.1). |

### Task design

- **AGENT-SQL-01** — Prompt: chỉ SELECT; khớp tên bảng/cột trong artifact; gợi ý JOIN theo FK nếu có trong file meta.
- **AGENT-SQL-02** — Ép **một** statement; từ chối sinh batch / nhiều query (validate_sql có thể bắt).
- **AGENT-SQL-03** — Tiêm tenant filter nếu policy yêu cầu (placeholder trong prompt hoặc post-process — phối hợp validate_sql).
- **AGENT-SQL-04** — Nhận feedback có cấu trúc từ `sql_review` / `validate_sql` / execute / `validate_result` để sửa SQL lần sau.

### Ranh giới

- Không tự execute; không bypass `sql_review` / `validate_sql`.

---

## 5. Agent_SQL_Review (node `sql_review`)

**Vai trò:** Đối chiếu SQL đã sinh với **artifact schema**: bảng/cột tồn tại, JOIN/FK hợp lệ, alias không che lỗi, gợi ý domain tối thiểu. **Trước** `validate_sql` để giảm round-trip DB.

### Contract

| | |
| :-- | :-- |
| **Input** | `generated_sql`; cùng schema snapshot như `gen_sql`. |
| **Output (structured)** | `ok: bool`; `issues: list[str]` (hoặc tương đương); khi fail → merge vào `validation_feedback`. |
| **LLM** | Khuyến nghị có; **tuỳ chọn** hybrid: parser deterministic + LLM khi ambiguous (feature plan §4.3). |

### Task design

- **AGENT-REV-01** — Schema output JSON để conditional edge rõ ràng.
- **AGENT-REV-02** — Prompt tập trung **semantic + structural** khớp DB; không trùng nhiệm vụ policy keyword với `validate_sql`.
- **AGENT-REV-03** — Fail: không execute; route retry về `gen_sql` nếu `can_regen_sql`.
- **AGENT-REV-04** — Không tăng `sql_attempt_count` tại node này (feature plan).

### Ranh giới

- Không thay RBAC tenant ở infrastructure; chỉ review khớp schema đã cho.

---

## 6. Validate SQL — policy (node `validate_sql`)

**Vai trò:** Lớp **cứng**, có thể **không LLM**: chỉ cho phép đọc an toàn trước khi chạm DB.

**Kiểm tra gợi ý (stack + feature plan):**

- Chỉ `SELECT` (hoặc subset được phép).
- Allowlist bảng/cột (theo tenant/role config).
- `LIMIT` bắt buộc hoặc inject an toàn.
- Deny DDL/DML keywords.
- Timeout query (thiết lập ở execute nhưng có thể kiểm tra ước lượng độ phức tạp sau).

### Contract

| | |
| :-- | :-- |
| **Input** | `generated_sql`; rule config (allowlist, tenant). |
| **Output** | Pass/fail + chi tiết vào `validation_feedback`. |

### Task design

- **VAL-SQL-01** — Parser / sqlparse hoặc lib tương đương — quyết định công cụ trong spike.
- **VAL-SQL-02** — Map lỗi → message ngắn cho `gen_sql` retry.
- **VAL-SQL-03** — Đồng bộ với Agent_DB_Meta allowlist (một nguồn config nếu có thể).

### Ranh giới

- Không gọi LLM mặc định; không execute.

---

## 7. Execute read-only (node `execute_sql`)

**Vai trò:** Chạy query đã pass validate, **read-only**; lỗi runtime (syntax DB, connection, timeout) → feedback cho vòng retry.

### Contract

| | |
| :-- | :-- |
| **Input** | SQL string đã validate; context tenant để áp filter nếu execute layer thêm predicate. |
| **Output** | `query_result` (list[dict] hoặc typed); hoặc lỗi có cấu trúc. |

### Task design

- **EXE-01** — Chọn kiến trúc: Python→DB trực tiếp **hoặc** HTTP Spring “execute read query” — spike + ADR ngắn.
- **EXE-02** — Connection pool, timeout, user DB read-only.
- **EXE-03** — Không log full result nếu policy; correlation_id trên log.

### Ranh giới

- Không DML; không quyết định intent.

---

## 8. Validate kết quả (node `validate_result`)

**Vai trò:** Sau execute — kiểm tra số dòng, kích thước payload, empty vs lỗi nghiệp vụ tối thiểu; có thể trigger retry `gen_sql` nếu policy cho thấy truy vấn lệch nghĩa (feature plan §2 bảng).

### Contract

| | |
| :-- | :-- |
| **Input** | `query_result`; `user_text` (so khớp nghĩa tối thiểu — có thể heuristic). |
| **Output** | Pass/fail + feedback. |

### Task design

- **VAL-RES-01** — Ngưỡng max rows / max bytes.
- **VAL-RES-02** — Empty result: có retry hay chuyển summarize giải thích “không có dữ liệu” — **chốt policy v1**.
- **VAL-RES-03** — LLM **không** bắt buộc; nếu sau này cần “semantic check” kết quả thì tách task mở rộng.

---

## 9. Summarize answer (node `summarize_answer`)

**Vai trò:** Chuyển `query_result` + câu hỏi → **câu trả lời tự nhiên** cho user (feature plan §4.2). Có thể gộp vào cuối subgraph.

### Task design

- **SUM-01** — Prompt tóm tắt số liệu; không bịa số không có trong rows.
- **SUM-02** — Giới hạn độ dài; format số/ngày theo `locale`.

---

## 10. Registry intent & handler

**Vai trò:** `intent → compiled subgraph | Runnable` — scale thêm agent không sửa lõi router (stack plan §2.5 + feature plan §4.4).

### Task design

- **REG-01** — Cấu trúc đăng ký: key intent, handler factory, version.
- **REG-02** — Intent không biết → lỗi có cấu trúc hoặc fallback `general_chat` (chốt).
- **REG-03** — Tài liệu hoá cách thêm intent mới (checklist 1 trang).

---

## 11. Phụ thuộc chéo & context chung

**Context xuyên agent (stack plan):** `thread_id`, `user_id`, `tenant_id`, `locale`, `schema_version`, `correlation_id`.

**Task design ngang:**

- **CTX-01** — Truyền context qua state hoặc `config["configurable"]` — một chuẩn duy nhất.
- **CTX-02** — Spring đã cấp quyền AI; Python không được mở rộng scope truy cập ngoài artifact + allowlist.

---

## 12. Checklist “đủ thiết kế agent” trước khi code

- [ ] Mỗi agent có bảng Input/Output và field state.
- [ ] Phân tách rõ **Agent_SQL_Review** vs **validate_sql** vs **validate_result**.
- [ ] Retry: chỉ `gen_sql` tăng `sql_attempt_count`; max 3 lần sinh SQL.
- [ ] Agent_DB_Meta deliver artifact path + version.
- [ ] Registry intent đồng bộ enum `Agent_Intent`.
- [ ] Tài liệu rủi ro text-to-SQL (tenant, LIMIT, read-only) gắn với agent/validate tương ứng.

---

## 13. Tham chiếu nhanh

| Tài liệu | Nội dung liên quan agent |
| :-- | :-- |
| `docs/plans/existing/feature/ai_chatbot_da_agent_v1.plan.md` | Node graph, state, subgraph, retry §2.1 |
| Plan stack `ai_chatbot_stack_phân_tích_2a2c5a12` | Vai trò từng agent v1, rủi ro, registry, Spring cổng |

---

## 14. Tóm tắt

- Đã tách **thiết kế task** cho từng agent/lớp: Intent, Chat_Normal, DB_Meta (artifact), SQL, SQL_Review, validate policy, execute, validate result, summarize, registry.  
- Căn chỉnh **hai plan**: stack plan gộp validate → feature plan tách **ba lớp** sau `gen_sql` (review / policy SQL / kết quả).  
- Bước tiếp theo có thể map ID `AGENT-*` / `VAL-*` sang issue tracker hoặc bổ sung vào `TASK_LANGGRAPH_GEMMA4_TRIEN_KHAI.md` nếu cần một backlog thống nhất.
