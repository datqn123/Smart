# Tóm tắt Chức năng Chính - Dự án Mini-ERP

Tài liệu này tổng hợp các chức năng chính của hệ thống Mini-ERP dựa trên 13 đặc tả Use Case (UC) đã được phê duyệt. Hệ thống tập trung vào tính đơn giản, hiệu quả và tích hợp AI để hỗ trợ người dùng không chuyên về công nghệ.

---

## 📋 Tổng quan Dự án

- **Loại dự án**: Multi-platform Mini-ERP System (Web Dashboard + Mobile App planned)
- **Đối tượng người dùng**: Chủ doanh nghiệp nhỏ, nhà bán lẻ không rành công nghệ
- **Triết lý thiết kế**: "The Guided Sanctuary" - Đơn giản, dễ tiếp cận, AI hỗ trợ nhưng không thay thế quyết định con người
- **Công nghệ chính**: React 19 + Vite + TypeScript + Tailwind CSS v4 + Shadcn UI + TanStack Query + Zustand
- **Database**: PostgreSQL 15+ (24 tables, 42+ foreign keys)
- **AI Integration**: DeepSeek LLM, Azure Document Intelligence (OCR), Web Speech API (Voice)

---

## 1. Hệ thống Dashboard & Phân tích (Analytics)

### UC1 - Bảng điều khiển tổng quan (Dashboard)

- **Màn hình mặc định** sau khi đăng nhập (`/dashboard`)
- **Chỉ số kinh doanh cốt lõi**:
  - Tổng giá trị tồn kho (Inventory Value)
  - Báo cáo lãi lỗ (Profit & Loss)
  - Trạng thái kho: Hàng sắp hết (Low Stock), hàng cận date (Expiring Soon)
  - Giao dịch chờ phê duyệt (Pending Approvals)
- **Thiết kế**: Tối giản, tập trung vào dữ liệu quan trọng nhất
- **Route**: `/dashboard`

### UC2 - Phân tích kinh doanh bằng AI (AI Business Insight)

- **Công nghệ**: DeepSeek LLM phân tích dữ liệu thực tế từ hệ thống
- **Chức năng**:
  - Phân tích snapshot dashboard tại thời điểm yêu cầu
  - Đưa ra lời khuyên chiến lược và gợi ý tối ưu hóa kinh doanh
  - Trả kết quả dưới dạng Markdown dễ đọc
- **Lưu vết**: Mọi phân tích AI được lưu vào `AIInsights` table
- **Routes**: `/analytics/revenue`, `/analytics/top-products`

---

## 2. Quản trị & Thiết lập (Administration)

### UC3 - Quản lý tài khoản nhân viên (Manage Staff Accounts)

- **Người thực hiện**: Chủ cửa hàng (Owner role)
- **Chức năng**:
  - Tạo mới, cập nhật thông tin nhân viên
  - Phân quyền chi tiết qua Roles (Owner, Staff, Admin)
  - Khóa tài khoản (Lock) hoặc reset mật khẩu
  - Xem lịch sử đăng nhập (last_login)
- **Permissions JSON**: 9 quyền chi tiết (view_dashboard, manage_staff, approve, v.v.)
- **Route**: `/settings/employees`

### UC5 - Cấu hình cài đặt cảnh báo (Configure Alert Settings)

- **Cá nhân hóa** theo từng người dùng
- **Loại cảnh báo**:
  - LowStock: Tồn kho dưới ngưỡng
  - ExpiryDate: Hàng cận date (≤ 30 ngày)
  - HighValueTransaction: Giao dịch giá trị cao
  - PendingApproval: Chờ phê duyệt
- **Kênh nhận**: App, Email, Zalo, SMS
- **Tần suất**: Realtime, Daily Digest, Weekly
- **Route**: `/settings/store-info` (planned)

---

## 3. Quản lý Kho hàng (Inventory Management)

### UC6 - Danh sách tồn kho (Inventory List)

- **Theo dõi**:
  - Số lượng tồn kho theo thời gian thực (real-time stock)
  - Vị trí lưu trữ (kho/kệ: WH01-A1, WH01-B2)
  - Hạn sử dụng (expiry date tracking)
  - Số lô (batch number tracking)
