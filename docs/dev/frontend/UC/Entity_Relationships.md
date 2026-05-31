# Entity Relationships - Smart Inventory Management

## 📋 Thông tin

- **Mục đích**: Tài liệu phát triển ứng dụng (Frontend & Backend)
- **Ngôn ngữ**: TypeScript interfaces (dễ chuyển sang các ngôn ngữ khác)
- **Ngày tạo**: 11/04/2026

---

## 🎯 Entity Diagram tổng quan

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│   Role   │         │ Category │         │ Supplier │
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │ 1:N               │ 1:N                │ 1:N
     ▼                   ▼                    ▼
┌──────────────────────────────────────────────────────────┐
│                          User                            │
└────────┬─────────────────────────────────────┬───────────┘
         │ 1:N                                 │ 1:N
         ▼                                     ▼
┌─────────────────────┐              ┌─────────────────────┐
│  AlertSetting       │              │     Product         │
│  SystemLog          │              └────────┬────────────┘
│  FinanceLedger      │                       │ 1:N
│  AIInsight          │           ┌───────────┼──────────────┐
│  AIChatHistory      │           ▼           ▼              ▼
│  Notification       │    ProductImage  ProductUnit   PriceHistory
│  StockReceipt       │                       ▼
│  SalesOrder         │                  Inventory
│  StockDispatch      │              (WarehouseLocation)
│  InventoryLog       │
│  MediaAudit         │
└─────────────────────┘

┌──────────┐
│ Customer │
└────┬─────┘
     │ 1:N
     ▼
┌─────────────────────┐
│   SalesOrder        │◄──── self-ref (parentOrderId: Backorder)
└────────┬────────────┘
         │ 1:N
         ▼
┌─────────────────────┐         ┌─────────────────┐
│   OrderDetail       │         │ StockDispatch   │
└─────────────────────┘         └────────┬────────┘
                                         │ 1:N
                                         ▼
                                  ┌─────────────────┐
                                  │ InventoryLog    │
                                  └─────────────────┘
```

---

## 📚 Entity Definitions

### 1. Role

```typescript
interface Role {
  id: number;
  name: "Owner" | "Staff" | "Admin";
  permissions: RolePermissions;
  createdAt: Date;
}

interface RolePermissions {
  can_view_dashboard: boolean;
  can_manage_staff: boolean;
  can_approve: boolean;
  can_configure_alerts: boolean;
  can_view_finance: boolean;
  can_manage_products: boolean;
  can_manage_inventory: boolean;
  can_manage_orders: boolean;
  can_use_ai: boolean;
}
```

**Quan hệ:**

- `Role 1 → N User` (role.users)

---

### 2. User

```typescript
interface User {
  id: number;
  username: string;
  passwordHash: string; // KHÔNG trả về frontend
  fullName: string;
  email: string;
  phone?: string;
  roleId: number; // FK → Role
  status: "Active" | "Locked";
  lastLogin?: Date;
  createdAt: Date;
  updatedAt: Date;

  // Relations (loaded when needed)
  role?: Role;
  alertSettings?: AlertSetting[];
  createdReceipts?: StockReceipt[];
  approvedReceipts?: StockReceipt[];
  createdOrders?: SalesOrder[];
  dispatchedOrders?: StockDispatch[];
}
```

**Quan hệ:**

- `User N → 1 Role` (user.role)
- `User 1 → N AlertSetting`
- `User 1 → N StockReceipt` (as staff)
- `User 1 → N StockReceipt` (as approver)
- `User 1 → N SalesOrder` (as creator)
- `User 1 → N SalesOrder` (as canceller)
- `User 1 → N StockDispatch`
- `User 1 → N InventoryLog`
- `User 1 → N FinanceLedger`
- `User 1 → N AIInsight`
- `User 1 → N AIChatHistory`
- `User 1 → N MediaAudit`
- `User 1 → N Notification`
- `User 1 → N SystemLog`

---

### 3. Customer

```typescript
interface Customer {
  id: number;
  customerCode: string; // KH00001
  name: string;
  phone: string;
  email?: string;
  address?: string;
  loyaltyPoints: number;
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Computed (không lưu trong DB)
  totalSpent?: number; // SUM(SalesOrder.totalAmount)
  orderCount?: number;

