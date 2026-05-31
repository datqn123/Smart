# 📄 API SPEC: `PATCH /api/v1/inventory/audit-sessions/{id}` — Cập nhật đợt kiểm kê - Task024

> **Trạng thái**: Draft  
> **Feature**: UC6 — chỉnh `title`, `notes`, **chuyển trạng thái** (ví dụ `Pending` → `In Progress`)

---

## 1. Mục tiêu Task

- Partial update meta + **state machine** hợp lệ.  
- **Out of scope**: ghi số thực tế từng dòng → Task025; hoàn tất / hủy → Task026,027.

---

## 2. Mục đích Endpoint

**`PATCH /api/v1/inventory/audit-sessions/{id}`** — không sửa `audit_code` / `audit_date` sau tạo (mặc định); nếu PM cho phép, mô tả thêm.

**Chuyển trạng thái cho phép:**

- `Pending` → `In Progress`  
- `In Progress` → `Pending` (rollback — tùy PM, mặc định **409**)  
- `Pending` \| `In Progress` → `Cancelled` (khuyến nghị dùng Task027 — hoặc cho phép PATCH)

Mặc định spec: **chỉ** `Pending` → `In Progress` qua PATCH; **`Cancelled` dùng Task027**.

---

## 3. Thông tin chung (Overview)

| **API Design Ref** | §4.15 |
| **Endpoint** | `/api/v1/inventory/audit-sessions/{id}` |
| **Method** | `PATCH` |
| **Auth** | `Bearer` |

---

## 5. Request body (partial)

```json
{
  "title": "Kiểm kê kho A1 - Tháng 4 (đổi tên)",
  "notes": "Bổ sung ghi chú",
  "status": "In Progress"
}
```

---

## 6. Thành công — `200 OK`

`data` như Task023.

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **`SELECT id, status FROM inventory_audit_sessions WHERE id = ? FOR UPDATE`** — **404** / **409** nếu `Completed` / `Cancelled`.
2. Validate transition → **409** nếu không hợp lệ.
3. **`UPDATE inventory_audit_sessions SET …, updated_at = NOW()`**.
4. **`INSERT SystemLogs`**.
5. **`COMMIT`**.

### 7.2 Các ràng buộc (Constraints)

- CHECK `status`.

---

## 8. Lỗi — 400, 401, 403, 404, 409, 500 (JSON tiếng Việt — tham chiếu Task013).

---

## 9. Zod

```typescript
import { z } from "zod";
export const AuditSessionPatchSchema = z.object({
  title: z.string().min(1).max(255).optional(),
  notes: z.string().max(2000).optional(),
  status: z.enum(["In Progress"]).optional(),
});
```
