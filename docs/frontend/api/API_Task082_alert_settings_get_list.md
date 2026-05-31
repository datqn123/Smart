# 📄 API SPEC: `GET /api/v1/alert-settings` — Danh sách cấu hình cảnh báo — Task082

> **Trạng thái**: Draft  
> **Feature**: UC5 — màn **Cấu hình cảnh báo** (`AlertSettingsPage` — đồng bộ từng rule / switch)

---

## 1. Endpoint

**`GET /api/v1/alert-settings`**

---

## 2. RBAC

**Owner** (theo `owner_id` trong bảng). **Admin** được đọc **toàn cục** (danh sách của mọi Owner).

---

## 3. Query (optional)

| Tham số | Mô tả |
| :------ | :---- |
| `ownerId` | **Chỉ Admin**: lọc theo `owner_id` cụ thể; nếu bỏ qua thì Admin thấy toàn cục |
| `alertType` | Lọc một `alert_type` |
| `isEnabled` | `true` / `false` |

---

## 4. Response

Mỗi phần tử khớp [`Database_Specification.md`](../UC/Database_Specification.md) §10 — **camelCase**:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 10,
        "alertType": "LowStock",
        "thresholdValue": 10,
        "channel": "App",
        "frequency": "Realtime",
        "isEnabled": true,
        "recipients": ["user_2"],
        "updatedAt": "2026-04-20T12:00:00Z"
      }
    ]
  },
  "message": "Thành công"
}
```

**Mapping UI hiện tại** (switch) ↔ `alert_type` (sau migration DB):

| Switch FE | `alert_type` đề xuất |
| :---------- | :------------------- |
| lowStock | `LowStock` |
| overStock | `OverStock` |
| newOrder | `SalesOrderCreated` |
| largeTransaction | `HighValueTransaction` + `threshold_value` (VD 50_000_000) |
| debtDue | `PartnerDebtDueSoon` + `threshold_value` = số ngày (3) |
| systemError | `SystemHealth` |

---

## 5. Migration gợi ý

Flyway V1 hiện đã có bảng `AlertSettings` nhưng `CHECK (alert_type IN (...))` còn thiếu các loại mới. Cần migration V2+ để **drop/add lại CHECK** theo danh sách tại **Database_Specification §10** (thêm `OverStock`, `SalesOrderCreated`, `SystemHealth`).

---

## 6. Zod

```typescript
import { z } from "zod";

const AlertTypeSchema = z.enum([
  "LowStock",
  "ExpiryDate",
  "HighValueTransaction",
  "PendingApproval",
  "OverStock",
  "SalesOrderCreated",
  "PartnerDebtDueSoon",
  "SystemHealth",
]);

export const AlertSettingItemSchema = z.object({
  id: z.number().int().positive(),
  alertType: AlertTypeSchema,
  thresholdValue: z.number().nullable(),
  channel: z.enum(["App", "Email", "SMS", "Zalo"]),
  frequency: z.enum(["Realtime", "Daily", "Weekly"]),
  isEnabled: z.boolean(),
  recipients: z.array(z.string()).nullable().optional(),
  updatedAt: z.string(),
});
```