  // Relations
  orders?: SalesOrder[];
}
```

**Quan hệ:**

- `Customer 1 → N SalesOrder` (customer.orders)

---

### 4. Supplier

```typescript
interface Supplier {
  id: number;
  supplierCode: string; // NCC0001
  name: string;
  contactPerson?: string;
  phone?: string;
  email?: string;
  address?: string;
  taxCode?: string;
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Relations
  receipts?: StockReceipt[];
}
```

**Quan hệ:**

- `Supplier 1 → N StockReceipt` (supplier.receipts)

---

### 5. Category

```typescript
interface Category {
  id: number;
  categoryCode: string; // CAT001
  name: string;
  description?: string;
  parentId?: number; // FK → Category (self-reference)
  sortOrder: number;
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Relations
  parent?: Category;
  children?: Category[];
  products?: Product[];
}
```

**Quan hệ:**

- `Category 1 → N Category` (self-reference: parent/children)
- `Category 1 → N Product` (category.products)

---

### 6. Product

```typescript
interface Product {
  id: number;
  categoryId?: number; // FK → Category
  skuCode: string; // unique
  barcode?: string;
  name: string;
  imageUrl?: string; // Legacy URL (ảnh đại diện cũ)
  description?: string;
  weight?: number; // grams
  status: "Active" | "Inactive";
  createdAt: Date;
  updatedAt: Date;

  // Relations
  category?: Category;
  images?: ProductImage[]; // Nhiều ảnh sản phẩm
  units?: ProductUnit[];
  priceHistory?: ProductPriceHistory[];
  inventories?: Inventory[];

  // Computed
  currentStock?: number; // SUM(Inventory.quantity)
  primaryImage?: ProductImage;
  currentPrice?: ProductPriceHistory;
}
```

**Quan hệ:**

- `Product N → 1 Category` (product.category)
- `Product 1 → N ProductImage` (product.images)
- `Product 1 → N ProductUnit` (product.units)
- `Product 1 → N ProductPriceHistory`
- `Product 1 → N Inventory`
- `Product 1 → N StockReceiptDetail`
- `Product 1 → N OrderDetail`
- `Product 1 → N InventoryLog`

---

### 7. ProductImage

```typescript
interface ProductImage {
  id: number;
  productId: number; // FK → Product
  imageUrl: string; // URL ảnh trên Cloud
  altText?: string; // Mô tả ảnh cho SEO
  isPrimary: boolean; // Ảnh đại diện (chỉ 1 TRUE/product)
  sortOrder: number; // Thứ tự hiển thị
  fileSizeBytes?: number; // Kích thước file
  mimeType?: string; // image/jpeg, image/png
  createdAt: Date;

  // Relations
  product?: Product;
}
```

**Quan hệ:**

- `ProductImage N → 1 Product`

**Business Rules:**

1. Mỗi product có thể có nhiều ảnh
2. Chỉ có ĐÚNG 1 ảnh với `isPrimary = true`
3. `sortOrder` dùng để sắp xếp khi hiển thị
4. URL ảnh lưu trên Cloud (S3, Firebase, etc.)

---

### 8. ProductUnit

```typescript
interface ProductUnit {
  id: number;
  productId: number; // FK → Product
  unitName: string; // Thùng, Hộp, Cái
  conversionRate: number; // > 0
  isBaseUnit: boolean; // ĐÚNG 1 per product
  createdAt: Date;
  updatedAt: Date;

