# Thiết kế Agentic AI — Smart ERP Assistant

> Tài liệu thiết kế chức năng **Agentic AI** trong `ai_python`. Đây là bản thiết kế mục tiêu (target design), mô tả kiến trúc **nên có để đạt hiệu suất cao**, không ràng buộc theo implementation hiện tại. Các phần đánh dấu 🎯 là nâng cấp so với bản nháp đầu tiên.

---

## 1. Mục tiêu & Phạm vi

### 1.1. Mục tiêu
Xây dựng một trợ lý AI dạng **agentic** cho hệ thống ERP, có khả năng:
- Hiểu yêu cầu ngôn ngữ tự nhiên (tiếng Việt) của user về dữ liệu và nghiệp vụ ERP.
- Tự lập kế hoạch, gọi tool/subagent phù hợp, lặp đến khi tạo ra câu trả lời đúng và đủ.
- Giữ ngữ cảnh hội thoại dài hạn, nhớ được các lượt trước.
- Đảm bảo an toàn dữ liệu, phân quyền, và có cơ chế hỏi lại (HITL) khi mơ hồ.

### 1.2. Trong phạm vi
- Truy vấn dữ liệu đọc (báo cáo, thống kê, tra cứu): inventory, products/catalog, orders, finance.
- Tạo nháp ghi dữ liệu có xác nhận (catalog draft, inventory draft) qua HITL.
- Vẽ biểu đồ/report từ dữ liệu truy vấn.
- Hội thoại nhiều lượt với memory.

### 1.3. Ngoài phạm vi (giai đoạn này)
- Thực thi ghi dữ liệu trực tiếp không qua xác nhận.
- Kiến thức tổng quát ngoài ERP (từ chối lịch sự, gợi ý phạm vi hỗ trợ).

---

## 2. Nguyên tắc thiết kế

| #   | Nguyên tắc                           | Diễn giải                                                                                  |
| --- | ------------------------------------ | ------------------------------------------------------------------------------------------ |
| P1  | **Harness là não điều phối**         | LLM + tools nằm trong khung harness; harness ra quyết định, không để flow tuyến tính cứng. |
| P2  | **Tool độc lập, có hợp đồng rõ**     | Mỗi tool/subagent có input/output schema, không phụ thuộc thứ tự gọi.                      |
| P3  | **Plan tường minh, có thể replan**   | Kế hoạch là một artifact đọc được, sửa được — không ẩn trong một lần gọi LLM.              |
| P4  | 🎯 **Song song khi có thể**          | Các bước độc lập chạy fan-out (DAG), chỉ tuần tự khi có phụ thuộc dữ liệu.                 |
| P5  | **An toàn mặc định**                 | Chặn ghi dữ liệu ngoài luồng, enforce phân quyền theo tenant/role, chống injection.        |
| P6  | **Mơ hồ thì hỏi, đo được**           | Confidence định lượng; dưới ngưỡng thì HITL, trên ngưỡng thì tự suy luận.                  |
| P7  | 🎯 **Tiết kiệm chi phí có chủ đích** | Model rẻ cho việc nhẹ, model mạnh cho việc khó; cache kết quả tất định.                    |
| P8  | **Quan sát được toàn trình**         | Mọi bước có trace, correlation id, metrics latency/cost/retry.                             |

---

## 3. Kiến trúc tổng thể