- **Tính năng nâng cao**:
  - Tìm kiếm thông minh bằng ngôn ngữ tự nhiên (qua AI Chat)
  - Kiểm kê kho (Stock Audit) - đối chiếu tồn kho vật lý vs hệ thống
  - Xuất/nhập dữ liệu qua Excel
  - Cảnh báo tự động khi `quantity ≤ min_quantity`
- **Đa đơn vị tính**: Tồn kho luôn lưu theo đơn vị cơ sở (base unit)
- **Routes**: `/inventory/categories`, `/inventory/inbound`, `/inventory/audit`

### UC10 - Quản lý xuất kho & Điều phối (Stock Dispatch)

- **Xử lý yêu cầu xuất kho** dựa trên đơn bán (SalesOrder)
- **Picking List**: Tự động chỉ dẫn vị trí lấy hàng (Warehouse Location)
- **Cập nhật tồn kho** ngay khi hoàn tất xuất kho (via InventoryLogs)
- **Xuất kho một phần** (Partial Dispatch):
  - Tạo Backorder tự động cho phần chưa đủ
  - `OrderDetail.dispatchedQty` tracking số lượng đã xuất
- **Audit Trail**: Mọi biến động kho được ghi log trong `InventoryLogs`
- **Status Flow**: `Pending → Full` hoặc `Pending → Partial → Backorder` hoặc `Cancelled`

---

## 4. Danh mục & Sản phẩm (Products & Catalogs)

### UC8 - Quản lý sản phẩm (Manage Products)

- **Thông tin sản phẩm**:
  - Mã SKU (duy nhất), Barcode (có thể trùng)
  - Danh mục phân cấp (Categories tree - self-referencing)
  - Nhiều hình ảnh (ProductImages table, primary + secondary images)
  - Trọng lượng (gram) - dùng cho tính phí vận chuyển
- **Quản lý giá**:
  - Giá vốn (cost_price) - tính lãi lỗ chính xác
  - Giá bán đề nghị (sale_price)
  - Lịch sử giá theo thời gian (ProductPriceHistory)
- **Đơn vị tính quy đổi** (ProductUnits):
  - Ví dụ: Thùng → Hộp → Cái
  - Mỗi sản phẩm có ĐÚNG 1 đơn vị cơ sở (is_base_unit = true)
  - Conversion rate > 0
- **Trạng thái**: Active /Inactive (Inactive → không cho bán/nhập mới)

### UC7 - Quản lý phiếu nhập kho (Stock Receipts)

- **Theo dõi lịch sử nhập hàng** từ nhà cung cấp (Suppliers)
- **Workflow phê duyệt**:
  - `Draft` → Staff tạo nháp
  - `Pending` → Gửi phê duyệt cho Owner
  - `Approved` → Owner duyệt → **cập nhật Inventory + FinanceLedger**
  - `Rejected` → Từ chối
- **Chi tiết phiếu nhập** (StockReceiptDetails):
  - Sản phẩm, đơn vị, số lượng, đơn giá
  - Số lô, hạn sử dụng
  - Line total tự động tính (quantity × cost_price)
- **OCR Support** (UC12): Tự động trích xuất dữ liệu từ ảnh hóa đơn
- **Route**: `/inventory/inbound`

---

## 5. Quản lý Đơn hàng (Orders Management)

### UC9 - Quản lý đơn bán hàng (Sales Orders)

- **Trung tâm điều phối** đơn hàng từ khách hàng (Customers)
- **Thông tin đơn hàng**:
  - Mã đơn tự sinh (SO-YYYY-NNNN)
  - Khách hàng, người tạo, địa chỉ giao hàng
  - Total amount, discount amount, final amount (auto-calculated)
- **Đối chiếu tồn kho** thời gian thực:
  - Cảnh báo khi không đủ hàng
  - Gợi ý backorder nếu thiếu
- **Chi tiết đơn** (OrderDetails):
  - Sản phẩm, đơn vị, số lượng, giá tại thời điểm đặt (price_at_time)
  - Tracking `dispatched_qty` vs `quantity`
  - Line total tự động tính
- **Backorder Logic**:
  - `parent_order_id` trỏ về đơn cha
  - Xóa đơn cha → đơn con thành độc lập (SET NULL)
- **Status Flow**: `Pending → Processing → Partial → Shipped → Delivered` hoặc `Cancelled`
- **Routes**: `/orders/retail`, `/orders/wholesale`, `/orders/returns`

---

## 6. Quy trình Phê duyệt (Approval Workflow)

