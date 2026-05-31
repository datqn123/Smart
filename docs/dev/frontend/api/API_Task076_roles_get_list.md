# 📄 API SPEC: `GET /api/v1/roles` — Danh sách vai trò — Task076

> **Trạng thái**: Draft  
> **Feature**: UC3 — dropdown phân quyền (`EmployeeForm`, filter nội bộ)

---

## 1. Endpoint

**`GET /api/v1/roles`**

---

## 2. RBAC

**Bearer JWT**. Khuyến nghị đồng bộ với các endpoint quản lý nhân viên (Task078/078_02): yêu cầu claim quyền **`can_manage_staff`** → `hasAuthority('can_manage_staff')`.  
Nếu policy chỉ cho Owner/Admin thì cần PO chốt rõ tiêu chí (theo role name hay theo permissions JSON) để tránh lệch với codebase.

---

## 3. `200 OK`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Owner",
        "permissions": {
          "can_view_dashboard": true,
          "can_use_ai": true,
          "can_manage_inventory": true,
          "can_manage_products": true,
          "can_manage_customers": true,
          "can_manage_orders": true,
          "can_approve": true,
          "can_view_finance": true,
          "can_manage_staff": true,
          "can_configure_alerts": true
        }
      }
    ]
  },
  "message": "Thành công"
}
```

**Lưu ý**:

- Backend lưu `roles.permissions` kiểu **JSONB**; API nên trả `permissions` dạng **object** để FE dùng trực tiếp.
- FE hiện có 4 nhãn `Admin/Manager/Warehouse/Staff` trong UI nhưng seed DB baseline chỉ có `Owner/Staff/Admin` → cần PO chốt hướng đồng bộ (thêm role DB hay FE map tạm).

Tham chiếu: [`Database_Specification.md`](../UC/Database_Specification.md) §1 `Roles`.

---

## 4. Zod

```typescript
import { z } from "zod";

export const RoleItemSchema = z.object({
  id: z.number().int().positive(),
  name: z.string(),
  permissions: z.record(z.string(), z.unknown()),
});
```
