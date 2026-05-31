# 📄 API SPEC: `PATCH /api/v1/inventory/audit-sessions/{id}/lines` — Ghi số kiểm thực tế - Task025

> **Trạng thái**: Draft  
> **Feature**: UC6 — nhập `actualQuantity` / `notes` cho từng dòng (mobile/scanner sau này)

---

## 1. Mục tiêu Task

- Cập nhật **một hoặc nhiều** `inventory_audit_lines` trong đợt **`Pending`** hoặc **`In Progress`** (chốt: **không** cho `Completed`/`Cancelled`).

---

## 2. Mục đích Endpoint

**`PATCH …/lines`** — body mảng `{ lineId, actualQuantity, notes }`; set `is_counted = true` khi `actual_quantity` NOT NULL.

---

## 3. Thông tin chung (Overview)

| **Endpoint** | `/api/v1/inventory/audit-sessions/{id}/lines` |
| **Method** | `PATCH` |
| **Auth** | `Bearer` |
| **API Design Ref** | §4.15 |

---

## 5. Request body

```json
{
  "lines": [
    { "lineId": 7, "actualQuantity": 12, "notes": "Đếm lại kệ A2" },
    { "lineId": 8, "actualQuantity": 0, "notes": null }
  ]
}
```

| Field | Bắt buộc |
| :---- | :------- |
| `lines` | Có, min 1 |
| `lines[].lineId` | Có (`inventory_audit_lines.id`) |
| `lines[].actualQuantity` | Có (≥ 0) |
| `lines[].notes` | Không |

---

## 6. Thành công — `200 OK`

`data` như Task023 (session + items sau cập nhật).

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. Lock session: **`SELECT status FROM inventory_audit_sessions WHERE id=? FOR UPDATE`** — phải `Pending` hoặc `In Progress` — else **409**.
2. Với mỗi `lineId`: **`SELECT id FROM inventory_audit_lines WHERE id=? AND session_id=?`** — không khớp → **400** (`details`).
3. **`UPDATE inventory_audit_lines SET actual_quantity=?, notes=?, is_counted=true, updated_at=NOW()`**.
4. **`INSERT SystemLogs`** (tùy policy — có thể gộp 1 log bulk).
5. **`COMMIT`**.

### 7.2 Các ràng buộc (Constraints)

- `actual_quantity >= 0` (CHECK ở app hoặc DB).

---

## 8. Lỗi — 400, 401, 403, 404, 409, 500.

---

## 9. Zod

```typescript
import { z } from "zod";
const LineUpdateSchema = z.object({
  lineId: z.number().int().positive(),
  actualQuantity: z.number().nonnegative(),
  notes: z.string().max(500).nullable().optional(),
});
export const AuditLinesPatchSchema = z.object({
  lines: z.array(LineUpdateSchema).min(1),
});
```
