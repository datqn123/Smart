# AI API Contracts

Base path: `/api/v1/ai`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## POST /api/v1/ai/chat/stream

**Mô tả:** Relay chat AI với SSE stream (Server-Sent Events). Nhận message từ client, relay đến Python FastAPI LangGraph, stream token về qua SSE.

**Auth:** JWT (Bearer token trong `Authorization` header)

**Headers:**
- `Authorization: Bearer <accessToken>`
- `Content-Type: application/json`

**Request body:**
```json
{
  "message": "string (required) — Nội dung tin nhắn",
  "conversationId": "string (optional) — ID cuộc hội thoại (thread)",
  "interactionMode": "string (optional) — Chế độ tương tác (auto, clarify, ...)",
  "clarify": {
    "clarifyId": "string (optional) — ID yêu cầu làm rõ",
    "clarifyKind": "string (optional) — Loại làm rõ",
    "continuationContext": "object (optional) — Context tiếp nối",
    "suggestedRewrite": "string (optional) — Đề xuất viết lại"
  }
}
```

**Response:** `text/event-stream` — Các sự kiện SSE:
- `event: token` — Token text
- `event: error` — Lỗi
- `event: done` — Kết thúc stream

**Errors:** 401 (thiếu/invalid token), 502 (lỗi relay Python)

---

## POST /api/v1/ai/chat/transcribe

**Mô tả:** Nhận diện giọng nói (speech-to-text) qua multipart file upload, relay đến Python.

**Auth:** JWT (Bearer token trong `Authorization` header)

**Headers:**
- `Authorization: Bearer <accessToken>`
- `Content-Type: multipart/form-data`

**Request (multipart):**
- `file` (file, required) — File audio (wav, mp3, ...)
- `language` (string, optional) — Mã ngôn ngữ (vd: `vi`, `en`)

**Response 200:**
```json
{
  "text": "string — Nội dung đã nhận dạng"
}
```

**Errors:** 400 (thiếu file), 401 (token không hợp lệ), 502 (lỗi relay Python)

---

## POST /api/v1/ai/chat/synthesize

**Mô tả:** Tổng hợp giọng nói (text-to-speech), relay đến Python, trả về audio bytes.

**Auth:** JWT (Bearer token trong `Authorization` header)

**Headers:**
- `Authorization: Bearer <accessToken>`
- `Content-Type: application/json`

**Request body:**
```json
{
  "text": "string (required) — Nội dung cần chuyển thành giọng nói",
  "voice": "string (optional) — Giọng đọc (vd: female, male)"
}
```

**Response 200:** `audio/wav` — Binary audio data.

**Errors:** 400 (thiếu text), 401 (token không hợp lệ), 502 (lỗi relay Python)

---

## POST /api/v1/ai/catalog-drafts/validate

**Mô tả:** Kiểm tra tham chiếu dữ liệu trong draft danh mục trước khi tạo.

**Auth:** JWT + `can_use_ai`

**Request body:**
```json
{
  "entityType": "string (max 32, required) — Loại entity (vd: product, category)",
  "columns": "JsonNode (required) — Cấu trúc cột",
  "rows": "JsonNode (required) — Dữ liệu rows",
  "meta": "JsonNode (optional) — Metadata bổ sung",
  "conversationId": "string (max 128, optional) — ID hội thoại AI"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "ok": "boolean — true nếu tất cả tham chiếu hợp lệ",
    "issues": ["string — Danh sách vấn đề phát hiện"]
  },
  "message": "Tham chiếu hợp lệ"
}
```

**Errors:** 400 (validation), 403 (thiếu quyền)

---

## POST /api/v1/ai/catalog-drafts

**Mô tả:** Tạo draft danh mục mới.

**Auth:** JWT + `can_use_ai`

**Request body:**
```json
{
  "entityType": "string (max 32, required) — Loại entity",
  "columns": "JsonNode (required) — Cấu trúc cột",
  "rows": "JsonNode (required) — Dữ liệu rows",
  "meta": "JsonNode (optional) — Metadata bổ sung",
  "conversationId": "string (max 128, optional) — ID hội thoại AI"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "string — UUID draft",
    "entityType": "string",
    "status": "string — Trạng thái (draft, committed, expired)",
    "columns": "JsonNode",
    "rows": "JsonNode",
    "meta": "JsonNode",
    "commitResult": "JsonNode — null nếu chưa commit",
    "conversationId": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "expiresAt": "Instant"
  },
  "message": "Đã tạo nháp"
}
```

**Errors:** 400 (validation), 403 (thiếu quyền)

---

## GET /api/v1/ai/catalog-drafts/{id}

**Mô tả:** Lấy thông tin draft danh mục theo ID.