  // Relations
  product?: Product;
}
```

**Quan hệ:**

- `ProductUnit N → 1 Product`
- `ProductUnit 1 → N ProductPriceHistory`
- `ProductUnit 1 → N StockReceiptDetail`
- `ProductUnit 1 → N OrderDetail`
- `ProductUnit 1 → N InventoryLog`

---

### 9. ProductPriceHistory

```typescript
interface ProductPriceHistory {
  id: number;
  productId: number; // FK → Product
  unitId: number; // FK → ProductUnit
  costPrice: number; // giá vốn
  salePrice: number; // giá bán
  effectiveDate: Date; // ngày áp dụng
  createdAt: Date;

  // Relations
  product?: Product;
  unit?: ProductUnit;
}
```

**Quan hệ:**

- `ProductPriceHistory N → 1 Product`
- `ProductPriceHistory N → 1 ProductUnit`

---

### 10. WarehouseLocation

```typescript
interface WarehouseLocation {
  id: number;
  warehouseCode: string; // WH01
  shelfCode: string; // A1, B2
  description?: string;
  capacity?: number; // m³
  status: "Active" | "Maintenance" | "Inactive";
  createdAt: Date;

  // Relations
  inventories?: Inventory[];
}
```

**Quan hệ:**

- `WarehouseLocation 1 → N Inventory`
- `WarehouseLocation 1 → N InventoryLog` (from/to)

---

### 11. Inventory

```typescript
interface Inventory {
  id: number;
  productId: number; // FK → Product
  locationId: number; // FK → WarehouseLocation
  batchNumber?: string;
  expiryDate?: Date;
  quantity: number; // theo đơn vị cơ sở, >= 0
  minQuantity: number; // ngưỡng cảnh báo
  updatedAt: Date;

  // Computed
  isLowStock?: boolean; // quantity <= minQuantity
  isExpiringSoon?: boolean; // expiryDate <= now + 30 days

  // Relations
  product?: Product;
  location?: WarehouseLocation;
}
```

**Quan hệ:**

- `Inventory N → 1 Product`
- `Inventory N → 1 WarehouseLocation`
- UNIQUE: (productId, locationId, batchNumber)

---

### 12. StockReceipt (Phiếu Nhập kho)

```typescript
interface StockReceipt {
  id: number;
  receiptCode: string; // PN-2026-0001
  supplierId: number; // FK → Supplier
  staffId: number; // FK → User
  receiptDate: Date;
  status: "Draft" | "Pending" | "Approved" | "Rejected";
  invoiceNumber?: string;
  totalAmount: number;
  notes?: string;
  approvedBy?: number; // FK → User
  approvedAt?: Date;
  createdAt: Date;
  updatedAt: Date;

  // Relations
  supplier?: Supplier;
  staff?: User;
  approver?: User;
  details?: StockReceiptDetail[];
  mediaAudits?: MediaAudit[];
}
```

**Quan hệ:**

- `StockReceipt N → 1 Supplier`
- `StockReceipt N → 1 User` (staff)
- `StockReceipt N → 1 User` (approver)
- `StockReceipt 1 → N StockReceiptDetail`
- `StockReceipt 1 → N InventoryLog`
- `StockReceipt 1 → N MediaAudit`

---

### 13. StockReceiptDetail

```typescript
interface StockReceiptDetail {
  id: number;
  receiptId: number; // FK → StockReceipt
  productId: number; // FK → Product
  unitId: number; // FK → ProductUnit
  quantity: number;
  costPrice: number;
  batchNumber?: string;
  expiryDate?: Date;
  lineTotal: number; // auto: quantity * costPrice
  createdAt: Date;

  // Relations
  receipt?: StockReceipt;
  product?: Product;
  unit?: ProductUnit;
}
```

**Quan hệ:**

- `StockReceiptDetail N → 1 StockReceipt`
- `StockReceiptDetail N → 1 Product`
- `StockReceiptDetail N → 1 ProductUnit`

---

### 14. SalesOrder (Đơn hàng bán)

```typescript
interface SalesOrder {
  id: number;
  orderCode: string; // SO-2026-0001
  customerId: number; // FK → Customer
  userId: number; // FK → User
  totalAmount: number;
  discountAmount: number;
  finalAmount: number; // auto: totalAmount - discountAmount
  status:
    | "Pending"
    | "Processing"
    | "Partial"
    | "Shipped"
    | "Delivered"
    | "Cancelled";
  parentOrderId?: number; // FK → SalesOrder (Backorder)
  shippingAddress?: string;
  notes?: string;