### UC4 - Phê duyệt giao dịch (Approve Transactions)

- **Kiểm soát cuối cùng** của Chủ cửa hàng đối với giao dịch nhạy cảm:
  - Phiếu nhập kho (StockReceipts)
  - Phiếu xuất kho (StockDispatches)
  - Giao dịch tài chính (FinanceLedger)
- **Nguyên tắc Human-in-the-Loop**:
  - AI/Staff tạo trạng thái `Draft/Pending`
  - Owner xem xét và **Confirm** manually
  - Dữ liệu kho/tài chính chỉ cập nhật sau khi **Approved**
- **Transaction Safety**:
  - Wrap trong DATABASE TRANSACTION
  - Rollback nếu có lỗi
  - Update Inventory + FinanceLedger + InventoryLogs + Notifications
- **Audit Trail**: `approved_by`, `approved_at` lưu vết người duyệt

---

## 7. Tích hợp AI & Tương tác Thông minh (Smart AI)

### UC11 - Trợ lý ảo AI Chat Bot

- **Hỗ trợ nhân viên** tra cứu nhanh:
  - Tồn kho: "Còn bao nhiêu sữa ông thọ?"
  - Thông tin sản phẩm: "Giá bán của SP001?"
  - Hướng dẫn nghiệp vụ: "Cách tạo phiếu nhập?"
- **Công nghệ**:
  - Web Speech API (Local STT - Speech to Text)
  - Gửi text đến AI Backend (DeepSeek)
  - Nhận dạng intent (ChatIntent JSON)
- **Lưu lịch sử chat** (AIChatHistory table) cho ngữ cảnh session
- **Tính năng rảnh tay** (Hands-free) qua giọng nói

### UC12 - Số hóa hóa đơn qua hình ảnh (OCR Invoice Scanning)

- **Công nghệ**: Azure Document Intelligence + LLM
- **Workflow**:
  1. Chụp ảnh hóa đơn giấy
  2. Nén ảnh (browser-image-compression)
  3. Upload lên Cloud (S3/Firebase)
  4. AI trích xuất dữ liệu: Nhà cung cấp, mặt hàng, số lượng, đơn giá
  5. Điền sẵn vào biểu mẫu nhập kho (Draft state)
  6. Staff/Owner xem xét và Confirm
- **Lưu vết media** (MediaAudits table): entityType + entityId (polymorphic)
- **Ứng dụng**: Tạo phiếu nhập kho nhanh từ hóa đơn giấy

### UC13 - Nhập liệu bằng giọng nói (Voice Commands)

- **Tính hands-free** hoàn toàn cho nhân viên kho
- **Ví dụ lệnh**:
  - "Nhập 50 thùng sữa vào kệ B1"
  - "Xuất 10 hộp bánh cho đơn SO-2026-0001"
  - "Kiểm tra tồn kho của SP001"
- **Workflow**:
  1. Web Speech API → Text
  2. AI phân tích intent (action, product, location, unit)
  3. Tạo Draft transaction
  4. User confirm → Commit to DB
- **Lưu vết**: MediaAudits (Voice_Audio) + AIChatHistory

---

## 8. Quản lý Tài chính (Cashflow & Finance)

### Finance Ledger (Sổ cái tài chính)

- **Theo dõi thu chi**:
  - SalesRevenue: Doanh thu bán hàng
  - PurchaseCost: Chi phí nhập hàng
  - OperatingExpense: Chi phí vận hành
  - Refund: Hoàn tiền
- **Polymorphic Reference**:
  - `reference_type` + `reference_id` → SalesOrder, StockReceipt, etc.
  - Liên kết chứng từ gốc
- **Nguyên tắc**:
  - Amount: Dương = thu, Âm = chi
  - Immutable sau khi ghi (không sửa)
  - Created by user (audit trail)
- **Routes**: `/cashflow/transactions`, `/cashflow/debt`

---

## 9. Hệ thống Thông báo & Nhật ký (Notifications & Logs)

### Notifications (Thông báo người dùng)

- **Loại thông báo**:
  - ApprovalResult: Kết quả phê duyệt
  - LowStock: Cảnh báo tồn kho thấp
  - ExpiryWarning: Hàng cận date
  - SystemAlert: Cảnh báo hệ thống
- **Trạng thái**: Unread/Read với timestamp
- **Link đến entity** liên quan (reference_type + reference_id)

