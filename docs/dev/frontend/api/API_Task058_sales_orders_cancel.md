# 📄 API SPEC: `POST /api/v1/sales-orders/{id}/cancel` — Hủy đơn - Task058

> **Trạng thái**: Draft  
> **Feature**: UC9 / UC4 — hủy đơn bán; đồng bộ [`API_PROJECT_DESIGN.md`](API_PROJECT_DESIGN.md) **§4.10**  
> **Tags**: RESTful, SalesOrders, Cancel

---

## 1. Mục tiêu Task

- Chuyển đơn sang **`Cancelled`**, ghi **`cancelled_at`**, **`cancelled_by`** (user hiện tại); không xóa bản ghi.

---

## 2. Endpoint

**`POST /api/v1/sales-orders/{id}/cancel`**

---

## 3. Request body (optional)

```json
{
  "reason": "Khách đổi ý"
}
```

---

## 4. Thành công — `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 2,
    "status": "Cancelled",
    "cancelledAt": "2026-04-23T14:00:00Z",
    "cancelledBy": 5
  },
  "message": "Đã hủy đơn hàng"
}
```

---

## 5. Logic DB (transaction)

1. Lock header → **404**.
2. Nếu đã `Cancelled` → **200** idempotent (trả cùng trạng thái).
3. Nếu đã xuất kho (`StockDispatches` / `dispatched_qty` > 0):  
   - Với **Retail POS** (Task090): thực hiện **hoàn kho** (reverse `InventoryLogs`, cộng lại `Inventory.quantity`, huỷ `StockDispatches`, reset `OrderDetails.dispatched_qty`) rồi mới hủy đơn.  
   - Với kênh khác: **409** "Không thể hủy — đã có phiếu xuất".
4. **`UPDATE sales_orders SET status = 'Cancelled', cancelled_at = NOW(), cancelled_by = $uid, updated_at = NOW()`**.
5. (Tuỳ chọn) ghi `SystemLogs`; **hoàn tồn** nếu đã reserve — Task bổ sung / cùng UC10.

---

## 6. Lỗi

**404** / **409** / **401** / **403** / **500**.

---

## 7. Zod (body)

```typescript
import { z } from "zod";
export const SalesOrderCancelBodySchema = z.object({
  reason: z.string().max(500).optional(),
});
```
