# PRD — Task005 — Đọc DB (MCP), tạo file corpus RAG & registry (Agent/API không thuộc v1)

> **Gate**: G-AI-PLAN — **Owner đã chọn phương án triển khai: Option B** (artifact + smoke `sql.query_readonly`).  
> **Phiên bản tài liệu**: 1.3  
> **Phạm vi cứng**: Chỉ **`ai_python/`**. Không chỉnh `backend/`, `frontend/`.  
> **Trọng tâm v1**: **pipeline offline/batch** — sinh file ngữ cảnh + **RAG ingest/index**; **không** triển khai kết nối tới **Chat Agent qua HTTP/API** trong task này.  
> **Ràng buộc thiết kế** (tham chiếu `Design_Agent/mcp/DB_READONLY_TOOLS.md`): truy cập CSDL Smart ERP **read-only** qua MCP **`db-readonly`** trong bước generate; artifact và registry được thiết kế để **sau này** Agent (task khác) kết hợp RAG + **`template_id` + `params`** — **không** sinh SQL thô trong luồng retrieve/generate corpus.

---

## 4.1. Project Overview

**Mục tiêu (v1)**: Trong `ai_python`, triển khai **đọc metadata/tri thức từ DB qua MCP (read-only)** và **xuất các file cấu trúc** (catalog schema, glossary, registry template) vào thư mục corpus **ổn định**; chạy/chuẩn bị **RAG** (chunk + index/namespace) trên corpus đó. Các file phải đủ rõ để **một Agent tương lai** (ngoài scope Task005) có thể **retrieve RAG** và map intent → **`template_id` + `params`** / `sql.describe` theo guardrail — nhưng **không** yêu cầu trong Task005 phải có endpoint Agent, SSE, hay chỉnh luồng chat.

**Không thuộc v1**: Tích hợp runtime Chat Agent (REST/SSE/MCP turn), cập nhật prompt/tool của agent trong phiên chat, hay API cho UI — ghi nhận là **follow-up** sau khi corpus + RAG ổn định.

**Người dùng / actor (v1)**: Vận hành/dev chạy CLI/job generate và (tuỳ codebase) indexer RAG; **không** giả định người dùng cuối chat qua UI trong phạm vi task này.

**Giả định vận hành**: refresh corpus **hàng ngày** khi triển khai lịch; **theo Option B**, mỗi chu kỳ generate gồm **`sql.describe` batch + smoke `sql.query_readonly`** (template được đánh dấu smoke-safe + params mặc định) và ghi artifact trạng thái để RAG/triển khai sau tin cậy template còn “sống”; không bắt buộc trích dẫn chunk id trong UX **vì UX chat không thuộc v1**.

---

## 4.2. Specifications

### Functional requirements

1. **Artifact generation (file-based)**: Pipeline trong `ai_python` tạo/cập nhật tập file (ví dụ Markdown/JSON/YAML) mô tả:
   - **Danh mục đối tượng DB được phép** (views/tables theo contract MCP — khái niệm, không migration).
   - **Cột, kiểu, nullable** (từ nguồn được phép: export tĩnh hoặc kết quả `sql.describe` — tuỳ phương án).
   - **Glossary / domain terms** (tối thiểu: placeholder có cấu trúc nếu nội dung nghiệp vụ chưa đầy đủ).
   - **Registry `template_id` → mô tả intent, params schema, ví dụ params** (để Agent sau map intent → `sql.query_readonly`; không yêu cầu triển khai Agent trong Task005).