```
┌──────────────────────────────────────────────────────────────────┐
│                          USER (Frontend)                          │
│            gửi require + session_id  ◄── SSE streaming            │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                          HARNESS (orchestrator)                   │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Intent &   │  │ Planner  │  │ Loop     │  │ Guardrails /    │  │
│  │ Confidence │─▶│ (DAG)    │─▶│ Executor │◀▶│ Policy / HITL   │  │
│  └────────────┘  └──────────┘  └────┬─────┘  └─────────────────┘  │
│         ▲                            │                            │
│  ┌──────┴──────┐              ┌──────▼───────┐  ┌──────────────┐  │
│  │ Memory      │              │ Tool/Subagent│  │ Observability│  │
│  │ (3 tầng)    │              │ Registry     │  │ / Trace      │  │
│  └─────────────┘              └──────┬───────┘  └──────────────┘  │
└──────────────────────────────────────┼───────────────────────────┘
                                       │
┌───────────────────────────────────────▼──────────────────────────┐
│                    LANGGRAPH (tools & subagents)                  │
│  intent · planner · sql_subagent · data_validator · chart ·       │
│  catalog_draft · inventory_draft · compact · answer_composer      │
└──────────────────────────────────────┬───────────────────────────┘
                                       │
                          ┌─────────────▼─────────────┐
                          │  Backend Spring / Postgres │
                          │  (auth, RLS, business API) │
                          └────────────────────────────┘
```

**Phân tầng trách nhiệm:**
- **Harness**: điều phối, lập/sửa plan, quản loop, guardrail, memory, observability.
- **LangGraph**: tập tool/subagent độc lập, mỗi node một nhiệm vụ, có hợp đồng I/O.
- **Backend**: nguồn sự thật dữ liệu + phân quyền (RLS theo tenant), AI không bypass.

---

## 4. Harness — Trách nhiệm chi tiết

| # | Trách nhiệm | Yêu cầu |
|---|---|---|
| H1 | Khung bao quanh LLM + tools | Sở hữu vòng lặp; LLM chỉ là một thành phần ra quyết định. |
| H2 | Điều phối tool/subagent | Theo plan DAG; gọi song song nhánh độc lập; tổng hợp kết quả. |
| H3 | Vòng lặp đến khi có đáp án | Có điều kiện dừng đa tầng (mục 6). |
| H4 | Theo dõi mọi hoạt động | Trace từng tool call: input, output, latency, cost, ok/error. |
| H5 | Hiểu tác vụ & hệ thống | Đọc "System Data Dictionary" (mục 7.1) để map yêu cầu ↔ dữ liệu. |
| H6 | Guardrail bảo mật | Chặn ghi ngoài luồng, enforce tenant/role, chống prompt-injection (mục 11). |
| H7 | HITL | Hỏi lại khi confidence thấp hoặc trước thao tác ghi; pause/resume bền (mục 10). |
| H8 | Memory dài hạn | 3 tầng memory + compact tự động (mục 9). |

---

## 5. Tiếp nhận yêu cầu & Phân tích Intent

### 5.1. Luồng intent
1. User gửi `require` + `session_id`. Harness nạp **working memory** (N lượt gần nhất + bản tóm tắt phiên).
2. Harness gọi **Intent subagent** với input: require + memory + System Data Dictionary.
3. Intent subagent trả về một **Intent Object** có cấu trúc:

```jsonc
{
  "goal": "Mô tả mục tiêu user muốn",
  "intent_type": "data_query | chart_report | catalog_draft | inventory_draft | chat | out_of_scope",
  "required_data": ["entity/field cần lấy"],
  "resolved_entities": [{ "raw": "...", "matched": "...", "score": 0.0 }],
  "confidence": 0.0,        // 0..1, mức chắc chắn tổng thể
  "ambiguities": [{ "field": "...", "options": ["..."], "reason": "..." }],
  "missing_required": ["param bắt buộc còn thiếu"]
}
```

### 5.2. 🎯 Ngưỡng mơ hồ định lượng
Thay cho phán đoán định tính, dùng **confidence score** rõ ràng:

| Điều kiện | Hành động |
|---|---|
| `missing_required` không rỗng | **HITL bắt buộc** — hỏi đúng tham số thiếu. |
| `confidence < 0.75` **hoặc** có ambiguity điểm < 0.6 | **HITL** — hỏi lại, kèm option đề xuất (entity gần nhất). |
| `0.75 ≤ confidence < 0.9` và ambiguity nhẹ | **Tự chọn** entity điểm cao nhất, ghi chú giả định vào câu trả lời. |
| `confidence ≥ 0.9` | Tiến hành lập plan ngay. |

