# PRD (draft) — Task005: Spring relay ↔ FastAPI ↔ FE chat (SSE)

**Trạng thái:** DRAFT — chờ Owner chọn **A / B / C / pick optimal** (HITL G-AI-PLAN).  
**Task:** Task005  
**Bối cảnh:** Phân tích tích hợp trước đó: Spring `AiChatRelayController` gọi `GET {AI_PYTHON_BASE_URL}/v1/chat/stream?q=&cid=` và kỳ vọng SSE `delta`/`done`/`error`; FastAPI Task004 chỉ có `POST /api/v1/ai/chat/stream` (JSON + JWT + event `partial_answer`/`final_answer`). FE `EventSource` gọi Spring `GET /api/v1/ai/chat/stream`.

**Ranh giới `ai_python` (lean `/orchestrate`):** Code mặc định chỉ dưới `ai_python/`. Mọi sửa `backend/smart-erp` hoặc `frontend/mini-erp` = **handoff AI_BRIDGE** hoặc task repo gốc — ghi rõ trong từng option.

---

## 1. Overview

Đồng bộ **điểm chạm** giữa relay SSE hiện có và dịch vụ LangGraph FastAPI để luồng chat trên UI hoạt động end-to-end, không phá vỡ API Task004 đã review (POST + JWT).

## 2. Mục tiêu định lượng

| ID | Tiêu chí | Đo |
| :--- | :--- | :--- |
| NFR-01 | Relay Spring → Python không còn 404 do sai path/method | HTTP 200 + stream |
| NFR-02 | FE nhận `delta` text và `done` (tương thích `aiChatSse.ts`) | Manual / test tích hợp |
| NFR-03 | POST `/api/v1/ai/chat/stream` (Task004) vẫn hoạt động | `pytest` Task004 |
| NFR-04 | Prod: không mở relay ẩn danh không kiểm soát | Cấu hình env rõ ràng |

## 3. Spec chức năng (tóm tắt)

- Endpoint tương thích relay: **GET** `/v1/chat/stream` — query `q` (bắt buộc), `cid` (tuỳ chọn → map `thread_id`).
- Phản hồi **text/event-stream** với tên sự kiện: `delta` (payload = đoạn text mới), `done`, `error` (payload = thông báo).
- Map nội bộ sang `LangGraphRuntime.stream` + state giống `ChatRequest` (metadata mặc định an toàn cho dev relay).
- Auth: **chỉ bật** khi `AUTH_DEV_BYPASS=true` **hoặc** header `Authorization` hợp lệ (tùy option); prod relay tin cậy qua network + Spring.

## 4. Kiến trúc — Option A / B / C

### Option A — **Chỉ `ai_python` (khuyến nghị cho lean / đóng nhanh lỗi relay)**

- Thêm module route (ví dụ `app/api/relay_routes.py`) mount **ngoài** prefix Task004: `GET /v1/chat/stream`.
- Khi `AUTH_DEV_BYPASS=true`: dùng metadata cố định relay (`user_id`/`tenant_id` từ env mới ví dụ `RELAY_DEFAULT_USER_ID` / `RELAY_DEFAULT_TENANT_ID`) + `schema_version=v1`.
- Consumer `runtime.stream`, theo dõi `final_answer` trong partial updates; emit `delta` = phần suffix mới so với lần trước; khi stream kết thúc → `done`.
- **Hạn chế:** Token-by-token không có nếu graph dùng `invoke_text` (câu trả lời có thể đến một cục); vẫn đủ cho MVP.
- **Out-of-scope:** Không sửa Spring/FE.

### Option B — **Chuẩn hóa contract Task004 (POST + JWT) trên toàn stack**

- Spring relay đổi sang `POST` Python `/api/v1/ai/chat/stream`, forward `Authorization` + body JSON.
- FE đổi từ `EventSource` sang `fetch` + `ReadableStream` hoặc thư viện SSE client gửi header Bearer.
- **Phạm vi:** `backend/` + `frontend/` + tài liệu bridge — **ngoài** lean `/orchestrate` chỉ `ai_python`; cần session **AI_BRIDGE** hoặc task DEV repo gốc.

### Option C — **Hybrid**

- Python: giữ GET `/v1/chat/stream` (như A) **và** chấp nhận optional `Authorization` để khi tắt bypass vẫn enforce JWT.
- Spring: bổ sung forward header Bearer (sửa Java).
- **Phạm vi:** `ai_python` + `backend/` — vẫn cần handoff nếu driver tuân thủ “chỉ ai_python”.

## 5. Task checklist (sau khi Owner chọn option)

- [ ] Khóa option trong mục §6 (final).
- [ ] AI_BA → SRS Task005.
- [ ] AI_PM → `TASKS/Task005.md` + `docs/task005/`.
- [ ] AI_TECH_LEAD → ADR (số kế tiếp trong `docs/adr/`).
- [ ] AI_DEVELOPER → code + `pytest` + ruff/mypy theo instruction.
- [ ] AI_CODE_REVIEWER → `docs/task005/05-code-review/CODE_REVIEW_Task005.md`.

## 6. Owner decision (HITL — điền sau khi chọn)

**Đã chọn:** _(chờ: A / B / C / pick optimal)_  

**Ghi chú:** `pick optimal` = chấp nhận **Option A** (khuyến nghị) trừ khi Owner chỉnh sửa ngược tại đây.

---

**Recommendation (Planner):** **Option A** để khép relay trong một PR dev, tránh chạm `backend/`/`frontend/` trong gate lean; sau đó mở Option B/C cho hardening bảo mật qua AI_BRIDGE.
