# PRD — Task003 `erp_db_read_rag`

| Field | Value |
| :--- | :--- |
| **Slug** | `erp_db_read_rag` |
| **Chosen architecture** | **Option A** — RAG-first; gọi `db-readonly` (MCP) có chọn lọc khi cần số liệu xác minh |
| **Implementation scope** | Chỉ `ai_python/` — **không** sửa `backend/`, **không** sửa `frontend/` |
| **SQL policy** | Dịch vụ Python **không** chứa / không tạo **SQL thô**; mọi truy vấn CSDL ERP qua MCP `db-readonly` theo contract (template / tham số đã kiểm soát) do tầng tích hợp sở hữu |
| **Encoding** | UTF-8 |

---

## 4.1. Project Overview

Dự án mở rộng luồng chat AI để người dùng **Admin** có thể hỏi về nghiệp vụ dự án, cấu trúc/khái niệm CSDL Smart ERP và **số liệu tổng hợp đúng** khi cần, bằng chiến lược **ưu tiên RAG** (tài liệu, mô tả schema/catalog đã chunk trong `vector-rag`) và chỉ gọi **`db-readonly`** khi intent yêu cầu xác minh số liệu trực tiếp từ ERP. Mọi truy cập CSDL thực đều read-only, có guardrail, không có đường ghi từ AI trong phạm vi task; tri thức RAG được làm mới **theo ngày** để cân bằng độ tươi và chi phí.

**Target users:** chỉ **người dùng có Role Admin** (toàn quyền dữ liệu theo brief); việc enforce role/tenant ở biên hệ thống (gateway/backend) là giả định tích hợp — task chỉ triển khai logic và MCP trong `ai_python` theo contract đầu vào (session, correlation, metadata khi có).

---

## 4.2. Specifications

### Functional requirements

1. **Luồng trả lời RAG-first:** Với mỗi lượt hội thoại hợp lệ, hệ thống lấy ngữ cảnh từ MCP `vector-rag` (tài liệu domain, mô tả schema/catalog) trước khi xem xét gọi `db-readonly`.
2. **Định tuyến intent sang DB read-only có chọn lọc:** Khi câu hỏi yêu cầu **số lượng / tổng hợp / giá trị hiện tại** mà RAG không đủ để đảm bảo đúng số, orchestration gọi `db-readonly` theo **template / tham số** được phép (không dựng chuỗi SQL tự do trong Python).
3. **Từ chối thao tác ghi:** Mọi yêu cầu chỉnh sửa, xóa, chèn dữ liệu ERP phải bị từ chối rõ ràng trong phản hồi; không gọi công cụ ghi (nếu sau này có route Write/HITL — ngoài scope triển khai task này).
4. **Không lộ bí mật:** Không đưa credential, chuỗi kết nối, hay dữ liệu nhạy cảm không cần thiết vào log/prompt; policy từ chối khi phát hiện yêu cầu lộ secret.
5. **Streaming / contract đầu ra:** Phản hồi user theo cơ chế streaming (hoặc JSON) **đồng bộ với contract hiện có** của dịch vụ chat trong `ai_python`; không bắt buộc hiển thị trích dẫn chunk id hay tên bảng cho user (theo Owner), nhưng **nội bộ** vẫn có thể giữ metadata nguồn phục vụ eval và debug.
6. **Làm mới tri thức RAG định kỳ:** Pipeline ingest / cập nhật nguồn vào `vector-rag` chạy theo lịch **tối thiểu mỗi ngày** (hoặc trigger tương đương) để giảm drift giữa tài liệu đã index và CSDL thực tế.
7. **Giải thích theo nhu cầu hội thoại:** Ưu tiên trả **đúng số** khi user hỏi số liệu; giải thích chi tiết schema/concept khi user chủ động hỏi thêm trong các lượt chat sau (không ép luôn giải thích dài trong mọi câu trả lời số).

### Non-functional requirements (NFRs) — quantified

