# 📄 API SPEC: `GET /api/v1/stock-receipts/{id}` — Chi tiết phiếu nhập - Task015

> **Trạng thái**: Draft  
> **Feature**: UC7 — `ReceiptDetailDialog`, `ReceiptDetailPanel`, mở form sửa (hydrate)

---

## 1. Mục tiêu Task

- Trả về **một** phiếu nhập **đầy đủ** header + **mảng `details`** (join tên SP, SKU, đơn vị, `lineTotal`).
- **Out of scope**: danh sách → Task013; phê duyệt → Task019/020.

---

## 2. Mục đích Endpoint

**`GET /api/v1/stock-receipts/{id}`** phục vụ xem chi tiết / in / chuẩn bị **PATCH** (Draft).

**KHÔNG** thay danh sách phân trang.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8**; DB §17–§18 — header phiếu gồm **`rejection_reason`**, **`reviewed_at`**, **`reviewed_by`** (UC4 / lịch sử phê duyệt, [`Database_Specification.md`](../UC/Database_Specification.md) §17).

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Endpoint** | `/api/v1/stock-receipts/{id}` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | `hasAuthority('can_manage_inventory')` — xem **mọi** phiếu (không giới hạn theo người tạo). SRS: `backend/docs/srs/SRS_Task014-020_stock-receipts-lifecycle.md` §6. |
| **Use Case Ref** | UC7 |

---

## 5. Request

### 5.1 Headers — `Authorization: Bearer …`

### 5.2 Path — `id` (int, `StockReceipts.id`)

### 5.3 Query / Body — _Không có_

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 42,
    "receiptCode": "PN-2026-0042",
    "supplierId": 1,
    "supplierName": "Công ty TNHH Vinamilk",
    "staffId": 5,
    "staffName": "Nguyễn Văn A",
    "receiptDate": "2026-04-23",
    "status": "Pending",
    "invoiceNumber": "HD-2026-01",
    "totalAmount": 1080000,
    "notes": null,
    "approvedBy": null,
    "approvedByName": null,
    "approvedAt": null,
    "reviewedBy": null,
    "reviewedByName": null,
    "reviewedAt": null,
    "rejectionReason": null,
    "createdAt": "2026-04-23T10:00:00Z",
    "updatedAt": "2026-04-23T10:00:00Z",
    "details": [
      {
        "id": 1001,
        "receiptId": 42,
        "productId": 12,
        "productName": "Nước suối 500ml",
        "skuCode": "SKU-WAT-500",
        "unitId": 5,
        "unitName": "Chai",
        "quantity": 24,
        "costPrice": 45000,
        "batchNumber": "LOT-2026-01",
        "expiryDate": "2027-12-31",
        "lineTotal": 1080000
      }
    ]
  },
  "message": "Thành công"
}
```

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **`SELECT`** header `StockReceipts` (gồm `rejection_reason`, `reviewed_at`, `reviewed_by`, `approved_by`, `approved_at`) **JOIN** `suppliers` → tên NCC, **JOIN** `users u_staff` → người tạo, **LEFT JOIN** `users u_appr` ON `u_appr.id = sr.approved_by`, **LEFT JOIN** `users u_rev` ON `u_rev.id = sr.reviewed_by` (tên người xét duyệt / từ chối); **không** `SELECT *` bừa bãi — liệt kê cột.
3. **`details`**: join `StockReceiptDetails` với `Products`, `ProductUnits` như hiện tại.
4. Không thấy `id` → **404** (không trả **403** chỉ vì phiếu do người khác tạo).

### 7.2 Các ràng buộc (Constraints)

- Read-only; không lộ dữ liệu nhạy cảm.

---

## 8. Lỗi (Error Responses)

#### 400 Bad Request

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Mã phiếu không hợp lệ",
  "details": {
    "id": "Giá trị phải là số nguyên dương"
  }
}
```

#### 401 Unauthorized

```json
{
  "success": false,
  "error": "UNAUTHORIZED",
  "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn"
}
```

#### 403 Forbidden

Thiếu quyền module (vd. không có `can_manage_inventory`) — **không** dùng 403 để che phiếu của người khác.

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền truy cập chức năng này"
}
```

#### 404 Not Found

```json
{
  "success": false,
  "error": "NOT_FOUND",
  "message": "Không tìm thấy phiếu nhập kho yêu cầu"
}
```

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

---

## 9. Zod

```typescript
import { z } from "zod";
export const StockReceiptIdParamSchema = z.object({
  id: z.coerce.number().int().positive(),
});
```