  createdAt: Date;
  updatedAt: Date;
  cancelledAt?: Date;
  cancelledBy?: number; // FK → User

  // Relations
  customer?: Customer;
  user?: User;
  canceller?: User;
  details?: OrderDetail[];
  dispatches?: StockDispatch[];
  childOrders?: SalesOrder[]; // backorders
  parentOrder?: SalesOrder; // if this is backorder
}
```

**Quan hệ:**

- `SalesOrder N → 1 Customer`
- `SalesOrder N → 1 User` (creator)
- `SalesOrder N → 1 User` (canceller)
- `SalesOrder N → 1 SalesOrder` (parent - backorder)
- `SalesOrder 1 → N OrderDetail`
- `SalesOrder 1 → N StockDispatch`
- `SalesOrder 1 → N SalesOrder` (children - backorders)

---

### 15. OrderDetail

```typescript
interface OrderDetail {
  id: number;
  orderId: number; // FK → SalesOrder
  productId: number; // FK → Product
  unitId: number; // FK → ProductUnit
  quantity: number;
  priceAtTime: number; // giá tại thời điểm đặt
  lineTotal: number; // auto: quantity * priceAtTime
  dispatchedQty: number; // đã xuất kho
  createdAt: Date;

  // Computed
  remainingQty?: number; // quantity - dispatchedQty
  isFullyDispatched?: boolean; // dispatchedQty == quantity

  // Relations
  order?: SalesOrder;
  product?: Product;
  unit?: ProductUnit;
}
```

**Quan hệ:**

- `OrderDetail N → 1 SalesOrder`
- `OrderDetail N → 1 Product`
- `OrderDetail N → 1 ProductUnit`

---

### 16. StockDispatch (Phiếu Xuất kho)

```typescript
interface StockDispatch {
  id: number;
  dispatchCode: string; // PX-2026-0001
  orderId: number; // FK → SalesOrder
  userId: number; // FK → User
  dispatchDate: Date;
  status: "Pending" | "Full" | "Partial" | "Cancelled";
  notes?: string;
  createdAt: Date;
  updatedAt: Date;

  // Relations
  order?: SalesOrder;
  user?: User;
  logs?: InventoryLog[];
}
```

**Quan hệ:**

- `StockDispatch N → 1 SalesOrder`
- `StockDispatch N → 1 User`
- `StockDispatch 1 → N InventoryLog`

---

### 17. InventoryLog

```typescript
interface InventoryLog {
  id: number;
  productId: number; // FK → Product
  actionType: "INBOUND" | "OUTBOUND" | "TRANSFER" | "ADJUSTMENT";
  quantityChange: number; // + nhập, - xuất
  unitId: number; // FK → ProductUnit
  userId?: number; // FK → User
  dispatchId?: number; // FK → StockDispatch
  receiptId?: number; // FK → StockReceipt
  fromLocationId?: number; // FK → WarehouseLocation
  toLocationId?: number; // FK → WarehouseLocation
  referenceNote?: string;
  createdAt: Date;

  // Relations
  product?: Product;
  unit?: ProductUnit;
  user?: User;
  dispatch?: StockDispatch;
  receipt?: StockReceipt;
  fromLocation?: WarehouseLocation;
  toLocation?: WarehouseLocation;
}
```

**Quan hệ:**

- `InventoryLog N → 1 Product`
- `InventoryLog N → 1 ProductUnit`
- `InventoryLog N → 1 User`
- `InventoryLog N → 1 StockDispatch` (optional)
- `InventoryLog N → 1 StockReceipt` (optional)
- `InventoryLog N → 1 WarehouseLocation` (from)
- `InventoryLog N → 1 WarehouseLocation` (to)

---

### 18. AlertSetting

```typescript
interface AlertSetting {
  id: number;
  ownerId: number; // FK → User
  alertType:
    | "LowStock"
    | "ExpiryDate"
    | "HighValueTransaction"
    | "PendingApproval";
  thresholdValue?: number;
  channel: "App" | "Email" | "SMS" | "Zalo";
  frequency: "Realtime" | "Daily" | "Weekly";
  isEnabled: boolean;
  recipients?: string[]; // user IDs
  createdAt: Date;
  updatedAt: Date;