| ID | NFR | Target / threshold |
| :--- | :--- | :--- |
| NFR-01 | **Độ trễ p95** (một lượt user → bắt đầu stream token đầu tiên) | Đường chỉ RAG: **p95 < 4 s**; đường có thêm 1 lần gọi `db-readonly` hợp lệ: **p95 < 10 s** (số liệu cuối cùng chốt theo ADR `G-AI-TL` nếu điều chỉnh) |
| NFR-02 | **Độ tin cậy** | Tỷ lệ lỗi 5xx trên lượt chat có MCP: **< 0,5%** trong môi trường staging trong 7 ngày đo liên tục (mẫu tối thiểu 200 lượt/tuần hoặc toàn bộ traffic nếu thấp hơn) |
| NFR-03 | **Eval chất lượng** (theo gate `G-AI-TST` / Design §6) | **≥ 80%** pass trên **≥ 30 prompt**, bao phủ **4 năng lực** trong Design Doc §6 (schema/glossary/tổng hợp có kiểm chứng số/guardrail) |
| NFR-04 | **An toàn MCP** | **0% HITL bypass** trong kịch bản red-team guardrail (`db-readonly`, từ chối ghi, từ chối SQL tự do từ phía agent Python) |
| NFR-05 | **RPO tri thức RAG** | Nội dung index không “cũ hơn” **24 giờ** so với lần ingest thành công gần nhất trong môi trường triển khai (ngoại lệ có log `stale_acknowledged`) |
| NFR-06 | **Chi phí & giới hạn gọi MCP** | Số lần gọi `db-readonly` trung bình mỗi lượt chat kiểu tra cứu chung: **≤ 1** khi không cần số; hard cap và chi phí token theo ADR TL (file caps / cost cap có giá trị số trong ADR) |
| NFR-07 | **Observability** | Mỗi lượt có `correlation_id` (hoặc tương đương) trong log; **không** ghi payload đầy đủ chứa PII cố định trừ khi đã masked; retention log ứng dụng **≥ 30 ngày** staging |

---

## 4.3. Tech stack

- **Frontend / UI:** Không chỉnh sửa trong Task003. Client chat hiện hữu gọi API/SSE của dịch vụ như đã có; PRD chỉ ràng buộc hành vi phía `ai_python`.
- **Backend / business logic (`ai_python/`):** Python, orchestration/agent graph theo conventions repo (LangGraph hoặc tương đương), client MCP cho `vector-rag` và `db-readonly`, policy layer (từ chối ghi/secret), router intent RAG-vs-DB.
- **Database & storage:** Không kết nối trực tiếp từ Python tới CSDL ERP. **Vector storage & chỉ mục** qua MCP `vector-rag`; **dữ liệu vận hành ERP** chỉ đọc qua MCP `db-readonly` theo contract template/tham số. Ingest có thể đọc nguồn tài liệu được phép (file nội bộ artifact, export snapshot — chi tiết path trong SRS/ADR) **không** chứa SQL thô trong service.

---

## 4.4. Task breakdown & dependency graph

**Thứ tự phụ thuộc gợi ý:** T1 → T2 → T3; T4 song song sau T2; T5 sau T3+T4; T6 sau T5; T7 sau T6; T8 cuối vòng chức năng; T9 theo điều kiện contract.

```text
[T1 MCP config] ──► [T2 Client wrappers]
                         │
[T4 Ingest scheduler] ───┼──► [T3 Router RAG-first]
                                       │
                                       ▼
                               [T5 Prompt & policy]
                                       │
                                       ▼
                               [T6 Observability]
                                       │
                                       ▼
                               [T7 Tests unit/feature]
                                       │
                                       ▼
                               [T8 Eval & red-team]
                                       │
                                       ▼
                       [T9 BRIDGE/API docs if contract đổi]
```

---

- [ ] **Task 1 — Cấu hình & secrets MCP (`vector-rag`, `db-readonly`)**

  - **Description:** Khai báo endpoint/credential MCP (qua env hoặc cơ chế secrets hiện có của `ai_python`), tách profile dev/staging; validate kết nối tối thiểu khi khởi động (fail-fast có thông điệp rõ).
  - **Input/Output:** Input: biến môi trường / file cấu hình theo convention repo. Output: module cấu hình được import bởi client MCP; log khởi tạo không lộ secret.
  - **Acceptance Criteria:** Khởi động service với cấu hình hợp lệ không crash; thiếu biến bắt buộc → exit code ≠ 0 và thông báo tên biến; không có chuỗi secret in ra stdout ở mức INFO.

---

- [ ] **Task 2 — Client MCP: `vector-rag` và `db-readonly`**

  - **Description:** Lớp gọi MCP có timeout, retry có giới hạn, mapping lỗi sang mã lỗi nội bộ; **cấm** ghép SQL thô trong Python — chỉ truyền `template_id` + tham số kiểu an toàn theo contract MCP.
  - **Input/Output:** Input: query người dùng đã chuẩn hoá / intent + tham số từ router. Output: danh sách chunk/score từ `vector-rag`; result set đã giới hạn cột/hàng từ `db-readonly` (theo contract).
  - **Acceptance Criteria:** Unit test mock MCP: happy path + timeout + lỗi 4xx/5xx; grep CI đảm bảo không có pattern SQL keyword nối chuỗi (ví dụ `SELECT`/`INSERT` động) trong `ai_python/app` ngoài chuỗi constant test/fixture được liệt kê whitelist trong script check (nếu có).

---