2. **RAG ingest surface**: Các file trên nằm dưới thư mục/versioning rõ (ví dụ `ai_python/data/rag_corpus/…` hoặc tương đương) và được **đánh dấu phiên bản + timestamp** để tránh drift không kiểm soát; pipeline RAG đọc **trực tiếp** corpus/index (không bắt buộc qua Agent trong v1).
3. **Contract cho Agent sau này (file-only, không runtime)**: Registry + schema doc phải mô tả rõ **mapping intent → `template_id` + params** và giới hạn **không SQL thô** (theo `DB_READONLY_TOOLS.md`), để task tích hợp Agent sau chỉ **nối retrieve RAG + đọc registry** — không phải thiết kế lại corpus trong Task005.
4. **Refresh**: Job hoặc CLI có thể chạy **định kỳ hàng ngày** (cron/Task Scheduler ngoài scope code; trong PRD chỉ cần entrypoint rõ ràng).
5. **An toàn**: Không ghi DB từ `ai_python`; không lưu credential DB trong artifact; log không chứa dữ liệu nhạy cảm thô.
6. **Smoke validation template (Option B — đã khóa)**: Với tập `template_id` được cấu hình **smoke-safe** (params mặc định, LIMIT nhỏ), job định kỳ gọi **`sql.query_readonly`**; ghi **kết quả tóm tắt** (HTTP/MCP OK, số dòng, lỗi nếu có — **không** dump full row) vào file artifact (ví dụ `template_status/*.md` hoặc `health.json`) để đưa vào corpus hoặc namespace RAG tách biệt schema mô tả.

### Non-functional requirements (NFRs)

| NFR | Mục tiêu định lượng / ghi chú |
|-----|--------------------------------|
| Latency ingest batch | Hoàn tất refresh artifact điển hình \< 10 phút trên DB dev giả lập (điều chỉnh khi có số liệu thực). |
| Kích thước corpus | Giới hạn chunk hợp lý (ví dụ \< 5MB text tổng cho v1) hoặc chia namespace để vector store không nổ. |
| Idempotency | Chạy lại job không làm hỏng trạng thái (ghi file atomically / version). |
| Observability | Mỗi lần generate có `correlation_id` / log dòng: số object, thời gian, lỗi MCP từng bước. |

---

## 4.3. Tech stack

- **Runtime**: Python trong `ai_python/` — ưu tiên **CLI/worker** cho generate + ingest RAG; **FastAPI/endpoint chỉ khi đã có sẵn trong repo và phục vụ health/metrics tối thiểu** — **không** bắt buộc thêm API Chat Agent trong Task005.
- **Tích hợp DB (generate)**: Chỉ qua **MCP** `db-readonly`: bắt buộc **`sql.describe`** (batch) + **`sql.query_readonly`** (smoke theo Option B); tái sử dụng MCP client hiện có nếu có.
- **RAG**: Vector store / chunker trong `ai_python` (không đổi `backend/`/`frontend/`).
- **Định dạng file**: JSON Schema hoặc JSON cho registry; Markdown cho human-readable schema doc (để chunk dễ).

---

## 4.4. Solution options (A / B / C — đã chọn **B**)

### Option A — **Artifact-first, DB qua MCP tối thiểu** (“file tĩnh + describe định kỳ nhẹ”) — *không chọn*

- **Mô tả**: Script/job trong `ai_python` tạo file corpus chủ yếu từ **nguồn tĩnh đã duyệt** (danh sách object allowlist trong config) + gọi **`sql.describe`** theo danh sách đó **một lần mỗi ngày** để cập nhật cột. Template registry là file JSON đồng bộ tay (hoặc generate từ cùng config) — **Agent tương lai** sẽ đọc RAG + registry khi đã có task tích hợp; Task005 chỉ đảm bảo file + index.
- **Pros**: Đơn giản, bề mặt tấn công nhỏ; khớp “không SQL thô”; dễ review PR; chi phí MCP thấp.
- **Cons**: Thiếu “ground truth” động nếu không có bước query/template validation sau này (runtime); describe có thể lệch nếu allowlist không cập nhật.
- **Risks**: Drift giữa registry template và backend nếu template mới chưa được thêm vào file.
- **Cost-to-change**: Thấp–trung bình.
- **When to choose**: V1 ổn định, ưu tiên ship nhanh artifact + RAG; số liệu runtime qua **`sql.query_readonly`** thuộc **task Agent/API sau**, không bắt buộc trong Task005.