**Auth:** JWT + `can_use_ai`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "entityType": "string",
    "status": "string",
    "columns": "JsonNode",
    "rows": "JsonNode",
    "meta": "JsonNode",
    "commitResult": "JsonNode",
    "conversationId": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "expiresAt": "Instant"
  },
  "message": "Thành công"
}
```

**Errors:** 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/ai/catalog-drafts/{id}

**Mô tả:** Cập nhật draft danh mục (rows và columns).

**Auth:** JWT + `can_use_ai`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Request body:**
```json
{
  "rows": "JsonNode (required) — Dữ liệu rows cập nhật",
  "columns": "JsonNode (optional) — Cấu trúc cột cập nhật"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "entityType": "string",
    "status": "string",
    "columns": "JsonNode",
    "rows": "JsonNode",
    "meta": "JsonNode",
    "commitResult": "JsonNode",
    "conversationId": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "expiresAt": "Instant"
  },
  "message": "Đã lưu nháp"
}
```

**Errors:** 400 (validation), 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/ai/catalog-drafts/{id}/commit

**Mô tả:** Commit draft danh mục — tạo entity thật từ dữ liệu draft.

**Auth:** JWT + `can_use_ai`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Response 200:**
```json
{
  "success": true,
  "data": {
    "committedCount": "int — Số row commit thành công",
    "failedCount": "int — Số row thất bại",
    "skippedCount": "int — Số row bị bỏ qua",
    "outcomes": [
      {
        "rowId": "string — ID row trong draft",
        "success": "boolean",
        "createdEntityId": "int — ID entity đã tạo (nếu thành công)",
        "message": "string — Thông báo chi tiết",
        "fieldErrors": "JsonNode — Lỗi field (nếu có)"
      }
    ],
    "draft": "JsonNode — Draft sau commit"
  },
  "message": "Đã xử lý commit"
}
```

**Errors:** 400 (draft rỗng/đã commit), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/ai/catalog-drafts/{id}

**Mô tả:** Hủy (xóa) draft danh mục.

**Auth:** JWT + `can_use_ai`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đã hủy nháp"
}
```

**Errors:** 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/ai/inventory-drafts/validate

**Mô tả:** Kiểm tra tham chiếu dữ liệu trong draft phiếu kho trước khi tạo.

**Auth:** JWT + `can_use_ai` + `can_manage_inventory`

**Request body:**
```json
{
  "entityType": "string (max 32, required) — Loại entity (vd: goods-receipt, goods-issue)",
  "header": "JsonNode (required) — Dữ liệu header phiếu",
  "lineColumns": "JsonNode (required) — Cấu trúc cột dòng",
  "lines": "JsonNode (required) — Dữ liệu dòng",
  "meta": "JsonNode (optional) — Metadata bổ sung",
  "conversationId": "string (max 128, optional) — ID hội thoại AI"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "ok": "boolean — true nếu tất cả tham chiếu hợp lệ",
    "issues": ["string — Danh sách vấn đề phát hiện"]
  },
  "message": "Tham chiếu hợp lệ"
}
```

**Errors:** 400 (validation), 403 (thiếu quyền)

---

## POST /api/v1/ai/inventory-drafts

**Mô tả:** Tạo draft phiếu kho mới.

**Auth:** JWT + `can_use_ai` + `can_manage_inventory`

**Request body:**
```json
{
  "entityType": "string (max 32, required) — Loại entity",
  "header": "JsonNode (required) — Header phiếu",
  "lineColumns": "JsonNode (required) — Cấu trúc cột dòng",
  "lines": "JsonNode (required) — Dữ liệu dòng",
  "meta": "JsonNode (optional) — Metadata bổ sung",
  "conversationId": "string (max 128, optional) — ID hội thoại AI"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": "string — UUID draft",
    "entityType": "string",
    "status": "string — Trạng thái (draft, committed, expired)",
    "header": "JsonNode",
    "lineColumns": "JsonNode",
    "lines": "JsonNode",
    "meta": "JsonNode",
    "commitResult": "JsonNode — null nếu chưa commit",
    "conversationId": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "expiresAt": "Instant"
  },
  "message": "Đã tạo nháp phiếu kho"
}
```

**Errors:** 400 (validation), 403 (thiếu quyền)

---

## GET /api/v1/ai/inventory-drafts/{id}

**Mô tả:** Lấy thông tin draft phiếu kho theo ID.

