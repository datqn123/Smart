# 📄 API SPEC: `GET /api/v1/stock-receipts` — Danh sách phiếu nhập kho - Task013

> **Trạng thái**: Draft  
> **Feature**: Inventory / **UC7** — màn **Phiếu nhập kho** (`InboundPage`, `ReceiptTable`)  
> **Tags**: RESTful, StockReceipts, Pagination, Filter

---

## 1. Mục tiêu Task

- **Nghiệp vụ**: Cung cấp **danh sách phiếu nhập kho** có lọc theo từ khóa, trạng thái, khoảng ngày, nhà cung cấp và **phân trang / infinite scroll** thay cho mock `mockStockReceipts` + `filterReceipts` + `paginateReceipts` phía client.
- **Ai được lợi**: nhân viên kho / Owner xem và mở chi tiết; đồng bộ với bảng `StockReceipts` + join hiển thị.
- **Phạm vi Task này**: **chỉ** `GET /stock-receipts` (read-only).
- **Out of scope**: chi tiết một phiếu → [`API_Task015_stock_receipts_get_by_id.md`](API_Task015_stock_receipts_get_by_id.md); tạo/sửa/xóa → Task014,016,017; gửi duyệt → Task018; phê duyệt/từ chối → Task019,020; danh sách NCC/SP → `GET /suppliers`, `GET /products` (§4.14, §4.9).

---

## 2. Mục đích Endpoint

**`GET /api/v1/stock-receipts`** trả về **các phiếu nhập** trong phạm vi quyền, đủ cột để render bảng: mã phiếu, NCC, ngày nhập, người tạo, số HĐ, **số dòng hàng**, tổng tiền, trạng thái.

**Khi nào gọi**: mở màn Phiếu nhập kho; đổi bộ lọc / tìm kiếm; tải thêm trang (scroll); sau khi POST/PATCH/DELETE/Submit/Approve/Reject thành công.

**Sau khi thành công**: client nhận `items` + `page` / `limit` / `total` (hoặc cursor — mặc định offset).

**Endpoint này KHÔNG:**

- Không trả **đầy đủ** từng dòng `StockReceiptDetails` (tránh payload lớn) — dùng `lineCount`; chi tiết dòng → **Task015**.
- Không ghi DB.

---

## 3. Tham chiếu

**Khung thiết kế**: [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) §2–§3, **§4.8**.  
**DB**: [`Database_Specification.md`](../UC/Database_Specification.md) §17 `StockReceipts` (gồm `rejection_reason`, `reviewed_at`, `reviewed_by` sau migration), §18 `StockReceiptDetails`, `Suppliers`, `Users`.

**UI**: `mini-erp/src/features/inventory/pages/InboundPage.tsx`, `ReceiptTable.tsx`.

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.8** |
| **Endpoint** | `/api/v1/stock-receipts` |
| **Method** | `GET` |
| **Authentication** | `Bearer` (bắt buộc) |
| **RBAC** | Owner, Staff, Admin — đọc phiếu trong phạm vi quyền UC7 |
| **Use Case Ref** | UC7 |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
```

### 5.2 Query parameters

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
| :------ | :--- | :------- | :------- | :---- |
| `search` | string | Không | — | `receipt_code` ILIKE hoặc `invoice_number` |
| `status` | string | Không | `all` | `all`, `Draft`, `Pending`, `Approved`, `Rejected` |
| `dateFrom` | string (YYYY-MM-DD) | Không | — | `receipt_date >= dateFrom` |
| `dateTo` | string (YYYY-MM-DD) | Không | — | `receipt_date <= dateTo` |
| `supplierId` | number | Không | — | Lọc `supplier_id` |
| `mine` | boolean (query) | Không | `false` | Khi `true`: chỉ phiếu có `staff_id` = **JWT `subject`** (người tạo); không dùng `staffId` do client gửi |
| `page` | number (int ≥ 1) | Không | `1` | |
| `limit` | number (int 1–100) | Không | `20` | |
| `sort` | string | Không | `createdAt:desc` | Whitelist: `id:asc`\|`id:desc`, `createdAt:asc`\|`createdAt:desc` |

### 5.3 Request body

_Không có_

---

## 6. Ánh xạ UI → endpoint này

| Khu vực UI | Query / `data` |
| :----------- | :-------------- |
| Ô tìm kiếm | `search` |
| Lọc trạng thái | `status` |
| Lọc ngày | `dateFrom`, `dateTo` |
| Lọc NCC (khi có dropdown id) | `supplierId` |
| Checkbox «Chỉ phiếu của tôi» (Inbound) | `mine=true` |
| Thứ tự danh sách (Inbound) | `sort=createdAt:desc` (mặc định BE khi không gửi `sort` tương đương tạo mới nhất trước) |
| Cột “Dòng SP” | `data.items[].lineCount` *(FE nên dùng field này; không phụ thuộc mảng `details` trên list)* |
| Infinite scroll | tăng `page` hoặc tăng `limit` theo policy FE |

---

## 7. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "receiptCode": "PN-2026-0001",
        "supplierId": 1,
        "supplierName": "Công ty TNHH Vinamilk",
        "staffId": 5,
        "staffName": "Nguyễn Văn A",
        "receiptDate": "2026-04-20",
        "status": "Pending",
        "invoiceNumber": "HD-001",
        "totalAmount": 12500000,
        "lineCount": 3,
        "notes": null,
        "approvedBy": null,
        "approvedByName": null,
        "approvedAt": null,
        "reviewedBy": null,
        "reviewedByName": null,
        "reviewedAt": null,
        "rejectionReason": null,
        "createdAt": "2026-04-20T08:00:00Z",
        "updatedAt": "2026-04-20T09:00:00Z"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 42
  },
  "message": "Thành công"
}
```

