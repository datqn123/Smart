# 📄 API SPEC: `GET /api/v1/system-logs` — Nhật ký hệ thống — Task086

> **Trạng thái**: Draft  
> **Feature**: màn **Nhật ký hệ thống** (`LogsPage`, `LogTable`)

---

## 1. Endpoint

**`GET /api/v1/system-logs`**

---

## 2. RBAC

Chỉ **Admin** được xem nhật ký hệ thống: JWT claim **`role`** phải là **`Admin`** **và** claim **`mp.can_view_system_logs`** phải là **`true`** (seed `roles.permissions`; Flyway **V43** thu hồi quyền **Owner**). **Staff** và **Owner** nhận **403**.

> **Đồng bộ:** [`docs/backend/srs/SRS_PRD_system-audit-unified-admin-view.md`](../../../docs/backend/srs/SRS_PRD_system-audit-unified-admin-view.md) (Approved 02/05/2026); amend [`SRS_Task086_system-logs.md`](../../../docs/backend/srs/SRS_Task086_system-logs.md).

---

## 3. Query

| Tham số | Mô tả |
| :------ | :---- |
| `search` | `ILIKE` trên `message`, `action`, join `users.full_name` |
| `module` | = `module` |
| `logLevel` | `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` |
| `dateFrom`, `dateTo` | Lọc `created_at` |
| `page`, `limit` | Phân trang (mặc định sort `created_at DESC`) |

---

## 4. Response — map FE `SystemLog`

| FE | API / DB |
| :--- | :------- |
| `timestamp` | `createdAt` (ISO string) |
| `user` | `fullName` từ join `users` hoặc `"System"` nếu `user_id` null |
| `action` | `action` |
| `module` | `module` |
| `description` | `message` |
| `severity` | `INFO`→`Info`, `WARNING`→`Warning`, … (Pascal cho FE) |
| `ipAddress` | `context_data->>'clientIp'` (DB không có cột `ip_address`) |

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 101,
        "timestamp": "2026-04-23T10:30:15.000Z",
        "user": "Nguyễn Văn A",
        "action": "Create",
        "module": "Products",
        "description": "Tạo mới sản phẩm SKU…",
        "severity": "Info",
        "ipAddress": "192.168.1.1"
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 5000
  },
  "message": "Thành công"
}
```

---

## 5. DDL

Cột `ip_address` — [`Database_Specification.md`](../UC/Database_Specification.md) §11.

---

## 6. Zod (query)

```typescript
import { z } from "zod";

export const SystemLogsListQuerySchema = z.object({
  search: z.string().optional(),
  module: z.string().optional(),
  logLevel: z.enum(["INFO", "WARNING", "ERROR", "CRITICAL"]).optional(),
  dateFrom: z.string().date().optional(),
  dateTo: z.string().date().optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
});
```
