# API — Thông báo in-app (danh sách, đánh dấu đã đọc) — PRD admin-notifications

> **Trạng thái:** Draft (đồng bộ SRS `backend/docs/srs/SRS_PRD_admin-notifications-entity-dialogs.md`)  
> **Base:** `/api/v1/notifications`  
> **Envelope:** [`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md)

---

## 1. `GET /api/v1/notifications`

**Query:** `page` (default 1), `limit` (default 20, max 100), `unreadOnly` (optional `true`).

**Auth:** Bearer JWT — chỉ trả thông báo của `sub`.

**Response `data`:** `items[]` với `id`, `notificationType`, `title`, `message`, `read`, `referenceType`, `referenceId`, `createdAt`; thêm `page`, `limit`, `total`, `unreadTotal`.

**Giá trị `notificationType` (PRD / Flyway V39):** `StockReceiptPendingApproval`, `StockDispatchPendingApproval`, `StockDispatchShortage` (và các loại legacy: `SystemAlert`, `PasswordResetRequest`, …).

**Tham chiếu thực thể:** `referenceType` + `referenceId` — `StockReceipt` / `StockDispatch` để Mini-ERP mở dialog phiếu.

---

## 2. `PATCH /api/v1/notifications/{id}`

**Auth:** Bearer JWT.

**Thành công `200`:** `data` `{}`, `message` đánh dấu đã đọc.

**Lỗi:** `404` nếu không thuộc user.

---

## 3. `POST /api/v1/notifications/mark-all-read`

**Auth:** Bearer JWT.

**Thành công `200`:** đánh dấu đọc toàn bộ thông báo của user.

---

## 4. Luồng FE (Mini-ERP Header)

1. Click thông báo có `referenceType` = `StockReceipt` hoặc `StockDispatch` → gọi `GET` chi tiết phiếu tương ứng.  
2. Thành công → mở dialog nghiệp vụ → `PATCH` đã đọc.  
3. Thất bại → toast, **không** PATCH.
