# 📄 API SPEC: `POST /api/v1/inventory/audit-sessions/{id}/cancel` — Hủy đợt kiểm kê - Task027

> **Trạng thái**: Draft  
> **Feature**: UC6 — hủy đợt chưa hoàn tất

---

## 1. Mục tiêu Task

- **`Pending`**, **`In Progress`** hoặc **`Pending Owner Approval`** → `Cancelled` (SRS OQ-15).  
- **`Completed`** → **409** (trừ khi PM cho phép reverse — không mặc định).

---

## 2. Mục đích Endpoint

**`POST /api/v1/inventory/audit-sessions/{id}/cancel`** — body bắt buộc `{ "cancelReason": "…" }` (OQ-18 / SRS).

---

## 3. Thông tin chung (Overview)

| **API Design Ref** | §4.15 |
| **Endpoint** | `/api/v1/inventory/audit-sessions/{id}/cancel` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner / Staff |
| **Use Case Ref** | UC6 |

---

## 4. Request body (bắt buộc)

```json
{ "cancelReason": "Đổi kế hoạch kiểm kê" }
```

---

## 5. Thành công — `200 OK`

`data` với `status: "Cancelled"`.

---

## 6. Logic nghiệp vụ & Database (Business Logic)

1. Lock session; kiểm tra trạng thái → **409** nếu đã `Completed` hoặc đã `Cancelled`.
2. **`UPDATE … SET status='Cancelled', notes = COALESCE(notes,'') || reason, updated_at=NOW()`** (hoặc cột `cancel_reason` nếu migration).
3. **`INSERT SystemLogs`**; **`COMMIT`**.

---

## 7. Lỗi — 401, 403, 404, 409, 500.

---

## 8. Zod

```typescript
import { z } from "zod";
export const AuditSessionCancelBodySchema = z.object({
  reason: z.string().max(1000).optional(),
});
```
