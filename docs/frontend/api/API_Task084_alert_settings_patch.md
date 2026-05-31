# 📄 API SPEC: `PATCH /api/v1/alert-settings/{id}` — Cập nhật rule — Task084

> **Trạng thái**: Draft  
> **Feature**: UC5 — bật/tắt switch, đổi ngưỡng / kênh

---

## 1. Endpoint

**`PATCH /api/v1/alert-settings/{id}`**

---

## 2. Body (partial)

`thresholdValue`, `channel`, `frequency`, `isEnabled`, `recipients`.

---

## 3. RBAC

Chỉ Owner (hoặc Admin) sửa được bản ghi có `owner_id` thuộc quyền.

---

## 4. Lỗi

**404** (id không thuộc owner), **400**, **401**, **403**, **500**.

---

## 5. Zod

```typescript
import { z } from "zod";

export const AlertSettingPatchBodySchema = z
  .object({
    thresholdValue: z.number().nullable().optional(),
    channel: z.enum(["App", "Email", "SMS", "Zalo"]).optional(),
    frequency: z.enum(["Realtime", "Daily", "Weekly"]).optional(),
    isEnabled: z.boolean().optional(),
    recipients: z.array(z.string()).optional().nullable(),
  })
  .refine((o) => Object.keys(o).length > 0, { message: "Cần ít nhất một trường" });
```