  // Relations
  owner?: User;
}
```

**Quan hệ:**

- `AlertSetting N → 1 User`

---

### 19. SystemLog

```typescript
interface SystemLog {
  id: number;
  logLevel: "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  module: string;
  action: string;
  userId?: number; // FK → User
  message: string;
  stackTrace?: string;
  contextData?: Record<string, any>;
  createdAt: Date;

  // Relations
  user?: User;
}
```

**Quan hệ:**

- `SystemLog N → 1 User`

---

### 20. FinanceLedger

```typescript
interface FinanceLedger {
  id: number;
  transactionDate: Date;
  transactionType:
    | "SalesRevenue"
    | "PurchaseCost"
    | "OperatingExpense"
    | "Refund";
  referenceType?: string; // 'SalesOrder', 'StockReceipt'
  referenceId?: number; // ID của chứng từ
  amount: number; // + thu, - chi
  description?: string;
  createdBy: number; // FK → User
  createdAt: Date;
  updatedAt: Date;

  // Relations
  creator?: User;
}
```

**Quan hệ:**

- `FinanceLedger N → 1 User`
- Polymorphic: referenceType + referenceId → SalesOrder/StockReceipt

---

### 21. AIInsight

```typescript
interface AIInsight {
  id: number;
  ownerId: number; // FK → User
  dashboardSnapshot: DashboardData;
  prompt: string;
  aiAdvice: string; // Markdown
  modelUsed?: string;
  tokensUsed?: number;
  createdAt: Date;

  // Relations
  owner?: User;
}

interface DashboardData {
  dateRange: string;
  totalRevenue: number;
  totalExpenses: number;
  inventoryValue: number;
  lowStockItems: number;
  expiringSoon: number;
  topProducts: string[];
}
```

**Quan hệ:**

- `AIInsight N → 1 User`

---

### 22. AIChatHistory

```typescript
interface AIChatHistory {
  id: number;
  userId: number; // FK → User
  sessionId?: string;
  message: string;
  sender: "User" | "Bot";
  intent?: ChatIntent;
  responseTimeMs?: number;
  createdAt: Date;

  // Relations
  user?: User;
}

interface ChatIntent {
  action: string; // 'check_stock', 'create_order', etc.
  product?: string;
  location?: string;
  unit?: string;
  [key: string]: any;
}
```

**Quan hệ:**

- `AIChatHistory N → 1 User`

---

### 23. MediaAudit

```typescript
interface MediaAudit {
  id: number;
  fileType: "OCR_Image" | "Voice_Audio";
  cloudUrl: string;
  entityType: string; // 'StockReceipt', 'SalesOrder', 'Inventory'
  entityId: number;
  fileSizeBytes?: number;
  mimeType?: string;
  uploadedBy?: number; // FK → User
  createdAt: Date;

  // Relations
  uploader?: User;
}
```

**Quan hệ:**

- `MediaAudit N → 1 User`
- Polymorphic: entityType + entityId → various entities

---

### 24. Notification

```typescript
interface Notification {
  id: number;
  userId: number; // FK → User
  notificationType:
    | "ApprovalResult"
    | "LowStock"
    | "ExpiryWarning"
    | "SystemAlert";
  title: string;
  message: string;
  isRead: boolean;
  referenceType?: string;
  referenceId?: number;
  createdAt: Date;
  readAt?: Date;

