# 📄 API SPEC: `PATCH /api/v1/users/{userId}` — Cập nhật nhân viên — Task080

> **Trạng thái**: Draft  
> **Feature**: UC3 — `EmployeeForm` (sửa)

---

## 1. Endpoint

**`PATCH /api/v1/users/{userId}`**

---

## 2. Request body (partial)

| Trường | Mô tả |
| :----- | :---- |
| `fullName`, `email`, `phone`, `staffCode` | |
| `roleId` | |
| `status` | `Active` \| `Inactive` → DB `Active` \| `Locked` |
| `password` | Optional — chỉ khi đổi mật khẩu (Owner reset khác Task004) |

---

## 3. Ràng buộc

- Không tự **khóa** Owner cuối cùng.  
- Đổi `roleId` sang Owner → policy rủi ro (ghi rõ BA).

**Gợi ý đồng bộ với codebase hiện tại (Task078)**:

- Không cho phép gán `roleId` trỏ tới role `Owner` cho tài khoản nhân viên (trừ khi PO có yêu cầu “chuyển quyền Owner” riêng).

---

## 4. `200 OK`

Object user như Task079.

---

## 5. Lỗi

**400**, **404**, **409** (email trùng), **401**, **403**, **500**.

---

## 6. Zod

```typescript
import { z } from "zod";

export const UserPatchBodySchema = z
  .object({
    fullName: z.string().min(1).max(255).optional(),
    email: z.string().email().optional(),
    phone: z.string().max(20).optional().nullable(),
    staffCode: z.string().max(50).optional().nullable(),
    roleId: z.number().int().positive().optional(),
    status: z.enum(["Active", "Inactive"]).optional(),
    password: z.string().min(8).max(128).optional(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" });
```
