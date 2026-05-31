# 📄 API SPEC: `POST /api/v1/inventory/audit-sessions/{id}/apply-variance` — Áp chênh lệch lên tồn kho - Task028

> **Trạng thái**: Draft  
> **Feature**: UC6 — sau kiểm kê, điều chỉnh `Inventory` theo lệch (nghiệp vụ tương đương [`API_Task010_inventory_post_adjustments.md`](API_Task010_inventory_post_adjustments.md) + [`API_Task011_inventory_mutation_audit_logs.md`](API_Task011_inventory_mutation_audit_logs.md))

---

## 1. Mục tiêu Task

- Với session **`Completed`**, mỗi dòng có **`variance != 0`** (`actual_quantity - system_quantity`): **`UPDATE Inventory.quantity`** bằng `actual_quantity` **hoặc** cộng `delta` (= variance) — **chốt triển khai một hướng** (khuyến nghị: **set `quantity = actual_quantity`** vì snapshot `system_quantity` đã cố định tại tạo đợt; nếu tồn đã thay đổi sau đó, dùng **delta** có cảnh báo — ghi rõ trong code review).

- Ghi **`InventoryLogs`** (`ADJUSTMENT` hoặc `INBOUND`/`OUTBOUND` tùy dấu — khuyến nghị **`ADJUSTMENT`** + `reference_note` chứa `auditSessionId` + `lineId`).

- **Out of scope**: hoàn tất session — Task026 (endpoint này giả định đã Completed).

---

## 2. Mục đích Endpoint

Một transaction lớn: với mỗi dòng lệch, cập nhật `Inventory` + insert log + `SystemLogs` + (tuỳ Task012) notify Owner.

---

## 3. Thông tin chung (Overview)

| **API Design Ref** | §4.15 |
| **Endpoint** | `/api/v1/inventory/audit-sessions/{id}/apply-variance` |
| **Method** | `POST` |
| **Authentication** | `Bearer` |
| **RBAC** | Owner / Staff (theo quyền điều chỉnh tồn) |
| **Use Case Ref** | UC6 |

---

## 4. Request body

```json
{
  "reason": "Điều chỉnh theo kiểm kê KK-2026-0001",
  "mode": "delta"
}
```

| `mode` | Ý nghĩa |
| :----- | :------ |
| `delta` | `quantity += (actual_quantity - system_quantity)` trên dòng `inventory_id` hiện tại |
| `set_actual` | `quantity = actual_quantity` (ghi rõ rủi ro lệch với tồn thực tế hiện tại) |

`reason` bắt buộc (audit).

---

## 5. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "sessionId": 1,
    "appliedLines": [
      { "lineId": 1, "inventoryId": 101, "deltaQty": -2, "quantityAfter": 148 }
    ]
  },
  "message": "Đã áp chênh lệch kiểm kê lên tồn kho"
}
```

---

## 6. Logic nghiệp vụ & Database (Business Logic)

### 6.1 Quy trình thực thi (Step-by-Step)

1. **`SELECT status FROM inventory_audit_sessions WHERE id=? FOR UPDATE`** — phải `Completed` — else **409**.
2. **`BEGIN`** (hoặc đã FOR UPDATE).
3. Lấy các dòng **`is_counted` và `actual_quantity` NOT NULL** và `(actual_quantity - system_quantity) <> 0`.
4. Với mỗi dòng: **`SELECT quantity FROM inventory WHERE id=? FOR UPDATE`**; áp dụng `mode`; kiểm tra `quantity >= 0` sau cập nhật → nếu vi phạm **ROLLBACK** → **409** hoặc **400**.
5. **`UPDATE inventory SET quantity=…, updated_at=NOW()`**.
6. **`INSERT INTO inventory_logs`** (theo §22, `receipt_id` NULL, `reference_note` JSON ≤255 hoặc truncate).
7. **`INSERT system_logs`**; Task012 nếu Staff.
8. **`COMMIT`**.
9. **Idempotency**: cột `variance_applied_at` trên line hoặc bảng phụ — nếu đã apply → **409** “Đã áp chênh lệch” (tránh double).

### 6.2 Các ràng buộc (Constraints)

- `chk_quantity` trên `Inventory`; tuân Task011.

---

## 7. Lỗi — 400, 401, 403, 404, 409, 500.

---

## 8. Zod

```typescript
import { z } from "zod";
export const AuditApplyVarianceBodySchema = z.object({
  reason: z.string().min(1).max(500),
  mode: z.enum(["delta", "set_actual"]).default("delta"),
});
```
