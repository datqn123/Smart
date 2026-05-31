# 📄 API SPEC: `POST /api/v1/alert-settings` — Tạo rule cảnh báo — Task083

> **Trạng thái**: Draft  
> **Feature**: UC5

---

## 1. Endpoint

**`POST /api/v1/alert-settings`**

---

## 2. Body

| Trường | Bắt buộc |
| :----- | :------- |
| `alertType` | Có |
| `channel` | Có |
| `frequency` | Không (default `Realtime`) |
| `thresholdValue` | Tuỳ loại |
| `isEnabled` | Không (default `true`) |
| `recipients` | Không |

`owner_id` = user Owner hiện tại (server-side).

---

## 3. Ràng buộc

- **UNIQUE** gợi ý: `(owner_id, alert_type)` — mỗi loại một rule; trùng → **409**.

---

## 4. `201 Created`

Trả về bản ghi đầy đủ (shape Task082 item).

---

## 5. Zod

```typescript
import { z } from "zod";

export const AlertSettingCreateBodySchema = z.object({
  alertType: z.enum([
    "LowStock",
    "ExpiryDate",
    "HighValueTransaction",
    "PendingApproval",
    "OverStock",
    "SalesOrderCreated",
    "PartnerDebtDueSoon",
    "SystemHealth",
  ]),
  channel: z.enum(["App", "Email", "SMS", "Zalo"]),
  frequency: z.enum(["Realtime", "Daily", "Weekly"]).optional().default("Realtime"),
  thresholdValue: z.number().optional().nullable(),
  isEnabled: z.boolean().optional().default(true),
  recipients: z.array(z.string()).optional(),
});
```