> Ngưỡng cấu hình được; điểm khớp entity tính bằng kết hợp fuzzy + embedding similarity với danh mục thực trong DB.

### 5.3. HITL khi mơ hồ
- Không hỏi cụt lủn: mỗi câu hỏi kèm **option đề xuất** và lý do.
- Tối đa 1–3 câu hỏi/lần; ưu tiên hỏi yếu tố chặn thực thi.

---

## 6. Vòng lặp Agentic & Loop Control

### 6.1. Vòng lặp
```
plan → execute step(s) → observe → đánh giá → (replan? | tiếp | dừng)
```

### 6.2. 🎯 Điều kiện dừng đa tầng
Một agentic loop cần nhiều "cầu dao", không chỉ max steps:

| Loại budget | Mặc định | Hành vi khi chạm |
|---|---|---|
| Max steps tổng | 10 | Trả lời tốt nhất từ observation đã có + nêu giới hạn. |
| Token budget/turn | cấu hình | Gọi compact, hoặc dừng và tóm tắt. |
| Cost budget/turn (USD) | cấu hình | Dừng, trả kết quả từng phần. |
| Wall-clock timeout | cấu hình | Hủy nhánh treo, trả phần đã xong. |
| Trùng tool call | — | Phát hiện call trùng (tool+args) → short-circuit, không tốn bước. |
| "Done" tiêu chí | — | Khi `required_data` đã đủ và data_validator pass → final_answer. |

### 6.3. Tiêu chí "Done"
Loop coi là hoàn tất khi: mọi `required_data` của Intent Object đã có dữ liệu hợp lệ **và** đã qua data_validator **và** answer_composer tạo được câu trả lời. Nếu không đạt trong budget → trả lời từng phần kèm lý do và đề nghị user bổ sung chi tiết.

---

## 7. Planner — Kế hoạch tường minh (DAG)

### 7.1. System Data Dictionary (phụ thuộc cốt lõi)
🎯 Một tài liệu/cấu trúc mô tả toàn bộ dữ liệu hệ thống để intent & planner đọc:
- Danh sách bảng, cột, ý nghĩa nghiệp vụ, enum, đơn vị.
- Quan hệ khóa ngoại, join phổ biến.
- Từ điển đồng nghĩa tiếng Việt → tên cột (vd "tồn kho" → `inventory.quantity`).
- Cập nhật tự động từ schema DB + chú thích thủ công; có version.

### 7.2. 🎯 Plan là DAG, không phải danh sách tuyến tính
Planner nhận Intent Object, sinh **Plan Graph**:

```jsonc
{
  "nodes": [
    { "id": "n1", "tool": "sql_subagent", "needs": [], "input_spec": {...}, "output_expect": "rows: doanh thu theo tháng" },
    { "id": "n2", "tool": "sql_subagent", "needs": [], "input_spec": {...}, "output_expect": "rows: tồn kho hiện tại" },
    { "id": "n3", "tool": "data_validator", "needs": ["n1","n2"] },
    { "id": "n4", "tool": "answer_composer", "needs": ["n3"] }
  ]
}
```
- Node không có `needs` chung → **chạy song song** (P4).
- Mỗi node khai báo rõ **input cần** và **output kỳ vọng** → dễ kiểm tra, dễ replan.

### 7.3. Replan
Khi một tool báo "kết quả sai / cần xem lại require" (vd data_validator phủ định, SQL review phủ định nhiều lần), harness:
1. Đọc lại Intent Object + observation.
2. Sửa node lỗi (đổi input_spec) hoặc thêm node (vd thêm bước clarify).
3. Nếu mơ hồ vượt ngưỡng → quay lại HITL với user, confirm rồi tiếp.

---

## 8. Catalog Tool/Subagent

