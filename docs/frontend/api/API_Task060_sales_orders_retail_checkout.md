# 📄 API SPEC: `POST /api/v1/sales-orders/retail/checkout` — Thanh toán POS (bán lẻ) - Task060

> **Trạng thái**: Draft (đã có SRS Task090 Approved — trừ tồn khi checkout)  
> **Feature**: UC9 — `RetailPage`, `POSCartPanel` (`handleCheckout`)  
> **Tags**: RESTful, SalesOrders, OrderDetails, POS, Create

---

## 1. Mục tiêu Task

- **Một request** tạo đơn **`order_channel = Retail`**, ghi dòng `OrderDetails`, áp dụng **giảm giá / voucher** (server-side validate), set **`payment_status`**; map **Khách lẻ** khi không có `customerId`.

---

## 2. Khách vãng lai (`customer_id` NOT NULL trên DB)

Seed bản ghi **`Customers`** cố định, ví dụ `customer_code = 'WALKIN'` / `name = 'Khách lẻ'`. Request gửi **`walkIn: true`** **hoặc** bỏ `customerId` → backend gán `customer_id` của bản ghi seed.

---

## 3. Endpoint

**`POST /api/v1/sales-orders/retail/checkout`**

---

## 4. Request body

```json
{
  "customerId": null,
  "walkIn": true,
  "lines": [
    {
      "productId": 12,
      "unitId": 101,
      "quantity": 2,
      "unitPrice": 6000
    }
  ],
  "discountAmount": 0,
  "voucherCode": "DISCOUNT10",
  "paymentStatus": "Paid",
  "notes": null,
  "shiftReference": "SHIFT-0418"
}
```

| Trường | Bắt buộc | Mô tả |
| :----- | :------- | :---- |
| `lines` | Có | Giống Task056 |
| `customerId` | Điều kiện | Bắt buộc nếu `walkIn !== true` |
| `walkIn` | Không | Mặc định `true` nếu không gửi `customerId` |
| `discountAmount` | Không | Tiền mặt định giảm (đồng); cộng với voucher |
| `voucherCode` | Không | Server validate; ví dụ `DISCOUNT10` → giảm **10%** trên tổng dòng (policy thống nhất với `POSCartPanel` mock). |
| `paymentStatus` | Không | Mặc định `Paid` cho POS tiền mặt |
| `notes` | Không | |
| `shiftReference` | Không | Chuỗi hiển thị phiên ca (UI); lưu vào `notes` prefix hoặc cột `pos_shift_id` nếu sau này có bảng ca bán |

**Trừ tồn kho (Task090 — triển khai backend):** API **không** nhận `locationId` trong body. Backend trừ tồn theo **kho mặc định** cấu hình trong `StoreProfiles` (Owner) và cấp phát theo **FEFO**. Tham chiếu: [`backend/docs/srs/SRS_Task090_uc9-retail-checkout-stock-deduction.md`](../../../backend/docs/srs/SRS_Task090_uc9-retail-checkout-stock-deduction.md) (**Approved** 29/04/2026).

**`total_amount`**: tính từ `lines`; **tổng giảm** = `discountAmount` + phần voucher; **`discount_amount`** trên `sales_orders` = tổng (hoặc tách cột `voucher_discount` — tuỳ migration).

---

## 5. Thành công — `201 Created`

Giống Task055 (đơn mới, `orderChannel: "Retail"`).

---

## 6. Logic DB (transaction)

1. Resolve `customer_id` (walk-in seed hoặc FK).
2. Validate `lines`, đơn vị, giá (có thể so khớp `sale_price` hiện hành với **sai lệch cho phép** — policy chống sửa giá client).
3. Tính `total_amount`, voucher, `discount_amount` tổng.
4. **Lock + kiểm tra tồn** theo kho mặc định (`StoreProfiles`) và chiến lược FEFO; nếu thiếu tồn → **409** (không tạo đơn, không đổi tồn).  
5. **`INSERT sales_orders`** (`order_channel = 'Retail'`, `user_id` = JWT, `status` thường **`Delivered`** cho POS tại quầy).  
6. **`INSERT order_details`**.  
7. **Ghi nhận xuất kho**: `INSERT StockDispatches` (1 phiếu/đơn), `UPDATE Inventory.quantity` (giảm), `INSERT InventoryLogs` (OUTBOUND, quantity_change âm), `UPDATE OrderDetails.dispatched_qty` (đủ).  
8. Commit.

---

## 7. Lỗi

- **400**: giỏ rỗng, voucher không hợp lệ, giá sai.
- **404**: `customerId` không tồn tại.
- **409**: không đủ tồn (Task090) hoặc xung đột tồn do concurrent (sau khi lock).
- **401** / **403** / **500**.

---

## 8. Zod (body — FE)

```typescript
import { z } from "zod";

const PosLineSchema = z.object({
  productId: z.number().int().positive(),
  unitId: z.number().int().positive(),
  quantity: z.number().positive(),
  unitPrice: z.number().nonnegative(),
});

export const RetailCheckoutBodySchema = z
  .object({
    customerId: z.number().int().positive().nullable().optional(),
    walkIn: z.boolean().optional(),
    lines: z.array(PosLineSchema).min(1),
    discountAmount: z.number().nonnegative().optional().default(0),
    voucherCode: z.string().max(50).nullable().optional(),
    paymentStatus: z.enum(["Paid", "Unpaid", "Partial"]).optional().default("Paid"),
    notes: z.string().max(1000).nullable().optional(),
    shiftReference: z.string().max(100).optional(),
  })
  .refine(
    (d) => d.walkIn !== false || (d.customerId != null && d.customerId > 0),
    { message: "Cần customerId hoặc walkIn = true" }
  );
```

**Ghi chú:** FE không cần thêm field chọn kho trong body checkout (không có `locationId`); kho trừ tồn do backend cấu hình.

---

## 9. Ánh xạ UI

| UI | API |
| :-- | :-- |
| `useOrderStore` `cart` → `lines` | map `productId`, `unitId`, `quantity`, `unitPrice` |
| `getFinalTotal` | server tính lại; không tin tưởng `lineTotal` client |
| `customerName` "Khách lẻ" | `walkIn: true` |
