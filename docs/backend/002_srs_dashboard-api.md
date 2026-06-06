# SRS - Dashboard API

> Agent: SRS_WRITER  
> Ngày cập nhật: 06/06/2026  
> Trạng thái: Draft  
> Scope chính: `backend/smart-erp`  
> Liên quan frontend: `frontend/mini-erp/src/features/dashboard/`

## 1. Mục tiêu

Backend hiện tại không có DashboardController — FE gửi 8 truy vấn song song, mỗi truy vấn trả về danh sách chi tiết, và FE tự tổng hợp (tổng doanh thu hôm nay, so sánh hôm qua, xu hướng 7/30 ngày, top khách hàng, dòng tiền tháng, v.v.).

Mục tiêu: tạo **một endpoint dashboard tổng hợp** trả về dữ liệu đã được tính toán sẵn (pre-aggregated) ở backend, loại bỏ các truy vấn dư thừa (vd: fetch 100 orders chỉ để tính tổng doanh thu hôm nay, fetch 50 customers chỉ để lấy top 5).

## 2. Functional Scope

### 2.1. Consolidated Endpoint

**`GET /api/v1/dashboard`**

Trả về toàn bộ dữ liệu trong một response. Phân quyền gọi endpoint: `can_view_dashboard`.

### 2.2. Response Structure

```jsonc
{
  "success": true,
  "data": {
    // --- Financial quick-analysis (chỉ trả khi user role Owner/Admin/Manager) ---
    "financial": {
      "todayRevenue": 12500000.0,
      "yesterdayRevenue": 10000000.0,
      "todayOrders": 15,
      "pctChange": 25.0,          // % so với hôm qua; null nếu hôm qua = 0
      "avgOrderValue": 833333.0
    },

    // --- Doanh thu trend theo ngày (7 hoặc 30 ngày) ---
    "revenueTrend": [
      {
        "date": "2026-06-01",
        "label": "01/06",
        "revenue": 5000000.0,
        "orders": 6
      }
      // ...
    ],

    // --- Cơ cấu kênh bán trong kỳ ---
    "channelBreakdown": {
      "retail": 8000000.0,
      "wholesale": 4500000.0,
      "total": 12500000.0
    },

    // --- KPI tổng quan (luôn trả) ---
    "kpis": {
      "totalSkus": 120,
      "totalValue": 850000000.0,
      "lowStockCount": 5,
      "expiringSoonCount": 3,
      "pendingOrders": 7,
      "allOrdersTotal": 340,
      "pendingApprovals": 4,
      "approvalByType": {
        "Inbound": 2,
        "Outbound": 1,
        "Return": 1,
        "Debt": 0
      }
    },

    // --- 5 đơn gần đây ---
    "recentOrders": [
      {
        "id": 101,
        "orderCode": "DD-20260606-001",
        "orderChannel": "Retail",
        "customerName": "Nguyễn Văn A",
        "finalAmount": 250000.0,
        "status": "Completed",
        "createdAt": "2026-06-06T10:30:00Z"
      }
      // ...
    ],

    // --- 5 approval pending gần nhất ---
    "pendingApprovals": [
      {
        "entityType": "stock_receipt",
        "entityId": 1,
        "transactionCode": "PN-001",
        "type": "Inbound",
        "creatorName": "Trần Văn B",
        "totalAmount": 15000000.0,
        "date": "2026-06-06T09:00:00Z"
      }
      // ...
    ],

    // --- 5 khách hàng chi tiêu nhiều nhất ---
    "topCustomers": [
      {
        "id": 1,
        "name": "Công ty TNHH ABC",
        "orderCount": 12,
        "totalSpent": 150000000.0
      }
      // ...
    ],

    // --- Dòng tiền từ đầu tháng đến hôm nay ---
    "cashflow": {
      "income": 50000000.0,
      "expense": 30000000.0,
      "net": 20000000.0
    },

    // --- 5 mặt hàng tồn thấp ---
    "lowStockAlerts": [
      {
        "id": 1,
        "productName": "Sữa tươi Vinamilk",
        "skuCode": "VNM-001",
        "quantity": 2,
        "minQuantity": 10,
        "unitName": "thùng"
      }
      // ...
    ]
  }
}
```

### 2.3. Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `trendDays` | int | `7` | Số ngày cho revenueTrend (7 hoặc 30). Nếu 30, server trả đủ 30 điểm. |
| `recentLimit` | int | `5` | Số lượng recentOrders trả về (max 20) |
| `topCustomerLimit` | int | `5` | Số lượng topCustomers trả về (max 20) |
| `alertLimit` | int | `5` | Số lượng lowStockAlerts trả về (max 20) |
| `include` | string | *(all)* | Comma-separated: `financial`, `trend`, `channel`, `kpis`, `orders`, `approvals`, `customers`, `cashflow`, `alerts`. Cho phép FE chỉ lấy những phần cần. |

**Ví dụ**: `GET /api/v1/dashboard?trendDays=30&recentLimit=10&include=kpis,orders,alerts`