| Tool/Subagent | Nhiệm vụ | Input | Output |
|---|---|---|---|
| **intent** | Phân tích ý định, sinh Intent Object, chấm confidence | require + memory + dictionary | Intent Object |
| **planner** | Sinh Plan Graph (DAG) từ Intent Object | Intent Object | Plan Graph |
| **sql_subagent** | Sinh & thực thi SQL đọc (mục 8.1) | input_spec | rows + meta |
| **data_validator** | 🎯 Đánh giá tính hợp lý/đủ của dữ liệu nghiệp vụ | rows + required_data | pass/fail + lý do |
| **chart** | Chuẩn hóa dữ liệu → biểu đồ/report | rows + chart_spec | chart payload |
| **catalog_draft** | Tạo nháp danh mục, chờ xác nhận | slots | draft + HITL |
| **inventory_draft** | Tạo nháp tồn kho, chờ xác nhận | slots | draft + HITL |
| **compact** | Nén hội thoại khi vượt ngưỡng context | messages | summary block |
| **answer_composer** | 🎯 Soạn câu trả lời giàu thông tin + gợi ý tiếp theo | observations | final answer |

### 8.1. SQL Subagent — pipeline self-correcting
```
sql_raw  ──▶  sql_review  ──▶  execute  ──▶  (rows)
   ▲             │  phủ định        │ rỗng
   └─────────────┘                 │
   regen (≤3 lần false)            └─▶ retry (≤2 lần) → review lại
```
- **sql_raw**: đọc System Data Dictionary + schema DB, soạn SQL raw (chỉ SELECT).
- **sql_review**: đối chiếu độc lập (đọc lại schema + chú thích + required_data của planner), đưa nguyên nhân phủ định và đề xuất sửa.
- **Budget**: tối đa **3** lần regen do review phủ định; nếu execute trả **rỗng**, retry tối đa **2** lần rồi gọi lại review.
- 🎯 **Dedup**: nếu SQL fingerprint trùng + cùng lý do lỗi → dừng, tránh lặp vô ích.
- 🎯 **Degrade**: khi không đạt, trả kết quả gần nhất hợp lệ + cảnh báo thay vì fail cứng.

### 8.2. 🎯 Data Validator (tách khỏi SQL)
Sau khi có rows, validator đánh giá **ngữ nghĩa nghiệp vụ**: số liệu có vô lý (âm, vượt trần), có thiếu cột so với `required_data`, có lệch thời gian không. Nếu fail → gửi feedback về sql_subagent (replan node). Nếu pass → chuyển answer_composer.

### 8.3. 🎯 Answer Composer
- Format nổi bật thông tin user cần (bảng/số liệu/điểm nhấn), không trả lời đơn điệu.
- Nêu rõ giả định đã tự suy (nếu có) ở mục 5.2.
- Luôn kèm **1–3 câu hỏi gợi ý tiếp theo** liên quan.
- Khi kết quả tệ (rỗng/lỗi) → đề nghị user nhập chi tiết hơn, kèm ví dụ.
- Toàn bộ text hướng tới user bằng tiếng Việt (vi-VN).

---

## 9. Memory — 3 tầng 🎯

| Tầng | Nội dung | Vòng đời | Dùng khi |
|---|---|---|---|
| **Working memory** | N lượt hỏi/đáp gần nhất (đề xuất N=6–8 cặp) | Trong phiên | Đính kèm mỗi require gửi lên LLM. |
| **Episodic (session)** | Bản tóm tắt nén của phiên: mốc thời gian, yêu cầu kéo dài, ràng buộc | Toàn phiên | Nạp đầu phiên + sau mỗi lần compact. |
| **Semantic (long-term)** | Sự kiện/khái niệm xuyên phiên của user (sở thích, entity hay dùng) | Bền, có expire | Recall theo độ liên quan khi cần. |

### 9.1. Cơ chế Compact
- Lưu hội thoại theo phiên + bộ nhớ phía user (gửi kèm N lượt gần nhất khi request).
- Khi vượt **ngưỡng token** (đề xuất ~70% context window của model) → gọi tool **compact**:
  - Nén toàn bộ thành một message có **ký hiệu `[COMPACT]`** để AI biết đọc trước tin gần đây.
  - Tóm tắt phải giữ: đủ ý, mốc thời gian, yêu cầu có tính kéo dài, ràng buộc, kết quả quan trọng.
