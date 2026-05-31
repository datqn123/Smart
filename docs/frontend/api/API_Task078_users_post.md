# 📄 API SPEC: `POST /api/v1/users` — Tạo nhân viên — Task078

> **Trạng thái**: Draft  
> **Feature**: UC3 — `EmployeeForm` (tạo mới)

---

## 1. Endpoint

**`POST /api/v1/users`**

---

## 2. RBAC

**Owner** / Admin có `can_manage_staff`. Không cho phép tạo thêm **Owner** nếu policy giới hạn 1 Owner/tenant.

---

## 3. Request body

| Trường | Bắt buộc | Mô tả |
| :----- | :------- | :---- |
| `username` | Có | Đăng nhập (có thể trùng quy tắc với `employeeCode`) |
| `password` | Có | Chỉ plaintext trên wire HTTPS; server hash |
| `fullName` | Có | |
| `email` | Có | UNIQUE |
| `phone` | Không | |
| `staffCode` | Không | Map `staff_code`; sinh từ `employeeCode` FE |
| `roleId` | Có | FK `Roles` |
| `status` | Không | `Active` \| `Inactive` → lưu `Active` \| `Locked` |

---

## 4. Logic DB

`INSERT INTO users (username, password_hash, full_name, email, phone, staff_code, role_id, status) VALUES (…)`  
Không trả `passwordHash` trong response.

---

## 5. `201 Created`

Trả về bản ghi dạng Task077 một phần tử.

---

## 6. Lỗi

**400**, **409** (trùng email/username), **401**, **403**, **500**.

---

## 7. Zod

```typescript
import { z } from "zod";

export const UserCreateBodySchema = z.object({
  username: z.string().trim().min(3).max(100),
  password: z.string().min(8).max(128),
  fullName: z.string().trim().min(1).max(255),
  email: z.string().trim().email(),
  phone: z.string().trim().max(20).optional().or(z.literal("")),
  staffCode: z.string().trim().max(50).optional().or(z.literal("")),
  roleId: z.number().int().positive(),
  status: z.enum(["Active", "Inactive"]).optional().default("Active"),
});
```