### 2.4. Security & Authorization

- Endpoint yêu cầu authenticated user + `can_view_dashboard` authority.
- Nếu user không có quyền tài chính (không phải Owner/Admin/Manager), trả `financial`, `revenueTrend`, `channelBreakdown`, `cashflow` là `null` (hoặc omit). Các phần còn lại vẫn trả bình thường.
- Kiểm tra quyền tài chính dựa trên role trong JWT (claim `role`): Owner, Admin, Manager được xem.

### 2.5. Tính toán chi tiết từng phần

#### 2.5.1. Financial
- Lọc `sales_orders` có `created_at` = hôm nay và hôm qua.
- Bỏ đơn Cancelled.
- `pctChange` = `(todayRevenue - yesterdayRevenue) / yesterdayRevenue * 100`. null nếu yesterdayRevenue = 0.
- `avgOrderValue` = `todayRevenue / todayOrders`. 0 nếu todayOrders = 0.

#### 2.5.2. Revenue Trend
- Lọc `sales_orders` trong `trendDays` ngày gần nhất (bao gồm hôm nay).
- Bỏ đơn Cancelled.
- Group theo `yyyy-mm-dd` (theo local time của server hoặc UTC).
- Đảm bảo đủ `trendDays` điểm, kể cả ngày không có đơn (revenue = 0, orders = 0).
- Label format: `dd/mm`.

#### 2.5.3. Channel Breakdown
- Lọc `sales_orders` cùng cửa sổ `trendDays`.
- Bỏ đơn Cancelled.
- `retail` = sum of `finalAmount` nơi `orderChannel = 'Retail'`.
- `wholesale` = sum nơi `orderChannel = 'Wholesale'`.

#### 2.5.4. KPIs
- **totalSkus, totalValue, lowStockCount, expiringSoonCount**: tái sử dụng `InventorySummaryService.summary()` (đã có).
- **pendingOrders**: count `sales_orders` nơi `status = 'Pending'`.
- **allOrdersTotal**: total count `sales_orders` (không filter).
- **pendingApprovals, approvalByType**: tái sử dụng `ApprovalsService.listPending()` response summary.

#### 2.5.5. Recent Orders
- Query `sales_orders` sort `createdAt DESC`, limit = `recentLimit`.
- Trả các field: id, orderCode, orderChannel, customerName, finalAmount, status, createdAt.

#### 2.5.6. Pending Approvals
- Query `approvals_pending` sort by `date DESC`, limit 5 (hard-coded hoặc từ query param).

#### 2.5.7. Top Customers
- Query `customers` join với `sales_orders`, group by customer_id, tính `orderCount` và `totalSpent`.
- Sort by `totalSpent DESC`, limit = `topCustomerLimit`.
- Nếu performance không đảm bảo, có thể materialize view hoặc cache 5 phút.

#### 2.5.8. Cashflow
- Query `cash_movements` (hoặc `cash_transactions`) từ ngày đầu tháng hiện tại đến hôm nay.
- Chỉ lấy Completed transactions.
- `income` = sum nơi `direction = 'Income'`.
- `expense` = sum nơi `direction = 'Expense'`.
- `net` = `income - expense`.

#### 2.5.9. Low Stock Alerts
- Tái sử dụng `InventoryListService.list()` với filter `stockLevel = 'low_stock'`, sort `quantity ASC`, limit = `alertLimit`.

### 2.6. Error Responses

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 401 | UNAUTHORIZED | Token hết hạn/không hợp lệ |
| 403 | FORBIDDEN | Không có `can_view_dashboard` |

### 2.7. Caching & Performance

- Response có thể cached 30 giây ở API gateway hoặc CDN (Cache-Control: public, max-age=30).
- Backend nên cache internal `topCustomers` và `cashflow` 5 phút vì các tính toán này nặng.

## 3. Non-functional Requirements

- Response time < 500ms (cached) / < 2s (cold).
- Khi `include` param được dùng, chỉ query các phần được yêu cầu — không query thừa.
- Các phần độc lập (kpis, orders, approvals, alerts) nên query song song bằng CompletableFuture hoặc @Async.

## 4. Acceptance Criteria

1. `GET /api/v1/dashboard` (không param) trả về đủ 9 section đã định nghĩa.
2. User có role Staff (không financial) nhận `financial`, `revenueTrend`, `channelBreakdown`, `cashflow` là `null`.
3. `trendDays=30` trả về đúng 30 điểm dữ liệu.
4. `include=kpis,orders` chỉ trả về đúng 2 section đó.
5. Top customers được sắp xếp theo `totalSpent` giảm dần.
6. Cashflow chỉ tính month-to-date, không bao gồm các tháng trước.
7. Revenue trend không bỏ sót ngày nào (kể cả ngày 0).
8. Low stock alerts trả về đúng `alertLimit` items, sort theo quantity tăng dần.
9. `pctChange` tính đúng %, null khi yesterdayRevenue = 0.