- 🎯 Compact theo tầng: nén working → episodic, không nén cụt nội dung đang dở.

### 9.2. 🎯 Persistence
- Checkpoint state theo `thread_id` để loop có thể tạm dừng (HITL) và phục hồi sau restart.
- Working/episodic memory persist; semantic memory ở store riêng (vd vector store).

---

## 10. HITL — Pause / Resume bền 🎯

### 10.1. Khi nào HITL
- Mơ hồ vượt ngưỡng (mục 5.2).
- Trước **mọi thao tác ghi** (catalog/inventory draft): hiển thị nháp, chờ xác nhận.
- Khi replan cần user xác nhận lựa chọn.

### 10.2. Cơ chế
1. Harness phát sự kiện HITL kèm `resume_token` + payload nháp, **persist** trạng thái loop theo `thread_id`.
2. Loop tạm dừng (không tốn budget chờ).
3. User trả lời → harness nạp lại checkpoint, gắn câu trả lời vào memory, **resume đúng node** đang chờ.
4. Nếu phiên hết hạn/server restart mà mất checkpoint → báo lỗi rõ ràng, đề nghị tạo lại nháp.

### 10.3. Trải nghiệm
- Câu hỏi confirm luôn kèm **option khác** để user chọn nhanh.
- Hiển thị rõ điều sẽ thực hiện nếu xác nhận (nhất là thao tác ghi).

---

## 11. Bảo mật & Guardrails

| # | Guardrail | Cơ chế |
|---|---|---|
| G1 | **Chỉ đọc với data_query** | Allowlist: chỉ SELECT; chặn DDL/DML (`insert/update/delete/drop/truncate/alter/create`), chặn nhiều câu lệnh `;`. |
| G2 | 🎯 **Phân quyền tenant/role** | Enforce ở Backend (RLS theo tenant) **và** kiểm tra capability ở harness theo role (owner/staff). AI không bypass auth. |
| G3 | **Ghi qua HITL** | Mọi mutation đi qua draft → xác nhận → apply; có audit log. |
| G4 | 🎯 **Chống prompt-injection** | Tách "dữ liệu user" khỏi "chỉ thị hệ thống"; bỏ qua chỉ thị nhúng trong nội dung dữ liệu; whitelist hành động. |
| G5 | **Bảo vệ dữ liệu nhạy cảm** | Hạn chế cột nhạy cảm (giá vốn, công nợ) theo quyền; không log PII thô. |
| G6 | **Idempotency** | Mutation có khóa idempotency để retry không nhân đôi. |

---

## 12. Quan sát & Vận hành (Observability)

- **Trace** mỗi turn: cây node, input/output rút gọn, latency, token, cost, ok/error, correlation id, tenant, thread.
- **Metrics**: p50/p95 latency theo intent; cost/turn; số lần retry; tỉ lệ HITL; tỉ lệ replan; tỉ lệ chạm budget.
- **Audit log**: cảnh báo khi chạm step/cost budget, khi guardrail chặn, khi HITL hết hạn.
- **Eval harness** 🎯: bộ câu hỏi vàng (golden set) cho intent/SQL/answer; chạy regression khi đổi prompt/model.

---

## 13. Yêu cầu phi chức năng & Hiệu suất 🎯

| # | Yêu cầu |
|---|---|
| N1 | **Tiered model routing**: model rẻ/nhanh cho intent & compact; model mạnh cho planner & SQL khó. |
| N2 | **Song song hóa**: nhánh DAG độc lập chạy đồng thời; async toàn trình, không chặn threadpool. |
| N3 | **Semantic cache**: cache kết quả tất định (schema explore, SQL theo fingerprint+tenant) để giảm độ trễ & chi phí. |
| N4 | **Streaming-first**: trả progress theo SSE (đang chạy tool gì), rồi stream câu trả lời cuối. |
| N5 | **Latency mục tiêu**: đặt SLO p95 theo intent; degrade trả từng phần khi vượt. |
| N6 | **Token budget**: theo dõi token mỗi step; compact chủ động trước khi tràn context. |