### SystemLogs (Nhật ký hệ thống)

- **Theo dõi**:
  - Log level: INFO, WARNING, ERROR, CRITICAL
  - Module, action, user thực hiện
  - Message + Stack trace (cho errors)
  - Context data (JSON linh hoạt)
- **Performance**: Cân nhắc partitioning theo tháng hoặc archive sau 90 ngày

---

## 🏗️ Kiến trúc Frontend

### Feature Folders Pattern

```
src/features/
├── auth/              # Đăng nhập (Task001 ✅)
├── dashboard/         # Dashboard chính
├── inventory/         # Quản lý kho (Categories, Inbound, Audit)
├── orders/            # Đơn hàng (Retail, Wholesale, Returns)
├── cashflow/          # Tài chính (Transactions, Debt)
├── analytics/         # Phân tích (Revenue, Top Products)
└── settings/          # Cài đặt (Store Info, Employees)
```

### Layout System

- **MainLayout**: Sidebar + Header + Content Outlet
- **Sidebar** (Task002 ✅):
  - 5 nhóm menu collapsible (Inventory, Orders, Cashflow, Analytics, Settings)
  - Resizable (192px - 320px, default 256px)
  - Persistent state qua Zustand + localStorage
- **Header** (Task003 🔄):
  - Breadcrumb navigation
  - Notification bell
  - User profile (avatar, name)

### State Management

- **TanStack Query v5**: Server state, caching, optimistic updates
  - 5-minute staleTime, retry: 1, no refetch on focus
- **Zustand**: Client state (sidebar, UI)
  - `sidebarStore.ts`: Collapsible states + width
  - `useUIStore.ts`: UI preferences (persisted)
- **React Hook Form + Zod**: Form validation

### Design System

- **Tailwind CSS v4**: Utility-first
- **Shadcn UI**: 9 primitives (Button, Card, Input, Avatar, Badge, v.v.)
- **Lucide React**: Icons 18px
- **Typography**:
  - Inter: Base 14px, line-height 1.6
  - Public Sans: Headers/uppercase
- **Color Palette** (Slate Monochrome):
  - Primary: `#0f172a` (Slate 900)
  - Success: `#15803d` / light: `#dcfce7`
  - Alert: `#b91c1c` / light: `#fee2e2`
  - Surface: Whites, Slate 50-200

---

## 📊 Database Schema Summary

### 24 Tables Overview

| Group                            | Tables                                                                                                                       | Key Features                  |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| **Admin & Users** (4)            | Roles, Users, AlertSettings, SystemLogs                                                                                      | RBAC, audit trail             |
| **Partners & Finance** (3)       | Customers, Suppliers, FinanceLedger                                                                                          | Polymorphic references        |
| **Categories & Products** (5)    | Categories, Products, ProductImages, ProductUnits, ProductPriceHistory                                                       | Hierarchical, multi-UoM       |
| **Warehouse & Transactions** (8) | WarehouseLocations, Inventory, StockReceipts, StockReceiptDetails, SalesOrders, OrderDetails, StockDispatches, InventoryLogs | Full audit trail              |
| **AI & Media** (3)               | AIInsights, AIChatHistory, MediaAudits                                                                                       | Polymorphic, session tracking |
| **Optional** (1)                 | Notifications                                                                                                                | User alerts                   |

### Key Database Features

- **42+ Foreign Keys** với ON DELETE rules (CASCADE, RESTRICT, SET NULL)
- **42+ Indexes** optimized cho queries
- **18+ CHECK Constraints** cho data validation
- **3 Generated Columns** (auto-calculated: final_amount, line_total)
- **12 Triggers** cho auto-update timestamps
- **Polymorphic Relationships**: FinanceLedger, MediaAudits
- **Self-References**: Categories (tree), SalesOrders (backorders)

---

## 🎯 Core Business Pillars

1. **Inventory (Tồn kho)**
   - Real-time stock tracking
   - AI low-stock alerts
   - Multi-location (warehouse/shelf)
   - Picking lists for dispatch

2. **Orders (Đơn hàng)**
   - Inbound: OCR invoice scanning (UC12)
   - Outbound: Voice commands (UC13)
   - Backorder handling
   - Partial dispatch support

3. **Cashflow (Dòng tiền)**
   - Revenue/expense tracking
   - Debt management
   - Finance ledger (immutable records)

