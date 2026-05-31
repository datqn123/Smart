# 📄 API SPEC: `DELETE /api/v1/cash-transactions/{id}` — Xóa giao dịch thu chi — Task068

> **Trạng thái**: Approved (đồng bộ SRS Task064–068 + PRD quỹ — 02/05/2026)  
> **SRS backend:** [`../../../backend/docs/srs/SRS_Task064-068_cash-transactions-api.md`](../../../backend/docs/srs/SRS_Task064-068_cash-transactions-api.md), [`../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md`](../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md)  
> **Feature**: Cashflow — **Giao dịch thu chi**

---

## 1. Mục tiêu

Xóa cứng bản ghi **`cash_transactions`** chỉ khi **`Pending`** hoặc **`Cancelled`** và **`finance_ledger_id IS NULL`**.

---

## 2. Endpoint

**`DELETE /api/v1/cash-transactions/{id}`**

---

## 3. Tham chiếu

[`Database_Specification.md`](../UC/Database_Specification.md) §12.1 — không xóa khi đã ghi sổ.

---

## 4. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Authentication** | `Bearer` |
| **RBAC** | **`mp.can_view_finance === true`** và (**`created_by` = user hiện tại** **hoặc** **Admin**) |

---

## 5. Request

Không body.

---

## 6. `200 OK` — chuẩn dự án

Đồng bộ với các `DELETE` khác trong `smart-erp` (vd. sản phẩm, phiếu nhập): **luôn** trả envelope JSON, **không** dùng `204` cho endpoint này.

```json
{
  "success": true,
  "data": null,
  "message": "Đã xóa giao dịch"
}
```

---

## 7. Logic & Database

1. Load row theo `id`.  
2. **404** nếu không tồn tại.  
3. Nếu `status = Completed` **hoặc** `finance_ledger_id IS NOT NULL` → **409**  
   `"Không thể xóa giao dịch đã ghi nhận vào sổ cái"`.  
4. `DELETE FROM cash_transactions WHERE id = :id`.

---

## 8. Lỗi

- **401**, **403** (thiếu quyền tài chính **hoặc** không phải người tạo **và** không phải Admin), **404**, **409**, **500**

Ví dụ **409**:

```json
{
  "success": false,
  "error": "CONFLICT",
  "message": "Không thể xóa giao dịch đã hoàn tất hoặc đã liên kết sổ cái"
}
```

---

## 9. Zod

Dùng chung `CashTransactionIdParamsSchema` (Task066).

---

## 10. Ghi chú FE

Ẩn nút xóa khi `status === Completed` để giảm round-trip.