- [ ] **Task 3 — Router intent RAG-first + điều kiện gọi `db-readonly`**

  - **Description:** Sau bước retrieve RAG, quyết định có cần gọi DB read-only: ví dụ intent “đếm/tổng/giá trị hiện tại/tháng này” và RAG không trả grounding đủ; giới hạn tối đa số round-trip DB mỗi lượt theo NFR-06.
  - **Input/Output:** Input: tin nhắn user + chunks RAG + (tuỳ chọn) lịch sử ngắn. Output: quyết định boolean + `template_id` + params hoặc lý do không gọi DB.
  - **Acceptance Criteria:** Bộ test feature/fixture: ≥ 10 scenario (mock) phân biệt chỉ RAG vs RAG+DB; không gọi `db-readonly` khi câu hỏi chỉ định nghĩa khái niệm; có gọi khi scenario số liệu yêu cầu ground truth (theo tên case đã định nghĩa).

---

- [ ] **Task 4 — Pipeline ingest / refresh RAG (chu kỳ ngày)**

  - **Description:** Job hoặc entrypoint lên lịch **mỗi 24h** đưa tài liệu schema/catalog/domain đã được phép vào `vector-rag` (chunk, metadata); loại trừ nội dung bí mật; ghi log lần ingest thành công phục vụ NFR-05.
  - **Input/Output:** Input: nguồn tài liệu theo path/cấu hình (SRS/ADR chi tiết). Output: trạng thái ingest + timestamp.
  - **Acceptance Criteria:** Chạy ingest trên môi trường dev/staging thành công end-to-end ít nhất 1 lần có bằng chứng log; thất bại retry hoặc báo cảnh báo rõ; không đẩy file chứa credential vào index.

---

- [ ] **Task 5 — Prompt an toàn & từ chối policy**

  - **Description:** System/developer prompt và bước kiểm nhanh trước khi stream: refuse write/refuse credential leakage; nhất quán với vai trò Admin (full data) nhưng vẫn tuân SIÊNG NFR audit.
  - **Input/Output:** Input: user message + ngữ cảnh RAG + (optional) kết quả `db-readonly`. Output: stream văn bản hợp lệ hoặc thông điệp từ chối có mã lý do nội bộ.
  - **Acceptance Criteria:** Test snapshot: các câu lệnh “UPDATE/DELETE/XÓA/ghi DB” bị từ chối 100% trong fixture; không inject được hướng dẫn lấy secrets qua MCP client.

---

- [ ] **Task 6 — Observability & correlation**

  - **Description:** Gắn `correlation_id`/`session_id` xuyên suốt chain; metric counter cho gọi RAG vs DB; log cấu trúc không chứa full PII — theo NFR-07.
  - **Input/Output:** Input: headers/context từ entrypoint HTTP/SSE. Output: log JSON lines hoặc tương đương + metric hooks (nếu repo đã có).
  - **Acceptance Criteria:** Một luồng request mẫu cho thấy cùng correlation trên ít nhất 3 điểm log; không có khóa `password`/`api_key` giá trị thật trong log mẫu.

---

- [ ] **Task 7 — Kiểm thử tự động (`pytest`, type/lint)**

  - **Description:** Viết/feature tests cho T2–T6; đạt coverage và `ruff`/`mypy` theo cổng `G-AI-DEV` hiện hành (≥ 70% coverage trên nhánh — trừ khi ADR miễn trừ phần).
  - **Input/Output:** Input: codebase + CI hoặc lệnh local. Output: báo cáo coverage và xanh pytest.
  - **Acceptance Criteria:** `pytest -q` xanh; `ruff check` và `mypy` không lỗi mới trong phạm vi thay đổi Task003.

---

- [ ] **Task 8 — Bộ đánh giá (eval) & red-team MCP**

  - **Description:** Bộ ≥ 30 prompt, nhãn expected behavior (RAG-only / RAG+DB / refuse); script chấm theo tiêu chí gate (≥ 80%); red-team prompts cho bypass guardrail MCP.
  - **Input/Output:** Input: môi trường staging + MCP credentials thử nghiệm. Output: báo cáo `% pass` và danh sách fail để chỉnh.
  - **Acceptance Criteria:** Đạt **NFR-03** và **NFR-04**; lưu kết quả chạy dưới dạng file báo cáo trong `ai_python/docs/` hoặc `ai_python/tests/eval_reports/` (theo convention PM/Tester).

---

- [ ] **Task 9 — Tài liệu BRIDGE/API (điều kiện: nếu đổi SSE hoặc schema MCP)**

  - **Description:** Nếu task làm đổi event SSE hoặc schema tool MCP mà downstream cần, sinh/ghi `ai_python/docs/api/bridge/BRIDGE_AI_Task003_erp_db_read_rag.md` đủ cột theo `AI_BRIDGE_AGENT_INSTRUCTIONS`.
  - **Input/Output:** Input: delta contract so với baseline. Output: file BRIDGE + (nếu cần) cập nhật README nội bộ agent (chỉ dưới `ai_python/`).
  - **Acceptance Criteria:** Gate `G-AI-BRIDGE` pass khi và chỉ khi có thay đổi contract; nếu **không** đổi contract, task được đánh dấu **N/A** trong báo cáo sync với lý do 1 dòng.

---

**End of PRD (§4.1–4.4).**
