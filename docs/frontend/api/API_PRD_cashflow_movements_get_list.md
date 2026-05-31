# API SPEC — Dòng tiền thống nhất (`GET /api/v1/cashflow/movements`)

> **Trạng thái**: Approved (PRD — 02/05/2026)  
> **SRS:** [`../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md`](../../../backend/docs/srs/SRS_PRD_cash-transactions-admin-unified-multi-fund.md)  
> **Feature:** Báo cái / Cashflow — **Admin-only** (đọc ledger ∪ phiếu thủ công Pending/Cancelled).

---

## 1. Overview

| Thuộc tính | Giá trị |
| :--------- | :------ |
| **Method** | `GET` |
| **Path** | `/api/v1/cashflow/movements` |
| **Auth** | `Bearer` |
| **RBAC** | `can_view_finance` **và** **Admin** (JWT) — Staff có finance vẫn **403** |

---

## 2. Query parameters

| Tham số | Kiểu | Mặc định | Mô tả |
| :------ | :--- | :------- | :---- |
| `dateFrom` | date | — | Nếu **cả** `dateFrom` và `dateTo` **đều bỏ trống** → BE gán **cả hai = ngày hôm nay** (server local date) |
| `dateTo` | date | — | Xem trên |
| `fundId` | int | — | Lọc theo quỹ |
| `search` | string | — | Tìm theo policy JDBC (mô tả, tham chiếu, …) |
| `page` | int | `1` | |
| `limit` | int 1–100 | `20` | |

---

## 3. `200 OK` — shape `data`

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "ledger:1001",
        "sourceKind": "Ledger",
        "transactionDate": "2026-05-02",
        "amount": 500000,
        "direction": "Income",
        "description": "Thu bán lẻ",
        "referenceType": "CashTransaction",
        "referenceId": 12,
        "fundId": 1,
        "fundCode": "CASH",
        "cashTransactionId": 12,
        "status": null,
        "category": null
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 1,
    "summary": {
      "totalIncome": 500000,
      "totalExpense": 0,
      "net": 500000
    }
  },
  "message": "Thao tác thành công"
}
```

- `id` ổn định dạng **`ledger:{financeledger.id}`** hoặc **`cash:{cashtransactions.id}`** (xem `CashflowMovementJdbcRepository`).
- `sourceKind`, `referenceType`, `referenceId`, `cashTransactionId`, `status`, `category` có thể **null** tùy nguồn — xem `@JsonInclude` trên BE.

---

## 4. Lỗi

**400** (khoảng ngày không hợp lệ, `fundId` không parse được), **401**, **403**, **500**.

---

## 5. Ghi chú FE

Chưa có trang tích hợp trong `mini-erp`; khi làm UI “Dòng tiền thống nhất”, gọi endpoint này và ẩn menu nếu user không Admin.
