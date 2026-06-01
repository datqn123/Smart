# SRS — Breadcrumb Navigation Tiếng Việt

> **File**: `docs/frontend/srs/SRS_Task119_breadcrumb-vietnamese.md`
> **Người viết**: SRS_WRITER Agent
> **Ngày**: 31/05/2026
> **Trạng thái**: Draft
> **Task**: Task119

## 1. Tóm tắt

- **Vấn đề**: Breadcrumb trên Header component hiển thị tiếng Anh ("Home", "Stock", "Inbound"...), không nhất quán với phần còn lại của UI đã dùng tiếng Việt (sidebar, notifications).
- **Mục tiêu**: Đổi toàn bộ breadcrumb text sang tiếng Việt để đồng bộ ngôn ngữ giao diện.
- **Phạm vi**: UI-only — không ảnh hưởng backend, database, hay API.

## 2. Phạm vi

### 2.1 In-scope

- Đổi "Home" → "Trang chủ" trong breadcrumb
- Đổi "Dashboard" → "Bảng điều khiển"
- Map toàn bộ path segment cuối cùng sang tiếng Việt dựa trên nhãn sidebar đã có

### 2.2 Out-of-scope

- Các breadcrumb category/product hierarchy (CategoryBreadcrumb — là data từ API)
- Sidebar labels (đã là tiếng Việt)
- Các page title / document head
- Test files cho Header component

## 3. Persona & Quyền

- **Tất cả user** (không phân biệt role) — breadcrumb là UI chung, không phụ thuộc quyền

## 4. User Stories

- **US1**: Là user, tôi muốn breadcrumb hiển thị tiếng Việt ("Trang chủ / Tồn kho") để dễ định vị trang.

## 5. UI Spec

### 5.1 Component

- `src/components/shared/layout/Header.tsx`
- Breadcrumb region hiện tại: dòng 205-210

### 5.2 Mapping path → tiếng Việt

| URL path | Hiện tại (EN) | Mới (VI) |
|----------|--------------|----------|
| `/` | Home | Trang chủ |
| `/dashboard` | Dashboard | Bảng điều khiển |
| `/dashboard/ai-insights` | Ai-insights | Phân tích AI |
| `/inventory/stock` | Stock | Tồn kho |
| `/inventory/inbound` | Inbound | Phiếu nhập kho |
| `/inventory/dispatch` | Dispatch | Xuất kho & Điều phối |
| `/inventory/locations` | Locations | Vị trí kho |
| `/products/categories` | Categories | Danh mục sản phẩm |
| `/products/list` | List | Quản lý sản phẩm |
| `/products/suppliers` | Suppliers | Nhà cung cấp |
| `/products/customers` | Customers | Khách hàng |
| `/orders/retail` | Retail | Đơn bán lẻ |
| `/orders/wholesale` | Wholesale | Lịch sử hóa đơn |
| `/orders/returns` | Returns | Đơn trả hàng |
| `/cashflow/transactions` | Transactions | Giao dịch thu chi |
| `/cashflow/debt` | Debt | Sổ nợ |
| `/cashflow/ledger` | Ledger | Sổ cái tài chính |
| `/analytics/revenue` | Revenue | Doanh thu |
| `/analytics/top-products` | Top-products | Top sản phẩm |
| `/ai/chat` | Chat | Trợ lý ảo AI |
| `/settings/store-info` | Store-info | Thông tin cửa hàng |
| `/settings/employees` | Employees | Quản lý nhân viên |
| `/settings/alerts` | Alerts | Cấu hình cảnh báo |
| `/settings/system-logs` | System-logs | Nhật ký hệ thống |

### 5.3 Fallback

- Nếu path segment không có trong mapping → giữ nguyên capitalize (ví dụ path lạ → "Somepath")

## 6. Technical Mapping

- **File**: `src/components/shared/layout/Header.tsx`
- **Dòng ảnh hưởng**: 130-135 (currentPage logic) + 205-208 (Home text)
- **Không cần** thêm dependencies, route, API

## 7. Acceptance Criteria

### 7.1 Happy path

```gherkin
Given User đang ở trang /inventory/stock
When Nhìn breadcrumb trên Header
Then Thấy "Trang chủ / Tồn kho"

Given User đang ở trang /inventory/inbound
When Nhìn breadcrumb
Then Thấy "Trang chủ / Phiếu nhập kho"

Given User đang ở trang /dashboard
When Nhìn breadcrumb
Then Thấy "Trang chủ / Bảng điều khiển"
```

### 7.2 Edge case

```gherkin
Given User đang ở path không có trong mapping (vd /some/new-page)
When Nhìn breadcrumb
Then Thấy "Trang chủ / Some-new-page" (fallback capitalize)
```

## 8. Open Questions

- Không có — mapping dựa trên sidebar labels đã được PO approve.
