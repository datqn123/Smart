# 📄 API SPEC: `POST /api/v1/stock-receipts/{id}/reject` — Từ chối phiếu nhập - Task020

> **Trạng thái**: Draft  
> **Feature**: **UC4** + **UC7** — từ chối phiếu `Pending` (`ReceiptDetailDialog` / `ReceiptDetailPanel`)

---

## 1. Mục tiêu Task

- Chuyển **`Pending` → `Rejected`**, lưu **`rejection_reason`**, **`reviewed_by`**, **`reviewed_at`**; **không** đụng `Inventory` / `FinanceLedger` / `approved_by` / `approved_at`.

- **Out of scope**: phê duyệt → Task019.

---

## 2. Mục đích Endpoint

**`POST /api/v1/stock-receipts/{id}/reject`** — cùng rule **Owner-only** với Task019 (JWT `role` = Owner + `can_approve`); SRS §6.

---

## 3. Overview

| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.5** |
| **Endpoint** | `/api/v1/stock-receipts/{id}/reject` |
| **Method** | `POST` |
| **Auth** | `Bearer` |
| **RBAC** | Giống Task019: `can_approve` + claim `role` = **Owner**; không phải Owner → **403**. |

---

## 4. Request body

```json
{
  "reason": "Số lượng không khớp hóa đơn gốc"
}
```

| Field | Kiểu | Bắt buộc | Mô tả |
| :---- | :--- | :------- | :---- |
| `reason` | string | Có | min 1, max 2000 (hoặc TEXT append vào `notes` + prefix) |

**Lưu lý do**: **`UPDATE StockReceipts`** ghi **`rejection_reason`** (cột chính, xem `Database_Specification.md` §17), đồng thời **`reviewed_at=NOW()`, `reviewed_by`** = user UC4. Có thể **nối thêm** vào `notes` cho người đọc cũ — không thay thế `rejection_reason` trên API.

---

## 5. Thành công — `200 OK`

`data` cùng shape Task015 với `status: "Rejected"`, **`rejectionReason`**, **`reviewedBy`**, **`reviewedAt`** đã ghi; `approvedBy` / `approvedAt` = **null**.

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** + RBAC UC4 → **403**.
2. **`SELECT id, status FROM StockReceipts WHERE id = ? FOR UPDATE`** — không có → **404**; `status <> 'Pending'` → **409**.
3. **`UPDATE StockReceipts SET status='Rejected', rejection_reason=?, reviewed_by=?, reviewed_at=NOW(), updated_at=NOW() WHERE id=?`** — `rejection_reason` lấy từ body `reason` (trim, max độ dài policy); `approved_by` / `approved_at` giữ NULL.
4. **`INSERT SystemLogs`** (WARNING hoặc INFO).
5. **`COMMIT`**.

### 7.2 Các ràng buộc (Constraints)

- Không xóa dòng detail (vẫn lưu để audit); không cộng kho.

---

## 8. Lỗi — 400 (thiếu reason), 401, 403, 404, 409, 500.

Ví dụ **403** (không phải Owner — cùng message Task017/Task019 / SRS §8.3):

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Chỉ tài khoản Owner mới được xóa phiếu (Nháp/Chờ duyệt), phê duyệt hoặc từ chối phiếu Chờ duyệt"
}
```

Ví dụ **400**:

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Vui lòng nhập lý do từ chối",
  "details": {
    "reason": "Trường reason là bắt buộc"
  }
}
```

---

## 9. Zod

```typescript
import { z } from "zod";
export const StockReceiptRejectBodySchema = z.object({
  reason: z.string().min(1).max(2000),
});
```