---

## 14. Xử lý lỗi & Suy giảm mềm (Graceful degradation)

- Tool lỗi → ghi observation lỗi, để planner replan thay vì sập cả turn.
- LLM lỗi/timeout → retry có backoff; sau ngưỡng → trả lời từ observation đã có.
- Không có kết quả → answer_composer giải thích và đề nghị user làm rõ.
- Mọi lỗi hướng user đều bằng tiếng Việt, có mã lỗi nội bộ để truy vết.

---

## 15. Quyết định đã chốt (Resolved Defaults)

> Các giá trị mặc định được đề xuất dưới đây để có thể triển khai ngay. Tất cả đều **cấu hình được** qua settings; chủ sở hữu có thể tinh chỉnh sau khi đo thực tế.

| # | Quyết định | Giá trị chốt | Lý do |
|---|---|---|---|
| D1 | Ngưỡng confidence | HITL khi `< 0.75`; tự suy luận `0.75–0.9`; chạy thẳng `≥ 0.9` | Cân bằng giữa hỏi quá nhiều (phiền user) và đoán sai. |
| D2 | Ngưỡng ambiguity entity | HITL khi điểm khớp `< 0.6` | Dưới 0.6 thường là đoán nhầm danh mục. |
| D3 | N lượt working memory | **6 cặp** hỏi/đáp gần nhất | Đủ ngữ cảnh đa số hội thoại ERP, chưa tốn context. |
| D4 | Ngưỡng compact | khi context đạt **70%** cửa sổ model | Còn biên an toàn cho câu trả lời + tool output. |
| D5 | Long-term memory store | **pgvector** trên Postgres sẵn có; expire 90 ngày không truy cập | Tận dụng hạ tầng hiện có, không thêm dịch vụ mới. |
| D6 | Chính sách PII | Không lưu PII thô vào semantic memory; chỉ lưu preference/entity-id | Giảm rủi ro lộ dữ liệu khách hàng. |
| D7 | Cột nhạy cảm | `owner`: full; `staff`: ẩn giá vốn, công nợ, lãi/lỗ (giá vốn `products.cost_price`, công nợ `finance_ledger`, margin) | Theo phân quyền nghiệp vụ ERP. |
| D8 | SLO latency p95 | data_query **≤ 8s**; chart_report **≤ 12s**; chat **≤ 3s** | Mức chấp nhận được cho trợ lý nội bộ. |
| D9 | Budget/turn | step **10**, token **theo 70% model**, cost **≤ $0.05/turn**, timeout **30s** | Chặn loop tốn kém, vẫn đủ cho tác vụ phức tạp. |
| D10 | Tiered model routing | intent/compact: **Haiku**; planner/sql/compose: **Sonnet**; chỉ leo **Opus** khi replan ≥ 2 lần | Tối ưu chi phí/độ chính xác theo độ khó việc. |
| D11 | Budget SQL self-correct | review-fail regen **≤ 3**; empty-result retry **≤ 2** | Đủ để tự sửa, không lặp vô hạn. |

---

## 16. Tài liệu ngoài cần bổ sung (Knowledge Assets)

> Đây là các **artifact dữ liệu/tri thức** mà tool & subagent phải đọc để hoạt động đúng. Thiếu chúng thì intent/planner/sql sẽ đoán mò. Ưu tiên theo mức độ chặn.

### 16.1. 🔴 Bắt buộc trước khi chạy (P0)

