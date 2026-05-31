# 📄 API SPEC: `POST /api/v1/stock-receipts/{id}/approve` — Phê duyệt phiếu nhập - Task019

> **Trạng thái**: Draft  
> **Feature**: **UC4** + **UC7** — `ReceiptDetailDialog` / `ReceiptDetailPanel` (`canApprove`, `status === 'Pending'`)

---

## 1. Mục tiêu Task

- Chuyển **`Pending` → `Approved`**, ghi **`approved_by`**, **`approved_at`**, đồng thời **`reviewed_by`**, **`reviewed_at`**, xóa **`rejection_reason`** (NULL), rồi **cộng `Inventory`**, ghi **`InventoryLogs`**, **`FinanceLedger`**, **`SystemLogs`** trong **một transaction** (theo DB §17, cột `reviewed_*` — [`Database_Specification.md`](../UC/Database_Specification.md) §17).

- **Out of scope**: từ chối → Task020.

---

## 2. Mục đích Endpoint

Sau khi duyệt, hệ thống **mới** được cộng tồn và ghi sổ tài chính — khớp `Database_Specification.md` §17 mục Business Rules.

---

## 3. Overview

| **API Design Ref** | [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.5** |
| **Endpoint** | `/api/v1/stock-receipts/{id}/approve` |
| **Method** | `POST` |
| **Auth** | `Bearer` |
| **RBAC** | JWT `hasAuthority('can_approve')` **và** claim `role` = **`Owner`** (không phân biệt hoa thường). User khác Owner → **403** dù có `can_approve`. SRS: `backend/docs/srs/SRS_Task014-020_stock-receipts-lifecycle.md` §6. |

---

## 4. Request body

**Vị trí nhập kho** không có trên `StockReceiptDetails` — body **bắt buộc** chỉ định vị trí đích chung cho mọi dòng (v1):

```json
{
  "inboundLocationId": 3
}
```

| Field | Kiểu | Bắt buộc | Mô tả |
| :---- | :--- | :------- | :---- |
| `inboundLocationId` | number | Có | `WarehouseLocations.id`, `status = 'Active'` |

_(V2: thêm `locationId` từng dòng trong receipt detail — cần migration DB + đổi UI.)_

---

## 5. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 42,
    "receiptCode": "PN-2026-0042",
    "status": "Approved",
    "approvedBy": 2,
    "approvedByName": "Owner Nguyễn",
    "approvedAt": "2026-04-23T11:00:00Z",
    "reviewedBy": 2,
    "reviewedByName": "Owner Nguyễn",
    "reviewedAt": "2026-04-23T11:00:00Z",
    "rejectionReason": null,
    "updatedAt": "2026-04-23T11:00:00Z",
    "details": []
  },
  "message": "Đã phê duyệt phiếu nhập kho"
}
```

(`details` có thể trả đầy đủ như Task015 hoặc rút gọn — chốt triển khai.)

---

## 7. Logic nghiệp vụ & Database (Business Logic)

### 7.1 Quy trình thực thi (Step-by-Step)

1. **JWT** → `approver_user_id`. Kiểm tra quyền UC4 → **403**.
2. **`SELECT sr.* FROM StockReceipts sr WHERE sr.id = ? FOR UPDATE`** — không có → **404**; `status <> 'Pending'` → **409**.
3. **`SELECT id, status FROM WarehouseLocations WHERE id = ?`** — không Active → **400** hoặc **409**.
4. **`SELECT` toàn bộ `StockReceiptDetails`** join `ProductUnits` để lấy `conversion_rate` nếu cần quy đổi về **đơn vị cơ sở** (`Inventory.quantity` luôn base unit — §16).
5. **`BEGIN`** (nếu chưa FOR UPDATE).
6. **Với mỗi detail** (số lượng base = `quantity * conversion_rate_to_base` nếu có; nếu v1 chỉ cho `unit_id` là base unit thì `quantity` giữ nguyên):
   - **`SELECT id, quantity FROM Inventory WHERE product_id = ? AND location_id = ? AND COALESCE(batch_number,'') = COALESCE(?, '') FOR UPDATE`**.
   - Nếu có: **`UPDATE Inventory SET quantity = quantity + :base_qty, updated_at = NOW()`**.
   - Nếu không: **`INSERT INTO Inventory (product_id, location_id, batch_number, expiry_date, quantity, min_quantity)`** với `min_quantity` mặc định 0 hoặc từ policy.
7. **`INSERT INTO InventoryLogs`** mỗi dòng: `product_id`, `action_type = 'INBOUND'`, `quantity_change` = +số lượng **theo đơn vị cơ sở**, `unit_id` = đơn vị cơ sở, `user_id` = approver, `receipt_id` = phiếu, `from_location_id` = NULL, `to_location_id` = `:inboundLocationId`, `reference_note` tùy chọn (≤255).
8. **`INSERT INTO FinanceLedger`**: `transaction_type = 'PurchaseCost'`, `amount` **< 0** nếu theo quy ước §12 (chi phí nhập), `reference_type = 'StockReceipt'`, `reference_id` = `receipt.id`, `created_by` = approver, `transaction_date` = `receipt_date`, `description` tóm tắt mã phiếu.
9. **`UPDATE StockReceipts SET status='Approved', approved_by=?, approved_at=NOW(), reviewed_by=?, reviewed_at=NOW(), rejection_reason=NULL, updated_at=NOW() WHERE id=?`** — `reviewed_by` / `reviewed_at` đồng bộ với người/thời điểm duyệt (xem `Database_Specification.md` §17 `reviewed_*`).
10. **`INSERT SystemLogs`**.
11. **`COMMIT`**.

### 7.2 Các ràng buộc (Constraints)

- `chk_quantity` trên `Inventory`; `uq_inventory_product_location_batch`.  
- `FinanceLedger` immutable sau ghi — không rollback nhẹ; transaction phải **all-or-nothing**.  
- **Idempotency**: nếu approve gọi 2 lần — bước 2 phải **409** vì đã `Approved`.

---

## 8. Lỗi

- **400** — thiếu `inboundLocationId`, vị trí không Active.  
- **401**, **403** (thiếu `can_approve` hoặc JWT `role` ≠ Owner), **404**, **409** (đã duyệt / sai trạng thái), **500**.

Ví dụ **403** (có `can_approve` nhưng không phải Owner — cùng message với Task017/020 / SRS §8.3):

```json
{
  "success": false,
  "error": "FORBIDDEN",
  "message": "Chỉ tài khoản Owner mới được xóa phiếu (Nháp/Chờ duyệt), phê duyệt hoặc từ chối phiếu Chờ duyệt"
}
```

Ví dụ **409**:

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Phiếu không ở trạng thái Chờ duyệt hoặc đã được phê duyệt trước đó"
}
```

---

## 9. Zod

```typescript
import { z } from "zod";
export const StockReceiptApproveBodySchema = z.object({
  inboundLocationId: z.number().int().positive(),
});
```