**Auth:** JWT + `can_use_ai` + `can_manage_inventory`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "entityType": "string",
    "status": "string",
    "header": "JsonNode",
    "lineColumns": "JsonNode",
    "lines": "JsonNode",
    "meta": "JsonNode",
    "commitResult": "JsonNode",
    "conversationId": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "expiresAt": "Instant"
  },
  "message": "Thành công"
}
```

**Errors:** 403 (thiếu quyền), 404 (không tìm thấy)

---

## PATCH /api/v1/ai/inventory-drafts/{id}

**Mô tả:** Cập nhật draft phiếu kho.

**Auth:** JWT + `can_use_ai` + `can_manage_inventory`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Request body:**
```json
{
  "header": "JsonNode (optional) — Header cập nhật",
  "lineColumns": "JsonNode (optional) — Cấu trúc cột cập nhật",
  "lines": "JsonNode (required) — Dữ liệu dòng cập nhật"
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "entityType": "string",
    "status": "string",
    "header": "JsonNode",
    "lineColumns": "JsonNode",
    "lines": "JsonNode",
    "meta": "JsonNode",
    "commitResult": "JsonNode",
    "conversationId": "string",
    "createdAt": "Instant",
    "updatedAt": "Instant",
    "expiresAt": "Instant"
  },
  "message": "Đã lưu nháp"
}
```

**Errors:** 400 (validation), 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/ai/inventory-drafts/{id}/commit

**Mô tả:** Commit draft phiếu kho — tạo phiếu nhập/xuất kho thật từ dữ liệu draft.

**Auth:** JWT + `can_use_ai` + `can_manage_inventory`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Response 200:**
```json
{
  "success": true,
  "data": {
    "success": "boolean — Kết quả commit",
    "message": "string — Thông báo chi tiết",
    "createdReceiptId": "int — ID phiếu kho đã tạo (nếu thành công)",
    "receiptCode": "string — Mã phiếu kho",
    "draft": "JsonNode — Draft sau commit"
  },
  "message": "Đã xử lý commit"
}
```

**Errors:** 400 (draft rỗng/đã commit), 403 (thiếu quyền), 404 (không tìm thấy)

---

## DELETE /api/v1/ai/inventory-drafts/{id}

**Mô tả:** Hủy (xóa) draft phiếu kho.

**Auth:** JWT + `can_use_ai` + `can_manage_inventory`

**Path parameters:**
- `id` (UUID, required) — ID draft

**Response 200:**
```json
{
  "success": true,
  "data": {},
  "message": "Đã hủy nháp"
}
```

**Errors:** 403 (thiếu quyền), 404 (không tìm thấy)

---

## POST /api/v1/ai/db/sql/describe

**Mô tả:** Mô tả cấu trúc đối tượng database (table/view). MCP facade cho Python agent.

**Auth:** permitAll (dành cho internal Python agent; dùng network ACL trong production)

**Headers:**
- `X-Correlation-Id` (optional)

**Request body:**
```json
{
  "object_name": "string (required) — Tên đối tượng (table/view)"
}
```

**Response 200:**
```json
{
  "object_name": "string",
  "columns": [
    {
      "name": "string — Tên cột",
      "type": "string — Kiểu dữ liệu",
      "nullable": "boolean"
    }
  ],
  "summary": "string — Tóm tắt",
  "correlation_id": "string"
}
```

**Errors:** 400 (object không tồn tại)

---

## POST /api/v1/ai/db/sql/query-readonly

**Mô tả:** Thực thi truy vấn read-only theo template ID (an toàn, tham số hóa).

**Auth:** permitAll (dành cho internal Python agent; dùng network ACL trong production)

**Headers:**
- `X-Correlation-Id` (optional)

**Request body:**
```json
{
  "template_id": "string (required) — ID template truy vấn",
  "params": {
    "key": "value — Tham số truy vấn"
  }
}
```

**Response 200:**
```json
{
  "columns": [
    {
      "name": "string — Tên cột",
      "type": "string — Kiểu dữ liệu"
    }
  ],
  "rows": [
    ["array — Dữ liệu từng dòng"]
  ],
  "row_count": "int",
  "summary": "string — Tóm tắt kết quả",
  "correlation_id": "string"
}
```

**Errors:** 400 (template không tồn tại)

---

## POST /api/v1/ai/db/sql/query-readonly-raw

**Mô tả:** Thực thi truy vấn read-only raw SQL (chỉ SELECT, kiểm tra tại runtime).

**Auth:** permitAll (dành cho internal Python agent; dùng network ACL trong production)

**Headers:**
- `X-Correlation-Id` (optional)

**Request body:**
```json
{
  "query": "string (required) — Câu lệnh SQL (SELECT)",
  "max_rows": "int (optional) — Giới hạn số dòng trả về"
}
```

**Response 200:**
```json
{
  "columns": [
    {
      "name": "string",
      "type": "string"
    }
  ],
  "rows": [
    ["array"]
  ],
  "row_count": "int",
  "summary": "string",
  "correlation_id": "string"
}
```

**Errors:** 400 (SQL không phải SELECT/cú pháp sai)