4. **Analytics (Phân tích)**
   - Visual dashboards
   - Profit/loss reports
   - Top products analysis

5. **AI Integration (Tích hợp AI)**
   - Voice-to-Action (Web Speech API → AI)
   - OCR-to-Data (Azure Document Intelligence)
   - Smart natural language querying
   - Human-in-the-Loop pattern

---

## ✅ Implementation Progress

### Completed Tasks

- [x] **Task001**: Login Interface ✅
  - Zod validation, password toggle, navigate to dashboard
  - Compliant with RULES.md (44px touch targets, monochrome palette)
- [x] **Task002**: Dashboard Sidebar ✅
  - 5 collapsible nav groups, resizable (192-320px)
  - Zustand store with persist middleware
  - Active route detection
- [x] **Database Documentation** ✅
  - Restructured into `docs/database/` folder
  - 24 table docs + schema + relationships + migrations

### In Progress

- 🔄 **Task003**: Dashboard Header
  - Breadcrumb, notification bell, user profile

### Planned Features

- [x] **Task043**: Mass Table Standardization & CRUD ✅
  - Standardized all tables to Master Table Pattern (no scroll, sticky headers).
  - Implemented Delete CRUD with confirmation dialogs across system.
  - Completed EmployeesPage, WarehouseLocationsPage, and SystemLogsPage.
- [ ] Dashboard KPIs (UC1)
- [ ] AI Chat Bot (UC11)
- [ ] OCR Invoice Scanning (UC12)
- [ ] Voice Commands (UC13)
- [x] Product Management CRUD (UC8) ✅
- [x] **Stock Receipt Workflow (UC7)** - Refactored UI ✅. Logic integration pending.
- [ ] Sales Order Management (UC9)
- [ ] Approval Workflow (UC4)
- [ ] Inventory Audit (UC6)
- [ ] Alert Settings (UC5)
- [x] Staff Management (UC3) ✅
- [ ] Finance Ledger
- [ ] Stock Dispatch (UC10)

---

## 🔐 Security & Best Practices

### Security

- Password hashing: bcrypt (cost ≥ 10) or argon2id
- NEVER store plaintext passwords
- Parameterized queries (prevent SQL injection)
- Transaction safety (BEGIN/COMMIT/ROLLBACK)

### Human-in-the-Loop Pattern

- AI/Staff tạo `Draft/Pending` states
- Owner review và **Confirm** manually
- KHÔNG có destructive actions tự động
- Full audit trail (InventoryLogs, SystemLogs, MediaAudits)

### Performance

- TanStack Query caching (5min staleTime)
- Optimistic updates cho mutations
- Image compression trước khi upload OCR
- Index strategy cho high-traffic queries

---

## 📚 Documentation Structure

```
frontend/
├── FUNCTIONAL_SUMMARY.md        # Tài liệu này (tổng quan chức năng)
├── Tech-Stack.md                # Công nghệ sử dụng
├── RULES.md                     # AI coding rules & design tokens
├── overall-project.md           # Tổng quan dự án
├── docs/
│   ├── database/                # Database documentation
│   │   ├── schema.md            # Schema overview
│   │   ├── relationships.md     # FK relationships
│   │   ├── migrations.md        # Indexes & migration guide
│   │   └── tables/              # Individual table docs
│   └── UC/                      # Use Case specifications
│       ├── Database_Specification.md
│       ├── Database_Specification_Part2.md
│       ├── Entity_Relationships.md
│       └── schema.sql           # Complete SQL schema
└── TASKS/
    ├── Task001.md               # Login (✅ Complete)
    ├── Task002.md               # Sidebar (✅ Complete)
    └── Task003.md               # Header (🔄 In Progress)
```

---

## 🚀 Next Steps

1. **Complete Task003**: Dashboard Header implementation
2. **Setup API Layer**: TanStack Query hooks + API client
3. **Implement Dashboard KPIs**: UC1 - Real-time metrics
4. **Build Product Management**: UC8 - CRUD operations
5. **Develop Stock Receipt Workflow**: UC7 - Draft → Approval flow
6. **Integrate AI Features**: UC11 (Chat), UC12 (OCR), UC13 (Voice)

---

_Ngày cập nhật: 18/04/2026_  
_Phiên bản: 2.1 - Updated with Mass Table Standardization (Task043) & CRUD completion_
