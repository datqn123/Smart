# Task003 — Đọc dữ liệu Smart ERP qua chat AI (RAG + MCP) — **Options document** (Gate G-AI-PLAN, pass 1)

> **Trạng thái**: Bản phương án cho Owner **HITL** — **không** phải PRD cuối (§4 theo `AI_PLANNER_AGENT_INSTRUCTIONS` v1.2).  
> **Phiên bản tài liệu**: 1.0  
> **Phạm vi cứng**: Toàn bộ triển khai chỉ trong `ai_python/`. **Không** chỉnh `backend/` hay `frontend/`. CSDL Smart ERP thuộc backend; AI chỉ đọc qua **MCP** theo Design Doc (`db-readonly`, `vector-rag`) — tài liệu này mô tả **khái niệm**, không SQL thô / migration.

---

## 1) Understanding summary

### Input

- Câu hỏi của người dùng trong luồng chat AI (tiếng Việt hoặc khác), có thể về **nghiệp vụ dự án**, **cấu trúc/thông tin** liên quan **CSDL ERP**, hoặc **số liệu tổng hợp** (tuỳ quyền).
- Ngữ cảnh phiên (`session_id`, có thể `correlation_id`) và (sau này) metadata tenant/role theo contract backend — **cần làm rõ** với Owner nếu chưa cố định.
- Nguồn dữ liệu **được phép**: chỉ qua MCP — ví dụ `vector-rag` (tài liệu, schema đã chunk) và `db-readonly` (truy vấn read-only theo template/guardrail), không kết nối DB trực tiếp từ `ai_python`.

### Logic

- Tách **hiểu câu hỏi** → **lấy ngữ cảnh** (RAG: docs/schema/catalog) → **tùy intent** gọi thêm **truy vấn dữ liệu thực** (read-only, có kiểm soát) hoặc chỉ trả lời từ ngữ cảnh đã index.
- **Tối ưu lưu trữ / RAG**: quyết định *gì* được đưa vào vector store (mô tả bảng, quan hệ khái niệm, glossary nghiệp vụ, catalog), tần suất làm mới, và **không** lưu trữ bí mật / dữ liệu nhạy cảm thô trong chunk công khai.
- Ghép kết quả vào **prompt an toàn** (policy: từ chối ghi, từ chối lộ credential), có thể có bước **critic / validator** theo chuỗi agent hiện có (`ai_python`).

### Output

- Phản hồi streaming (hoặc JSON theo contract) cho chat: trả lời **đúng** với dữ liệu được phép, kèm **giảm ảo giác** nhờ trích dẫn từ chunk RAG và/hoặc tóm tắt kết quả truy vấn read-only **đã được kiểm soát**.
- (Tuỳ chọn) Sự kiện audit / log cấp ứng dụng (không log nội dung nhạy cảm) — theo NFR Design Doc.

### Success Criteria

- Người dùng hợp lệ có thể **hỏi về dự án và CSDL** (ở mức được phép) và nhận câu trả lời **nhất quán** với nguồn (RAG +/hoặc dữ liệu live read-only).
- **Không** có đường ghi DB từ AI; mọi truy vấn DB qua MCP **read-only** và **từ chối** yêu cầu chỉnh sửa dữ liệu (route sang luồng Write/HITL nếu có — ngoài scope triển khai backend ở task này).
- **Chất lượng RAG**: cải thiện đo được (eval ≥ ngưỡng sprint theo `WORKFLOW_RULE` / Design §6) trên tập prompt kiểu: schema, glossary, câu hỏi tổng hợp có kiểm chứng số.

---

## 2) Ambiguities & open assumptions

- **Phân quyền theo vai trò/tenant**: brief chưa nêu rõ ai được hỏi dữ liệu nào — ảnh hưởng filter RAG và phạm vi `db-readonly`.
- **Độ “tươi” của dữ liệu**: cần trả lời theo snapshot tài liệu hay **bắt buộc** số live từ ERP — quyết định A/B/C bên dưới.
- **Giới hạn miền nghiệp vụ** (ví dụ chỉ master data vs có cả giao dịch) — ảnh hưởng ingest RAG và catalog template SQL.

---

## 3) Clarifying questions (tối đa 5)

1. **Ai là người dùng mục tiêu và phân quyền tối thiểu?** (ví dụ chỉ admin nội bộ, hay user đa tenant?) — **Why it matters**: xác định namespace/filter cho `vector-rag` và giới hại gọi `db-readonly`.
***Chỉ có user có Role Admin mới dùng AI được***
2. **Mức độ nhạy cảm dữ liệu được phép đưa vào câu trả lời** (PII, giá, lương, v.v.) — **Why it matters**: quyết định chunk nào được index, có cần masking, và eval red-team.
***Đã chốt role Admin toàn quyền***
3. **Ưu tiên: độ chính xác “đúng số” hay độ đầy “giải thích schema”?** — **Why it matters**: cân bằng giữa RAG tài liệu và tần suất gọi `db-readonly` (latency, chi phí, rủi ro).
***Chỉ cần cung cấp đúng số lượng yêu cầu, khi nào cần giải thích thì user sẽ chat giải thích***
4. **Tần suất làm mới tri thức RAG** (theo release, theo ngày, manual) — **Why it matters**: kiến trúc job ingest và KPI “không stale quá mức”.
***Theo ngày***
5. **Ngôn ngữ đầu ra mặc định và có bắt buộc trích dẫn nguồn (chunk id / tên bảng)?** — **Why it matters**: UX và kiểm chứng giảm hallucination.
***Không cần, chỉ cần đưa thông tin ra là được***