  // Relations
  user?: User;
}
```

**Quan hệ:**

- `Notification N → 1 User`

---

## 🔗 Relationship Summary

### Core Relationships

```
Role ──────────────── 1:N ──→ User
                        │
Category ───────────── 1:N ──→ Product
                        │
Supplier ───────────── 1:N ──→ StockReceipt ─── 1:N ──→ StockReceiptDetail
                        │           │
Customer ───────────── 1:N ──→ SalesOrder ──── 1:N ──→ OrderDetail
                        │           │
WarehouseLocation ──── 1:N ──→ Inventory
```

### Self-References

```
Category:     parent ← children (hierarchical tree)
SalesOrder:   parentOrder ← childOrders (backorders)
```

### Polymorphic Relationships

```
FinanceLedger:  referenceType + referenceId → SalesOrder | StockReceipt | ...
MediaAudit:     entityType + entityId → StockReceipt | SalesOrder | Inventory
```

---

## 📦 DTO Examples for API

### GET /api/products/:id Response

```json
{
  "id": 1,
  "skuCode": "SP001",
  "name": "Sữa ông Thọ",
  "units": [
    { "id": 1, "unitName": "Cái", "conversionRate": 1, "isBaseUnit": true },
    { "id": 2, "unitName": "Hộp", "conversionRate": 12, "isBaseUnit": false },
    { "id": 3, "unitName": "Thùng", "conversionRate": 120, "isBaseUnit": false }
  ],
  "currentStock": 1200,
  "currentPrice": {
    "costPrice": 25000,
    "salePrice": 35000,
    "effectiveDate": "2026-04-01"
  }
}
```

### POST /api/sales-orders Request

```json
{
  "customerId": 5,
  "items": [
    {
      "productId": 1,
      "unitId": 2,
      "quantity": 10,
      "priceAtTime": 35000
    }
  ],
  "discountAmount": 50000,
  "shippingAddress": "123 Đường ABC, Quận 1, TP.HCM"
}
```

---

## 🎯 Use Cases cho Developers

### 1. Fetch Product với tồn kho

```typescript
async function getProductWithStock(productId: number): Promise<
  Product & {
    currentStock: number;
    locations: Inventory[];
  }
> {
  // JOIN Product với Inventory
  // GROUP BY product_id, SUM(quantity)
}
```

### 2. Create SalesOrder với Backorder logic

```typescript
async function createSalesOrder(order: CreateOrderDto): Promise<SalesOrder> {
  // 1. Create SalesOrder
  // 2. Create OrderDetails
  // 3. Check stock availability
  // 4. If partial → create StockDispatch with status = 'Partial'
  // 5. Create child SalesOrder (backorder) với parentOrderId
}
```

### 3. Approve StockReceipt workflow

```typescript
async function approveReceipt(
  receiptId: number,
  approverId: number,
): Promise<void> {
  // 1. UPDATE StockReceipt SET status='Approved', approvedBy=?, approvedAt=NOW()
  // 2. FOR EACH detail: UPDATE Inventory SET quantity += detail.quantity
  // 3. INSERT FinanceLedger (PurchaseCost)
  // 4. INSERT InventoryLog (INBOUND)
  // 5. INSERT Notification cho staff
  // Wrap trong TRANSACTION → rollback nếu lỗi
}
```

---

## ✅ Checklist cho Development

- [ ] Định nghĩa tất cả interfaces trong TypeScript
- [ ] Tạo DTOs cho request/response
- [ ] Implement validation schemas (Zod/Joi)
- [ ] Tạo database models (Prisma/TypeORM/Sequelize)
- [ ] Implement repositories/services
- [ ] Viết unit tests cho từng entity
- [ ] Test relationships (JOIN queries)
- [ ] Test constraints (UNIQUE, CHECK, FK)

---

**Tài liệu này dùng làm reference cho việc phát triển ứng dụng.**  
**Có thể dùng để sinh code tự động với các tools như Prisma, GraphQL codegen, etc.**
