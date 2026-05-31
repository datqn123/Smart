# 📄 API SPEC: `GET /api/v1/users` — Danh sách nhân viên — Task077

> **Trạng thái**: Draft  
> **Feature**: UC3 — màn **Quản lý nhân viên** (`EmployeesPage`, `EmployeeTable`)

---

## 1. Endpoint

**`GET /api/v1/users`**

---

## 2. Query

| Tham số | Mô tả |
| :------ | :---- |
| `search` | `ILIKE` trên `staff_code`, `full_name`, `email` |
| `status` | `all` \| `Active` \| `Inactive` (Inactive ↔ DB `Locked`) |
| `roleId` | Lọc `role_id` |
| `page`, `limit` | Phân trang |

---

## 3. Response item (camelCase — đồng bộ `Employee`)

| JSON | Nguồn DB |
| :--- | :------- |
| `employeeCode` | `users.staff_code` (fallback `username` nếu null) |
| `fullName` | `full_name` |
| `joinedDate` | `created_at::date` hoặc ISO date |
| `role` | **Read-model** từ `roles.name` (string hiển thị) |
| `roleId` | `role_id` |
| `status` | `Active` nếu DB `Active`, else `Inactive` nếu DB `Locked` |

---

## 4. `200 OK` (rút gọn)

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 3,
        "employeeCode": "NV001",
        "fullName": "Nguyễn Văn A",
        "email": "vana@minierp.com",
        "phone": "0987654321",
        "roleId": 2,
        "role": "Staff",
        "status": "Active",
        "joinedDate": "2023-01-01",
        "avatar": null
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 4
  },
  "message": "Thành công"
}
```

---

## 5. DDL gợi ý

Cột `staff_code` trên `Users` — [`Database_Specification.md`](../UC/Database_Specification.md) §6.

---

## 6. Zod (query)

```typescript
import { z } from "zod";

export const UsersListQuerySchema = z.object({
  search: z.string().optional(),
  status: z.enum(["all", "Active", "Inactive"]).optional(),
  roleId: z.coerce.number().int().positive().optional(),
  page: z.coerce.number().int().min(1).optional().default(1),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
});
```
