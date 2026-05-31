# API SPEC — Task092 — Voucher POS (`GET /vouchers`, preview)

> **Trạng thái:** Draft (đồng bộ SRS [`SRS_Task092_uc9-retail-voucher-preview.md`](../../../backend/docs/srs/SRS_Task092_uc9-retail-voucher-preview.md) — Approved)  
> **RBAC:** `can_manage_orders` (giống Task060)  
> **Envelope:** [`API_RESPONSE_ENVELOPE.md`](API_RESPONSE_ENVELOPE.md)

---

## 1. `GET /api/v1/vouchers`

- **Mục đích:** Danh sách voucher **đang áp dụng được** (active, trong hạn, còn lượt nếu có `max_uses`).
- **Query:** `page` (mặc định `1`), `limit` (mặc định `5`, tối đa `50`).
- **Sắp xếp:** `created_at DESC`, `id DESC`.
- **Response `data`:** `{ items[], page, limit, total }` — mỗi item: `id`, `code`, `name`, `discountType`, `discountValue`, `validFrom`, `validTo`, `isActive`, `usedCount`, `maxUses`, `createdAt`.

---

## 2. `GET /api/v1/vouchers/{id}`

- **Mục đích:** Chi tiết một voucher (kể cả inactive — theo SRS; **404** nếu không có `id`).
- **Response:** một object cùng shape phần tử trong `items` ở trên.

---

## 3. `POST /api/v1/sales-orders/retail/voucher-preview`

- **Mục đích:** Ước tính giảm giá trên **giỏ** (cùng validate dòng / giá như checkout).
- **Body:**

```json
{
  "voucherId": 1,
  "voucherCode": null,
  "lines": [{ "productId": 5, "unitId": 12, "quantity": 1, "unitPrice": 10000 }],
  "discountAmount": 0
}
```

| Trường | Bắt buộc | Ghi chú |
| :--- | :--- | :--- |
| `voucherId` | Một trong hai | Cùng với `voucherCode` — ít nhất một |
| `voucherCode` | Một trong hai | Trim, max 50 |
| `lines` | Có | Giống Task060 |
| `discountAmount` | Không | Mặc định 0 |

- **200:** `applicable: true`, `voucherId`, `voucherCode`, `voucherName`, `discountType`, `discountValue`, `subtotal`, `manualDiscountAmount`, `voucherDiscountAmount`, `totalDiscountAmount`, `payableAmount`, `message` (null khi applicable).
- **400:** Không tìm thấy mã / không trong hạn / hết lượt / `lines` không hợp lệ / `voucherId` và `voucherCode` không khớp.

---

## 4. Checkout Task060 — bổ sung Task092

`POST /api/v1/sales-orders/retail/checkout` với `voucherCode` hợp lệ:

- Trong **cùng transaction**: sau khi tạo đơn + dòng + trừ tồn (Task090), server **`used_count += 1`** trên `vouchers` và **`INSERT voucher_redemptions`** (`voucher_id`, `sales_order_id`).
- **409** nếu voucher **hết lượt** tại thời điểm thanh toán (race an toàn nhờ khóa dòng voucher `FOR UPDATE` trước khi ghi đơn).

Hủy đơn bán lẻ có voucher: hoàn **`used_count`** và xóa bản ghi `voucher_redemptions` tương ứng (khi hủy thành công).

---

## 5. Flyway

- **`V24__task092_voucher_usage_and_redemptions.sql`**: cột `vouchers.used_count`, `vouchers.max_uses`; bảng `voucher_redemptions`.
