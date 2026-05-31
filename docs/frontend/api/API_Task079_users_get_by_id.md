# 📄 API SPEC: `GET /api/v1/users/{userId}` — Chi tiết nhân viên — Task079

> **Trạng thái**: Draft  
> **Feature**: UC3 — `EmployeeDetailDialog`

---

## 1. Endpoint

**`GET /api/v1/users/{userId}`** — `userId` int > 0.

---

## 2. RBAC

Owner / Admin (khuyến nghị: claim `can_manage_staff`).  
Staff chỉ được xem **chính mình** nếu PO chốt policy self-access (nếu không: 403).

---

## 3. `200 OK`

Cùng shape một phần tử Task077; thêm tùy chọn: `lastLogin`, `username` (không nhạy cảm).

**Không** trả: `passwordHash`.

---

## 4. Lỗi

**404**, **401**, **403**, **500**.

---

## 5. Zod (params)

```typescript
import { z } from "zod";

export const UserIdParamsSchema = z.object({
  userId: z.coerce.number().int().positive(),
});
```