### Option B — **Hybrid mạnh: artifact + validation query có kiểm soát** (“RAG + xác minh template”) — **[ĐÃ CHỌN]**

- **Mô tả**: Như A, thêm bước **smoke query** định kỳ: với một tập `template_id` “an toàn”, gọi `sql.query_readonly` với params mặc định (LIMIT nhỏ) để xác minh template còn hoạt động; ghi **kết quả tóm tắt** (không nhất thiết full rows) vào file status hoặc log structured để corpus/RAG phản ánh template alive (không cần Agent online).
- **Pros**: Giảm rủi ro “template chết”; tốt cho yêu cầu **đúng số**; phù hợp **smoke validation** định kỳ (phương án đã chọn).
- **Cons**: Phức tạp hơn A; cần kỷ luật không log dữ liệu nhạy cảm; tăng tải MCP.
- **Risks**: Nếu params mặc định không đại diện, vẫn có false sense of security.
- **Cost-to-change**: Trung bình–cao.
- **When to choose**: Khi số lượng template tăng và cần **độ tin cậy vận hành** của corpus trước khi nối Agent/chat sau này.

### Option C — **N/A (placeholder “MCP-live catalog”) — biến thể nhẹ** — *không chọn*

- **Mô tả**: **Không** duy trì corpus file lớn; job định kỳ hoặc bootstrap từ **một file manifest nhỏ** (danh sách object + template) + gọi `sql.describe` **lazy** hơn (ít batch). RAG chỉ index **glossary + policy ngắn**, không index full schema.
- **Pros**: Ít stale trên metadata; triển khai artifact tối thiểu.
- **Cons**: Latency cao hơn; phụ thuộc MCP mỗi lần hỏi sâu; kém “tối ưu lưu trữ + RAG” so với brief Task005.
- **Risks**: Rate limit / timeout MCP khi traffic tăng.
- **Cost-to-change**: Thấp cho storage, cao cho vận hành inference.
- **When to choose**: DB nhỏ, số template ít, chấp nhận đổi latency lấy độ “tươi”.

---

## 4.5. Quyết định Owner (khóa triển khai)

- **Đã chọn: Option B** — corpus gồm **schema/describe + registry + artifact trạng thái smoke** (`sql.query_readonly` định kỳ, có kiểm soát), phù hợp **độ tin cậy vận hành** trước khi (sau này) nối Agent/chat.
- **Phạm vi kỹ thuật**: Giữ nguyên giới hạn v1 — **không** API Chat Agent; smoke chỉ chạy trong job batch/CLI, không mở endpoint mới cho UI.
- **Gợi ý triển khai**: Module generate chạy tuần tự **describe → smoke (theo danh sách template smoke-safe) → ghi file → ingest RAG**; thiết kế config để tắt/bật từng `template_id` smoke khi cần vận hành.

---

## 4.6. Task breakdown & dependency graph

- [ ] **T005-1 — Layout corpus & config allowlist**
  - **Description**: Thêm cấu trúc thư mục + file config (object list, template registry schema).
  - **Input/Output**: Input: contract MCP + danh sách object; Output: tree `data/rag_corpus/` + `registry/templates.json` mẫu.
  - **Acceptance Criteria**: Đường dẫn cố định được doc trong README nội bộ module; không chứa secret.

- [ ] **T005-2 — Generator: `sql.describe` batch**
  - **Description**: Script gọi MCP `sql.describe` theo allowlist, merge vào file Markdown/JSON cho RAG.
  - **Input/Output**: Input: config; Output: `schema/*.md` hoặc `catalog.json` có version + timestamp.
  - **Acceptance Criteria**: Chạy lại idempotent; lỗi partial được ghi rõ; tôn trọng timeout/rate limit (retry backoff).

