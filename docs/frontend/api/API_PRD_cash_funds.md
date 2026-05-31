# API SPEC — Quỹ tiền (`/api/v1/cash-funds`)

> **Trạng thái**: Approved (PRD — 02/05/2026)  
> **SRS:** [`../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md`](../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md)  
> **Feature:** Cashflow — chọn quỹ khi tạo phiếu thu/chi; quản trị quỹ (Admin).

---

## 1. `GET /api/v1/cash-funds`

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Auth** | `Bearer` |
| **RBAC** | `mp.can_view_finance === true` |

**Response `200` — `data`:**

```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "code": "CASH", "name": "Tiền mặt", "isDefault": true, "isActive": true }
    ]
  },
  "message": "Thao tác thành công"
}
```

Chỉ trả các quỹ **`is_active = true`**, sắp xếp theo policy BE.

---

## 2. `POST /api/v1/cash-funds` — Admin

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **RBAC** | `can_view_finance` **và** role **Admin** |

**Body (JSON):**

| Trường | Kiểu | Bắt buộc |
| :----- | :--- | :------- |
| `code` | string ≤ 30 | Có |
| `name` | string ≤ 255 | Có |
| `isDefault` | boolean | Không |

**`201`** — một `CashFundItemData` trong `data`.

---

## 3. `PATCH /api/v1/cash-funds/{id}` — Admin

**Body:** partial — `isActive` (boolean), `isDefault` (boolean).

**`200`** — `CashFundItemData` sau cập nhật.

---

## 4. Lỗi chung

**400**, **401**, **403** (thiếu finance hoặc không Admin cho POST/PATCH), **404**, **500** — envelope chuẩn dự án.

---

## 5. Ghi chú FE

`frontend/mini-erp/src/features/cashflow/api/cashFundsApi.ts` — `getCashFundsList` cho dropdown tạo phiếu (Task065).