---

## 8. Logic nghiệp vụ & Database (Business Logic)

### 8.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. **Validate query** → **400** + `details` nếu sai `status`, ngày, `limit`.
3. **`COUNT(*)`** dùng **cùng** `FROM` / `JOIN` / `WHERE` như bước 4 (tránh lệch `total` với trang `items`).
4. **`SELECT`** trang — `FROM stock_receipts sr JOIN suppliers s ON … JOIN users u_staff ON u_staff.id = sr.staff_id LEFT JOIN users u_appr ON u_appr.id = sr.approved_by LEFT JOIN users u_rev ON u_rev.id = sr.reviewed_by` + `WHERE` RBAC + filters; cột: `sr.id`, `sr.receipt_code`, `sr.supplier_id`, `s.name`, `sr.staff_id`, `u_staff.full_name`, `sr.receipt_date`, `sr.status`, `sr.invoice_number`, `sr.total_amount`, `sr.notes`, `sr.approved_by`, `u_appr.full_name`, `sr.approved_at`, `sr.reviewed_by`, `u_rev.full_name`, `sr.reviewed_at`, `sr.rejection_reason`, `sr.created_at`, `sr.updated_at`, `(SELECT COUNT(*)::int FROM stock_receipt_details d WHERE d.receipt_id = sr.id) AS line_count`.
5. Map snake_case → **camelCase** cho JSON.

### 8.2 Các ràng buộc (Constraints)

- **Không** `SELECT *`.  
- Index gợi ý: `idx_sr_status`, `idx_sr_supplier`, `receipt_date`, `idx_sr_reviewed_at` (thêm nếu thiếu trong `schema.sql` / §17).  
- **Read-only**.

---

## 9. Lỗi (Error Responses)

#### 400 Bad Request

```json
{
  "success": false,
  "error": "BAD_REQUEST",
  "message": "Tham số truy vấn không hợp lệ",
  "details": {
    "status": "Giá trị phải là all, Draft, Pending, Approved hoặc Rejected"
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

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền xem danh sách phiếu nhập kho"
}
```

#### 404 Not Found

_Không áp dụng_ cho collection `GET /stock-receipts`.

#### 500 Internal Server Error

```json
{
  "success": false,
  "error": "INTERNAL_ERROR",
  "message": "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
}
```

---

## 10. Zod (query — FE)

```typescript
import { z } from "zod";

export const StockReceiptListQuerySchema = z.object({
  search: z.string().optional(),
  status: z.enum(["all", "Draft", "Pending", "Approved", "Rejected"]).optional(),
  dateFrom: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  dateTo: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  supplierId: z.coerce.number().int().positive().optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  sort: z.string().optional(),
});
```
