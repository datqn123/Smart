# Dashboard API Contracts

Base path: `/api/v1/dashboard`

> Response envelope: `{ success: boolean, data: T, message: string }`

---

## GET /api/v1/dashboard

**Mô tả:** Dashboard KPI — tổng quan tài chính, xu hướng, kênh, chỉ số, đơn hàng gần đây, chờ duyệt, khách hàng top, dòng tiền, cảnh báo tồn kho.

**Auth:** JWT + `can_view_dashboard`

**Query parameters:**
- `trendDays` (int, optional) — Số ngày xu hướng doanh thu
- `recentLimit` (int, optional) — Số đơn hàng gần đây
- `topCustomerLimit` (int, optional) — Số khách hàng top
- `alertLimit` (int, optional) — Số cảnh báo tồn kho
- `include` (string, optional) — Lọc section (ví dụ `financial,revenueTrend`)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "financial": {
      "todayRevenue": "BigDecimal — Doanh thu hôm nay",
      "yesterdayRevenue": "BigDecimal — Doanh thu hôm qua",
      "todayOrders": "long — Số đơn hôm nay",
      "pctChange": "BigDecimal — % thay đổi so với hôm qua",
      "avgOrderValue": "BigDecimal — Giá trị trung bình đơn"
    },
    "revenueTrend": [
      {
        "date": "string — Ngày (yyyy-MM-dd)",
        "label": "string — Nhãn",
        "revenue": "BigDecimal — Doanh thu",
        "orders": "long — Số đơn"
      }
    ],
    "channelBreakdown": {
      "retail": "BigDecimal — Doanh thu bán lẻ",
      "wholesale": "BigDecimal — Doanh thu bán sỉ",
      "total": "BigDecimal — Tổng doanh thu"
    },
    "kpis": {
      "totalSkus": "long — Tổng số SKU",
      "totalValue": "BigDecimal — Tổng giá trị tồn kho",
      "lowStockCount": "long — Số SKU sắp hết",
      "expiringSoonCount": "long — Số SKU sắp hết hạn",
      "pendingOrders": "long — Đơn chờ xử lý",
      "allOrdersTotal": "long — Tổng đơn hàng",
      "pendingApprovals": "long — Số yêu cầu chờ duyệt",
      "approvalByType": "Map[string, long] — Số chờ duyệt theo loại"
    },
    "recentOrders": [
      {
        "id": "int",
        "orderCode": "string — Mã đơn",
        "orderChannel": "string — Kênh (retail/wholesale)",
        "customerName": "string — Tên khách",
        "finalAmount": "BigDecimal — Thành tiền",
        "status": "string — Trạng thái",
        "createdAt": "Instant — Ngày tạo"
      }
    ],
    "pendingApprovals": [
      {
        "entityType": "string — Loại đối tượng",
        "entityId": "long — ID đối tượng",
        "transactionCode": "string — Mã giao dịch",
        "type": "string — Loại",
        "creatorName": "string — Người tạo",
        "totalAmount": "BigDecimal — Tổng tiền",
        "date": "Instant — Ngày tạo"
      }
    ],
    "topCustomers": [
      {
        "id": "int",
        "name": "string — Tên khách",
        "orderCount": "long — Số đơn",
        "totalSpent": "BigDecimal — Tổng chi tiêu"
      }
    ],
    "cashflow": {
      "income": "BigDecimal — Thu",
      "expense": "BigDecimal — Chi",
      "net": "BigDecimal — Ròng"
    },
    "lowStockAlerts": [
      {
        "id": "long",
        "productName": "string — Tên sản phẩm",
        "skuCode": "string — Mã SKU",
        "quantity": "int — Tồn hiện tại",
        "minQuantity": "int — Tồn tối thiểu",
        "unitName": "string — Đơn vị tính"
      }
    ]
  },
  "message": "Thành công"
}
```

**Errors:** 401 (JWT hết hạn), 403 (thiếu quyền `can_view_dashboard`)