- [ ] **T005-2b — Smoke `sql.query_readonly` + artifact trạng thái (Option B)**
  - **Description**: Theo registry, gọi `sql.query_readonly` cho các `template_id` cấu hình smoke (params mặc định, LIMIT nhỏ); ghi file tóm tắt kết quả/hỗ trợ index RAG (namespace riêng hoặc cùng corpus có tiền tố rõ).
  - **Input/Output**: Input: output T005-2 + `registry/templates.json` (mục smoke); Output: ví dụ `template_status/*` hoặc `health.json` có version + timestamp.
  - **Acceptance Criteria**: Không log row đầy đủ; template fail được ghi để RAG/agent sau không tin “template sống” sai; idempotent khi rerun.

- [ ] **T005-3 — RAG ingest wiring**
  - **Description**: Nối corpus mới (schema + **template status**) vào pipeline chunk/index hiện có (hoặc stub indexer nếu chưa có).
  - **Input/Output**: Input: artifact T005-2 **và** T005-2b; Output: index có namespace `erp_schema` (hoặc tên tương đương) và tuỳ chọn `erp_template_health`.
  - **Acceptance Criteria**: Integration test đọc được ≥1 chunk từ corpus mới (không yêu cầu gọi Agent/API).

- [ ] **T005-4 — Registry & contract files (cho Agent sau, không triển khai Agent API)**
  - **Description**: Hoàn thiện **file** registry (`template_id`, params schema, ví dụ) + tài liệu ngắn (README module) mô tả cách Agent tương lai kết hợp retrieve RAG + MCP — **không** thêm endpoint HTTP/SSE, không chỉnh luồng chat.
  - **Input/Output**: Input: PRD + `DB_READONLY_TOOLS.md`; Output: JSON/registry đã validate + ví dụ mapping **ở mức file**.
  - **Acceptance Criteria**: Schema/registry parse được bằng test đơn giản; có ví dụ “golden” **file-based** (không snapshot prompt Agent).

- [ ] **T005-5 — Daily refresh entrypoint**
  - **Description**: CLI `python -m ... generate_erp_rag_corpus` (hoặc tương đương) chạy **T005-2 → T005-2b → ingest (T005-3)** + exit code cho cron.
  - **Input/Output**: Input: env MCP; Output: corpus mới + log summary.
  - **Acceptance Criteria**: Chạy trên môi trường dev không crash khi MCP unavailable (fail graceful + exit ≠ 0).

**Dependencies**: T005-2 phụ thuộc T005-1; **T005-2b** phụ thuộc T005-2 (và registry có mục smoke); T005-3 phụ thuộc T005-2 **và** T005-2b; T005-4 song song sau T005-1 khi có registry mẫu; T005-5 bọc T005-2 → T005-2b → T005-3.

---

## 4.7. Assumptions (Owner có thể điều chỉnh sau)

1. MCP `db-readonly` đã (hoặc sẽ) expose **`sql.describe`** và **`sql.query_readonly`** đúng contract pack.  
2. Danh sách views/tables allowlist do **backend/MCP owner** cung cấp dưới dạng config có thể nhúng trong `ai_python` (không sửa backend trong task này).  
3. Template catalog ban đầu có thể **nhỏ** (3–10 template) để chứng minh end-to-end.  
4. Ngôn ngữ corpus: **tiếng Việt** cho glossary nếu có; tên cột giữ theo DB.

---

## 4.8. Out of scope

- **Kết nối Chat Agent qua API** (REST/SSE/WebSocket), MCP “turn” chat, hay endpoint phục vụ UI chat.  
- Cập nhật prompt/tool **runtime** của Agent trong phiên hội thoại (thuộc task tích hợp sau).  
- Tạo view/reporting mới trên DB Spring (backend).  
- UI thay đổi trong `frontend/`.  
- Bật `sql.query_readonly_raw` hoặc cho phép LLM sinh SQL tự do.

---

## Next step (sau khi khóa Option B)

Chuyển **AI_BA / SRS** và chuỗi implement theo [`ai_python/AGENTS/WORKFLOW_RULE.md`](../../AGENTS/WORKFLOW_RULE.md): SRS phản ánh **Option B** (describe batch + smoke `sql.query_readonly` + artifact status + RAG), không giả định API Chat Agent trong Task005.