---

## 4) Solution options

### Option A — **RAG-first, DB read-only có chọn lọc** (“schema trong vector, số khi cần”)

- **Pros**: Giảm gọi DB; phù hợp Design (Phase 0 có thể ưu tiên `vector-rag`); giải thích schema/glossary tốt; chi phí inference/DB hợp lý nếu index tốt.
- **Cons**: Cần quy trình ingest/chuẩn hoá tài liệu schema & domain; nếu ingest lỗi, model vẫn có thể ảo giác trừ khi có bước kiểm.
- **Risks**: Drift giữa RAG và DB thực tế nếu không refresh; trả lời “đúng concept, sai số” nếu không gọi `db-readonly` khi user cần số live.
- **Cost-to-change**: Trung bình: chủ yếu trong `ai_python` (pipeline chunk, tool routing); phụ thuộc MCP `vector-rag`/`db-readonly` đã/ sẽ có sẵn phía tích hợp.
- **When to choose**: Hầu hết câu hỏi là **hiểu hệ thống / tra cứu**; chỉ thỉnh thoảng cần **xác nhận số liệu** với guardrail.

### Option B — **Hybrid mạnh: RAG + truy vấn read-only theo template** (“đúng số ưu tiên khi được phép”)

- **Pros**: Câu trả lời gần **ground truth** cho báo cáo/tổng hợp; RAG vẫn hỗ trợ chọn đúng template/params và giải thích.
- **Cons**: Tăng độ phức tạp orchestration; tăng latency và chi phí; governance template_id/params chặt hơn; cần eval kỹ để tránh lộ dữ liệu qua kết quả query.
- **Risks**: Sai sót mapping intent → template; overload MCP `db-readonly` nếu không rate-limit; lỗi UX nếu NFR latency không đạt.
- **Cost-to-change**: Cao hơn A: nhiều nhánh agent, nhiều kịch bản test; phụ thuộc danh mục template an toàn (do backend/MCP owns contract).
- **When to choose**: Người dùng **thường xuyên** cần **số liệu ERP chính xác** trong chat (dashboard hỏi đáp), chấp nhận độ trễ và đầu tư eval.

### Option C — **Docs/catalog-only RAG (không live SQL trong v1 AI service)** (“an toàn triển khai, dữ liệu trễ”)

- **Pros**: Triển khai nhanh trong `ai_python`; bề mặt tấn công nhỏ hơn; không phụ thuộc `db-readonly` ngay; phù hợp MVP demo.
- **Cons**: Không đảm bảo **số live**; cần quy trình **xuất snapshot** định kỳ từ backend vào nguồn mà RAG ingest (concept: export được phép — triển khai chi tiết ngoài scope backend ở đây).
- **Risks**: Trả lời lệch thực tế vận hành; user tin tưởng sai nếu không gắn nhãn “dữ liệu đến ngày …”.
- **Cost-to-change**: Thấp đến trung bình trong `ai_python`; **chi phí tổ chức** snapshot/QA nghiệp vụ có thể cao theo thời gian.
- **When to choose**: MCP `db-readonly` **chưa** ổn định; hoặc chính sách **cấm** số live trong chat pha đầu.

---

## 5) Recommendation (chọn hướng triển khai)

- **Chọn Option A làm baseline**: phù hợp brief “tối ưu lưu trữ + RAG” và ranh giới Smart ERP DB thuộc backend; tận dụng `vector-rag.search_docs` / `search_schema` (theo Design) trước khi mở rộng.
- **Chuẩn bị mở rộng sang B**: thiết kế orchestration có **hook** gọi `db-readonly` chỉ khi intent = “số liệu xác minh” và có policy — tránh nhét SQL thô vào `ai_python`.
- **Không chọn C** trừ khi Owner xác nhận **không** cần số live trong nửa đầu release — vì brief nhấn “đưa ra câu trả lời **đúng nhất**”, thường cần ground truth có kiểm soát (A/B).
- **Bắt buộc**: nhãn thời gian / nguồn trả lời khi kết hợp RAG + DB; eval theo Design §6 (từ chối ghi, từ chối lộ secret).
- **Làm rõ qua 5 câu hỏi** về phân quyền và nhạy cảm trước khi khóa PRD cuối (§4).

---

## 6) Suggested slug (tên file / branch)

**`erp_db_read_rag`**

- Gợi ý tên file PRD sau khi Owner chọn A/B/C: `PRD_Task003_erp_db_read_rag.md` (theo gate `G-AI-PLAN`).

---

## 7) Next step (Owner)

Owner chọn **A**, **B**, hoặc **C** (hoặc A + lộ trình B), trả lời ngắn các mục mục §3 nếu có — sau đó AI_PLANNER sinh **PRD §4 đầy đủ** (không lặp bản options này).
