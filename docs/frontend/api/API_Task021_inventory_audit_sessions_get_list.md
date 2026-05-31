# 📄 API SPEC: `GET /api/v1/inventory/audit-sessions` — Danh sách đợt kiểm kê - Task021

> **Trạng thái**: Draft  
> **Feature**: Inventory / **UC6** — màn **Kiểm kê kho** (`AuditPage`, `AuditSessionsTable`)  
> **Tags**: RESTful, AuditSessions, Pagination

---

## 1. Mục tiêu Task

- Thay mock `mockAuditSessions` + lọc client bằng **một API phân trang** khớp cột bảng: mã đợt, tên, ngày kiểm, người tạo, **tiến độ**, **số dòng lệch**, trạng thái.
- **Out of scope**: chi tiết + dòng kiểm → Task023; tạo đợt → Task022.

---

## 2. Mục đích Endpoint

**`GET /api/v1/inventory/audit-sessions`** trả `items[]` **không** nhúng full `items` kiểm (payload lớn) — chỉ **số liệu tổng hợp** (`totalLines`, `countedLines`, `varianceLines`) như `lineCount` ở phiếu nhập Task013.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.15**.  
DB: bảng đề xuất trong [`API_Task022_inventory_audit_sessions_post.md`](API_Task022_inventory_audit_sessions_post.md) §Phụ lục DDL.

**UI**: `mini-erp/src/features/inventory/pages/AuditPage.tsx`, `AuditSessionsTable.tsx`.

---

## 4. Thông tin chung (Overview)

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.15** |
| **Endpoint** | `/api/v1/inventory/audit-sessions` |
| **Method** | `GET` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner, Staff, Admin (UC6) |
| **Use Case Ref** | UC6 |

---

## 5. Đặc tả Request (Request Specification)

### 5.1 Headers

```http
Authorization: Bearer <your_access_token>
```

### 5.2 Query parameters

| Tham số | Kiểu | Bắt buộc | Mặc định | Mô tả |
| :------ | :--- | :------- | :------- | :---- |
| `search` | string | Không | — | `audit_code`, `title`, `created_by` name (ILIKE) |
| `status` | string | Không | `all` | `all`, `Pending`, `In Progress`, `Completed`, `Cancelled` |
| `dateFrom` | string (YYYY-MM-DD) | Không | — | `audit_date >=` |
| `dateTo` | string (YYYY-MM-DD) | Không | — | `audit_date <=` |
| `page` | number | Không | `1` | |
| `limit` | number | Không | `20` | max 100 |

### 5.3 Request body

_Không có_

---

## 6. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "auditCode": "KK-2026-0001",
        "title": "Kiểm kê cuối tháng 3",
        "auditDate": "2026-03-31",
        "status": "Completed",
        "locationFilter": "WH01",
        "categoryFilter": null,
        "createdBy": 2,
        "createdByName": "Nguyễn Văn A",
        "completedAt": "2026-04-01T16:00:00Z",
        "completedByName": "Trần Quản Lý",
        "createdAt": "2026-03-31T08:00:00Z",
        "updatedAt": "2026-04-01T16:00:00Z",
        "totalLines": 6,
        "countedLines": 6,
        "varianceLines": 3
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 3
  },
  "message": "Thành công"
}
```

`varianceLines`: số dòng đã đếm có `(actual_quantity - system_quantity) <> 0` (NULL `actual_quantity` → chưa lệch / chưa đếm tùy policy — **chốt**: chỉ tính khi `is_counted = true` và `actual_quantity` NOT NULL).

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → **401** / **403**.
2. Validate query → **400**.
3. **`COUNT(*)`** sessions với filter.
4. **`SELECT`** trang từ `inventory_audit_sessions` join `users` (created_by, completed_by) + subquery aggregate từ `inventory_audit_lines`:
   - `total_lines = COUNT(*)`
   - `counted_lines = COUNT(*) FILTER (WHERE is_counted)`
   - `variance_lines = COUNT(*) FILTER (WHERE is_counted AND actual_quantity IS NOT NULL AND (actual_quantity - system_quantity) <> 0)`
5. Map camelCase.

### 7.2 Các ràng buộc (Constraints)

- Read-only; không `SELECT *`.

---

## 8. Lỗi (Error Responses)

_(400 / 401 / 403 / 500 — ví dụ JSON đầy đủ như [`API_Task013_stock_receipts_get_list.md`](API_Task013_stock_receipts_get_list.md) §9.)_

---

## 9. Zod (query — FE)

```typescript
import { z } from "zod";

export const AuditSessionListQuerySchema = z.object({
  search: z.string().optional(),
  status: z.enum(["all", "Pending", "In Progress", "Completed", "Cancelled"]).optional(),
  dateFrom: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  dateTo: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
});
```