| # | Tài liệu | Phục vụ tool/subagent | Nội dung cần có | Định dạng đề xuất |
|---|---|---|---|---|
| K1 | **System Data Dictionary** | intent, planner, sql_subagent | Mọi bảng/cột + ý nghĩa nghiệp vụ, kiểu dữ liệu, đơn vị, khóa ngoại, join phổ biến | YAML/JSON sinh tự động từ schema + chú thích tay; có `version` |
| K2 | **Từ điển đồng nghĩa VI → cột** | intent (resolve entity), sql_subagent | "tồn kho"→`inventory.quantity`, "doanh thu"→`sales_orders.total`, "công nợ"→`finance_ledger`... | bảng mapping `term → table.column` + alias |
| K3 | **Enum & mã trạng thái** | sql_subagent, data_validator | Liệt kê enum order_status, payment_status, draft_status... + nhãn tiếng Việt | JSON `{enum: {code: label_vi}}` |
| K4 | **Catalog danh mục thực** (embeddings) | intent (fuzzy/semantic match) | Tên products, categories, suppliers, customers thật để chấm điểm khớp entity | vector index (pgvector) refresh định kỳ |
| K5 | **SQL allowlist & quy tắc an toàn** | guardrail, sql_subagent | Bảng/cột được phép đọc theo role; pattern cấm; giới hạn LIMIT mặc định | YAML policy |
| K6 | **Capability / RBAC matrix** | guardrail, harness | role (owner/staff) × hành động/cột được phép | bảng quyền |

### 16.2. 🟡 Cần để chất lượng cao (P1)

| # | Tài liệu | Phục vụ | Nội dung |
|---|---|---|---|
| K7 | **Few-shot ví dụ SQL** | sql_subagent | 15–30 cặp (câu hỏi VI → SQL đúng) phủ các intent phổ biến, làm prompt example |
| K8 | **Quy tắc nghiệp vụ / công thức** | data_validator, sql_subagent | Định nghĩa "doanh thu", "lợi nhuận", "tồn an toàn", kỳ tài chính, cách tính margin |
| K9 | **Chart spec catalog** | chart tool | Loại biểu đồ hợp lệ theo shape dữ liệu (time_series→line, phân bổ→bar/pie) |
| K10 | **Mẫu câu trả lời (answer templates)** | answer_composer | Khung format cho từng intent + cách gợi ý câu hỏi tiếp theo |
| K11 | **Draft slot schema** | catalog_draft, inventory_draft | Trường bắt buộc/tùy chọn khi tạo nháp + ràng buộc hợp lệ |
| K12 | **Golden eval set** | eval harness | 30–50 câu hỏi vàng + đáp án mong đợi cho regression khi đổi prompt/model |

### 16.3. 🟢 Bổ trợ (P2)

| # | Tài liệu | Phục vụ | Nội dung |
|---|---|---|---|
| K13 | **ERP domain guide** | intent, answer_composer | Mô tả luồng nghiệp vụ (nhập kho → bán → công nợ) để hiểu ngữ cảnh câu hỏi |
| K14 | **Bảng đơn vị & định dạng VI** | answer_composer, chart | Định dạng tiền tệ VND, ngày tháng, đơn vị đo, cách hiển thị số |
| K15 | **Lịch sử intent ↔ tool thành công** | planner | Thống kê plan nào hiệu quả cho intent nào, để planner học theo |

### 16.4. Nguồn & cách duy trì
- **K1, K3, K4**: sinh **tự động** từ schema/DB Postgres (có job refresh), tránh lệch khi DB đổi.
- **K2, K7, K8, K10, K13**: biên soạn **thủ công** bởi người hiểu nghiệp vụ; review định kỳ.
- **K5, K6**: đồng bộ với phân quyền Backend (nguồn sự thật là Backend, tài liệu chỉ phản chiếu).
- Mọi tài liệu có **version**; harness log version đã dùng vào trace để truy vết khi kết quả sai.

---

## 17. Phụ lục — Hợp đồng dữ liệu chính

**Intent Object** (mục 5.1), **Plan Graph** (mục 7.2), **Tool Result**:
```jsonc
{
  "ok": true,
  "output": { /* dữ liệu cấu trúc của tool */ },
  "observation_text": "tóm tắt cho LLM đọc",
  "cost": { "tokens": 0, "latency_ms": 0 },
  "pending_hitl": null,        // hoặc { event_name, payload, resume_token }
  "error": null
}
```

> Mọi tool tuân theo cùng một `Tool Result` để harness điều phối, trace, và replan đồng nhất.
