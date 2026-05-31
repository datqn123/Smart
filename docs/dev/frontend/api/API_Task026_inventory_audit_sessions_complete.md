# 📄 API SPEC: `POST /api/v1/inventory/audit-sessions/{id}/complete` — Hoàn tất đợt kiểm kê - Task026

> **Trạng thái**: Draft  
> **Feature**: UC6 — đóng đợt (`Completed`), ghi `completed_at` / `completed_by`

---

## 1. Mục tiêu Task

- Chuyển **`In Progress` → `Completed`** (hoặc `Pending` → `Completed` nếu cho phép bỏ qua bước In Progress — mặc định: **chỉ từ `In Progress`**).

- **Out of scope**: áp chênh lệch tồn → Task028.

---

## 2. Mục đích Endpoint

Không đụng `Inventory.quantity` tại bước này.

---

## 3. Tham chiếu

[`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.15**; [`API_Task023_inventory_audit_sessions_get_by_id.md`](API_Task023_inventory_audit_sessions_get_by_id.md); [`API_Task025_inventory_audit_sessions_patch_lines.md`](API_Task025_inventory_audit_sessions_patch_lines.md).

---

## 4. Thông tin chung (Overview)

| **API Design Ref** | §4.15 |
| **Endpoint** | `/api/v1/inventory/audit-sessions/{id}/complete` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner / Staff (UC6) |
| **Use Case Ref** | UC6 |

---

## 5. Request body (optional)

```json
{
  "requireAllCounted": true
}
```

- `requireAllCounted: true` (mặc định): mọi dòng phải `is_counted = true` — else **409**.

---

## 6. Thành công — `200 OK`

`data` như Task023 với `status: "Completed"`.

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **`SELECT … FOR UPDATE`** session — **404**; status sai → **409**.
2. Nếu `requireAllCounted`: **`SELECT COUNT(*) FROM inventory_audit_lines WHERE session_id=? AND is_counted=false`** > 0 → **409**.
3. **`UPDATE inventory_audit_sessions SET status='Completed', completed_at=NOW(), completed_by=?, updated_at=NOW()`**.
4. **`INSERT SystemLogs`**.
5. **`COMMIT`**.

### 7.2 Các ràng buộc (Constraints)

- Không double-complete — lần 2 → **409**.

---

## 8. Lỗi — 401, 403, 404, 409, 500.

---

## 9. Zod

```typescript
import { z } from "zod";
export const AuditSessionCompleteBodySchema = z.object({
  requireAllCounted: z.boolean().optional().default(true),
});
```
