export type MockHttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE"
export type MockResponseKind = "json" | "multipart" | "sse"

export type MockSuccessEnvelope<T> = {
  success: true
  data: T
}

export type MockErrorEnvelope = {
  success: false
  error: string
  message: string
  details?: Record<string, string>
}

export type MockListPage<T> = {
  items: T[]
  page: number
  limit: number
  total: number
  totalPages: number
}

export type MockCatalogEntry = {
  method: MockHttpMethod
  path: string
  auth: boolean
  kind: MockResponseKind
  permission?: string | string[]
  description: string
  sampleData: unknown
}

export function mockSuccess<T>(data: T): MockSuccessEnvelope<T> {
  return { success: true, data }
}

export function mockError(
  error: string,
  message: string,
  details?: Record<string, string>,
): MockErrorEnvelope {
  return details ? { success: false, error, message, details } : { success: false, error, message }
}

export function mockList<T>(items: T[], page = 1, limit = 20): MockListPage<T> {
  return {
    items,
    page,
    limit,
    total: items.length,
    totalPages: Math.max(1, Math.ceil(items.length / limit)),
  }
}

const ownerPermissions = [
  "can_view_dashboard",
  "can_manage_inventory",
  "can_manage_products",
  "can_manage_customers",
  "can_manage_orders",
  "can_manage_staff",
  "can_configure_alerts",
  "can_view_finance",
  "can_approve",
  "can_use_ai",
]

const user = {
  id: 1,
  username: "owner",
  fullName: "Chu cua hang",
  email: "owner@example.com",
  role: "Owner",
  permissions: ownerPermissions,
}

const notification = {
  id: 1,
  type: "Inventory",
  title: "Sap het hang",
  message: "Sua tuoi SKU-MILK-01 sap cham nguong toi thieu.",
  read: false,
  createdAt: "2026-05-31T08:00:00Z",
  entityType: "Inventory",
  entityId: 101,
}

const inventoryItem = {
  id: 101,
  productId: 501,
  skuCode: "SKU-MILK-01",
  productName: "Sua tuoi",
  warehouseCode: "WH-A",
  shelfCode: "A01",
  location: "WH-A-A01",
  quantity: 42,
  unitName: "hop",
  unit: "hop",
  expiryDate: "2026-08-31",
  status: "in-stock",
  updatedAt: "2026-05-31T08:00:00Z",
}

const receipt = {
  id: 201,
  receiptCode: "PNK-0001",
  supplierName: "Cong ty Thuc pham A",
  receiptDate: "2026-05-30",
  staffName: "Nguyenx Chi Dat",
  invoiceNumber: "INV-1001",
  lineCount: 1,
  totalAmount: 1250000,
  status: "Draft",
  details: [{ productName: "Sua tuoi", quantity: 50, unitName: "hop", costPrice: 25000 }],
}

const dispatch = {
  id: 301,
  dispatchCode: "PXK-0001",
  orderCode: "DH-0001",
  customerName: "Khach le",
  dispatchDate: "2026-05-31",
  userName: "Nguyenx Chi Dat",
  itemCount: 1,
  lineCount: 1,
  status: "WaitingDispatch",
  lines: [{ productName: "Sua tuoi", quantity: 2, unitName: "hop" }],
}

const category = {
  id: 1,
  categoryCode: "CAT-FOOD",
  name: "Thuc pham",
  categoryName: "Thuc pham",
  productCount: 12,
  status: "Active",
}

const product = {
  id: 501,
  skuCode: "SKU-MILK-01",
  name: "Sua tuoi",
  productName: "Sua tuoi",
  categoryName: "Thuc pham",
  unitName: "hop",
  sellingPrice: 32000,
  stockQuantity: 42,
  status: "Active",
  imageUrl: "https://example.com/product.png",
}

const supplier = {
  id: 1,
  code: "NCC-001",
  name: "Cong ty Thuc pham A",
  phone: "0900000001",
  email: "supplier@example.com",
  status: "Active",
  createdAt: "2026-05-01T00:00:00Z",
}

const customer = {
  id: 1,
  code: "KH-001",
  name: "Khach le",
  phone: "0900000002",
  email: "customer@example.com",
  status: "Active",
  createdAt: "2026-05-01T00:00:00Z",
}

const order = {
  id: 401,
  orderCode: "DH-0001",
  customerName: "Khach le",
  orderDate: "2026-05-31",
  createdAt: "2026-05-31T08:00:00Z",
  channel: "Retail",
  status: "Completed",
  totalAmount: 64000,
  finalAmount: 64000,
  paymentStatus: "Paid",
  items: [{ productName: "Sua tuoi", quantity: 2, unitPrice: 32000 }],
}

const cashTransaction = {
  id: 701,
  transactionCode: "PT-0001",
  type: "Income",
  fundName: "Tien mat",
  amount: 64000,
  description: "Thu tien ban hang",
  transactionDate: "2026-05-31",
  createdByName: "Nguyenx Chi Dat",
}

const tableColumnSettings = {
  items: [
    {
      tableKey: "inventory_stock",
      tableLabel: "Ton kho",
      columns: [
        { key: "skuCode", label: "Ma SP", required: true, visible: true, order: 0 },
        { key: "productName", label: "Ten san pham", required: true, visible: true, order: 1 },
        { key: "location", label: "Vi tri", required: false, visible: true, order: 2 },
      ],
      updatedAt: "2026-05-31T10:20:30Z",
      updatedByName: "Chu cua hang",
    },
  ],
}

const catalogDraft = {
  draftId: "catalog-draft-1",
  status: "Draft",
  columns: [
    { key: "skuCode", label: "Ma SP", required: true },
    { key: "productName", label: "Ten san pham", required: true },
  ],
  rows: [{ rowId: "row-1", values: { skuCode: "SKU-MILK-01", productName: "Sua tuoi" } }],
}

const inventoryDraft = {
  draftId: "inventory-draft-1",
  status: "Draft",
  rows: [{ rowId: "row-1", values: { skuCode: "SKU-MILK-01", quantity: 10 } }],
}

export const frontendApiMockCatalog: MockCatalogEntry[] = [
  { method: "POST", path: "/api/v1/auth/login", auth: false, kind: "json", description: "Dang nhap", sampleData: { accessToken: "mock-access-token", refreshToken: "mock-refresh-token", user, permissions: ownerPermissions } },
  { method: "POST", path: "/api/v1/auth/refresh", auth: false, kind: "json", description: "Lam moi access token", sampleData: { accessToken: "mock-access-token" } },
  { method: "POST", path: "/api/v1/auth/logout", auth: true, kind: "json", description: "Dang xuat", sampleData: {} },
  { method: "POST", path: "/api/v1/auth/password-reset-requests", auth: false, kind: "json", description: "Yeu cau reset mat khau", sampleData: {} },

  { method: "GET", path: "/api/v1/notifications", auth: true, kind: "json", description: "Danh sach thong bao", sampleData: { ...mockList([notification]), unreadCount: 1 } },
  { method: "PATCH", path: "/api/v1/notifications/{id}", auth: true, kind: "json", description: "Danh dau thong bao da doc", sampleData: { ...notification, read: true } },
  { method: "POST", path: "/api/v1/notifications/mark-all-read", auth: true, kind: "json", description: "Danh dau tat ca thong bao da doc", sampleData: {} },

  { method: "GET", path: "/api/v1/inventory/summary", auth: true, kind: "json", permission: "can_manage_inventory", description: "KPI ton kho", sampleData: { totalSku: 1, totalValue: 1050000, lowStockCount: 0, outOfStockCount: 0, expiringSoonCount: 0 } },
  { method: "GET", path: "/api/v1/inventory", auth: true, kind: "json", permission: "can_manage_inventory", description: "Danh sach ton kho", sampleData: mockList([inventoryItem]) },
  { method: "GET", path: "/api/v1/inventory/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Chi tiet ton kho", sampleData: { ...inventoryItem, relatedLines: [] } },
  { method: "PATCH", path: "/api/v1/inventory/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cap nhat ton kho", sampleData: inventoryItem },
  { method: "PATCH", path: "/api/v1/inventory/bulk", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cap nhat ton kho hang loat", sampleData: { updatedCount: 1, items: [inventoryItem] } },

  { method: "GET", path: "/api/v1/stock-receipts", auth: true, kind: "json", permission: "can_manage_inventory", description: "Danh sach phieu nhap", sampleData: mockList([receipt]) },
  { method: "POST", path: "/api/v1/stock-receipts", auth: true, kind: "json", permission: "can_manage_inventory", description: "Tao phieu nhap", sampleData: receipt },
  { method: "GET", path: "/api/v1/stock-receipts/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Chi tiet phieu nhap", sampleData: receipt },
  { method: "PATCH", path: "/api/v1/stock-receipts/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cap nhat phieu nhap", sampleData: receipt },
  { method: "DELETE", path: "/api/v1/stock-receipts/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Xoa phieu nhap", sampleData: null },
  { method: "POST", path: "/api/v1/stock-receipts/{id}/submit", auth: true, kind: "json", permission: "can_manage_inventory", description: "Gui duyet phieu nhap", sampleData: { ...receipt, status: "Pending" } },
  { method: "POST", path: "/api/v1/stock-receipts/{id}/approve", auth: true, kind: "json", permission: "can_approve", description: "Duyet phieu nhap", sampleData: { ...receipt, status: "Approved" } },
  { method: "POST", path: "/api/v1/stock-receipts/{id}/reject", auth: true, kind: "json", permission: "can_approve", description: "Tu choi phieu nhap", sampleData: { ...receipt, status: "Rejected" } },

  { method: "GET", path: "/api/v1/stock-dispatches", auth: true, kind: "json", permission: "can_manage_inventory", description: "Danh sach phieu xuat", sampleData: mockList([dispatch]) },
  { method: "POST", path: "/api/v1/stock-dispatches", auth: true, kind: "json", permission: "can_manage_inventory", description: "Tao phieu xuat", sampleData: dispatch },
  { method: "POST", path: "/api/v1/stock-dispatches/from-order", auth: true, kind: "json", permission: "can_manage_inventory", description: "Tao phieu xuat tu don hang", sampleData: dispatch },
  { method: "GET", path: "/api/v1/stock-dispatches/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Chi tiet phieu xuat", sampleData: dispatch },
  { method: "PATCH", path: "/api/v1/stock-dispatches/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cap nhat phieu xuat", sampleData: dispatch },
  { method: "POST", path: "/api/v1/stock-dispatches/{id}/approve", auth: true, kind: "json", permission: "can_manage_inventory", description: "Duyet phieu xuat", sampleData: { ...dispatch, status: "WaitingDispatch" } },
  { method: "POST", path: "/api/v1/stock-dispatches/{id}/soft-delete", auth: true, kind: "json", permission: "can_manage_inventory", description: "Xoa mem phieu xuat", sampleData: {} },

  { method: "GET", path: "/api/v1/inventory/audit-sessions", auth: true, kind: "json", permission: "can_manage_inventory", description: "Danh sach kiem ke", sampleData: mockList([{ id: 1, auditCode: "KK-0001", title: "Kiem ke thang 5", status: "Draft" }]) },
  { method: "POST", path: "/api/v1/inventory/audit-sessions", auth: true, kind: "json", permission: "can_manage_inventory", description: "Tao phien kiem ke", sampleData: { id: 1, auditCode: "KK-0001", status: "Draft" } },
  { method: "GET", path: "/api/v1/inventory/audit-sessions/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Chi tiet kiem ke", sampleData: { id: 1, auditCode: "KK-0001", lines: [] } },
  { method: "PATCH", path: "/api/v1/inventory/audit-sessions/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cap nhat phien kiem ke", sampleData: { id: 1, auditCode: "KK-0001", status: "In Progress" } },
  { method: "PATCH", path: "/api/v1/inventory/audit-sessions/{id}/lines", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cap nhat dong kiem ke", sampleData: { id: 1, auditCode: "KK-0001", lines: [] } },
  { method: "POST", path: "/api/v1/inventory/audit-sessions/{id}/complete", auth: true, kind: "json", permission: "can_manage_inventory", description: "Hoan tat kiem ke", sampleData: { id: 1, status: "Completed" } },
  { method: "POST", path: "/api/v1/inventory/audit-sessions/{id}/approve", auth: true, kind: "json", permission: "can_manage_inventory", description: "Duyet kiem ke", sampleData: { id: 1, status: "Approved" } },
  { method: "POST", path: "/api/v1/inventory/audit-sessions/{id}/reject", auth: true, kind: "json", permission: "can_manage_inventory", description: "Tu choi kiem ke", sampleData: { id: 1, status: "Rejected" } },
  { method: "POST", path: "/api/v1/inventory/audit-sessions/{id}/cancel", auth: true, kind: "json", permission: "can_manage_inventory", description: "Huy kiem ke", sampleData: { id: 1, status: "Cancelled" } },
  { method: "DELETE", path: "/api/v1/inventory/audit-sessions/{id}", auth: true, kind: "json", permission: "can_manage_inventory", description: "Xoa kiem ke", sampleData: null },

  { method: "GET", path: "/api/v1/categories", auth: true, kind: "json", permission: "can_manage_products", description: "Danh sach danh muc", sampleData: { items: [category] } },
  { method: "GET", path: "/api/v1/categories/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Chi tiet danh muc", sampleData: category },
  { method: "POST", path: "/api/v1/categories", auth: true, kind: "json", permission: "can_manage_products", description: "Tao danh muc", sampleData: category },
  { method: "PATCH", path: "/api/v1/categories/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Cap nhat danh muc", sampleData: category },
  { method: "DELETE", path: "/api/v1/categories/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Xoa danh muc", sampleData: { deleted: true } },
  { method: "GET", path: "/api/v1/products", auth: true, kind: "json", permission: "can_manage_products", description: "Danh sach san pham", sampleData: mockList([product]) },
  { method: "POST", path: "/api/v1/products", auth: true, kind: "multipart", permission: "can_manage_products", description: "Tao san pham", sampleData: product },
  { method: "GET", path: "/api/v1/products/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Chi tiet san pham", sampleData: { ...product, units: [], images: [] } },
  { method: "PATCH", path: "/api/v1/products/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Cap nhat san pham", sampleData: product },
  { method: "DELETE", path: "/api/v1/products/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Xoa san pham", sampleData: { deleted: true } },
  { method: "POST", path: "/api/v1/products/bulk-delete", auth: true, kind: "json", permission: "can_manage_products", description: "Xoa nhieu san pham", sampleData: { deletedCount: 1, skippedIds: [] } },
  { method: "POST", path: "/api/v1/products/{id}/images", auth: true, kind: "multipart", permission: "can_manage_products", description: "Tai anh san pham", sampleData: { id: 1, imageUrl: product.imageUrl } },
  { method: "GET", path: "/api/v1/suppliers", auth: true, kind: "json", permission: "can_manage_products", description: "Danh sach nha cung cap", sampleData: mockList([supplier]) },
  { method: "POST", path: "/api/v1/suppliers", auth: true, kind: "json", permission: "can_manage_products", description: "Tao nha cung cap", sampleData: supplier },
  { method: "GET", path: "/api/v1/suppliers/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Chi tiet nha cung cap", sampleData: supplier },
  { method: "PATCH", path: "/api/v1/suppliers/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Cap nhat nha cung cap", sampleData: supplier },
  { method: "DELETE", path: "/api/v1/suppliers/{id}", auth: true, kind: "json", permission: "can_manage_products", description: "Xoa nha cung cap", sampleData: { deleted: true } },
  { method: "POST", path: "/api/v1/suppliers/bulk-delete", auth: true, kind: "json", permission: "can_manage_products", description: "Xoa nhieu nha cung cap", sampleData: { deletedCount: 1, skippedIds: [] } },
  { method: "GET", path: "/api/v1/customers", auth: true, kind: "json", permission: "can_manage_customers", description: "Danh sach khach hang", sampleData: mockList([customer]) },
  { method: "POST", path: "/api/v1/customers", auth: true, kind: "json", permission: "can_manage_customers", description: "Tao khach hang", sampleData: customer },
  { method: "GET", path: "/api/v1/customers/{id}", auth: true, kind: "json", permission: "can_manage_customers", description: "Chi tiet khach hang", sampleData: customer },
  { method: "PATCH", path: "/api/v1/customers/{id}", auth: true, kind: "json", permission: "can_manage_customers", description: "Cap nhat khach hang", sampleData: customer },
  { method: "DELETE", path: "/api/v1/customers/{id}", auth: true, kind: "json", permission: "can_manage_customers", description: "Xoa khach hang", sampleData: { deleted: true } },
  { method: "POST", path: "/api/v1/customers/bulk-delete", auth: true, kind: "json", permission: "can_manage_customers", description: "Xoa nhieu khach hang", sampleData: { deletedCount: 1, skippedIds: [] } },

  { method: "GET", path: "/api/v1/sales-orders", auth: true, kind: "json", permission: "can_manage_orders", description: "Danh sach don hang", sampleData: mockList([order]) },
  { method: "GET", path: "/api/v1/sales-orders/retail/history", auth: true, kind: "json", permission: "can_manage_orders", description: "Lich su ban le", sampleData: mockList([order]) },
  { method: "GET", path: "/api/v1/sales-orders/{id}", auth: true, kind: "json", permission: "can_manage_orders", description: "Chi tiet don hang", sampleData: order },
  { method: "POST", path: "/api/v1/sales-orders", auth: true, kind: "json", permission: "can_manage_orders", description: "Tao don hang", sampleData: order },
  { method: "PATCH", path: "/api/v1/sales-orders/{id}", auth: true, kind: "json", permission: "can_manage_orders", description: "Cap nhat don hang", sampleData: order },
  { method: "POST", path: "/api/v1/sales-orders/{id}/cancel", auth: true, kind: "json", permission: "can_manage_orders", description: "Huy don hang", sampleData: { ...order, status: "Cancelled" } },
  { method: "POST", path: "/api/v1/sales-orders/retail/checkout", auth: true, kind: "json", permission: "can_manage_orders", description: "Thanh toan POS", sampleData: order },
  { method: "POST", path: "/api/v1/sales-orders/retail/voucher-preview", auth: true, kind: "json", permission: "can_manage_orders", description: "Xem truoc voucher", sampleData: { discountAmount: 10000, finalAmount: 54000 } },
  { method: "GET", path: "/api/v1/pos/products", auth: true, kind: "json", permission: "can_manage_orders", description: "Tim san pham POS", sampleData: { items: [product] } },
  { method: "GET", path: "/api/v1/vouchers", auth: true, kind: "json", permission: "can_manage_orders", description: "Danh sach voucher", sampleData: mockList([{ id: 1, code: "SALE10", status: "Active" }]) },
  { method: "GET", path: "/api/v1/vouchers/{id}", auth: true, kind: "json", permission: "can_manage_orders", description: "Chi tiet voucher", sampleData: { id: 1, code: "SALE10", discountValue: 10000 } },

  { method: "GET", path: "/api/v1/approvals/pending", auth: true, kind: "json", description: "Danh sach cho duyet", sampleData: mockList([{ id: 1, entityType: "StockReceipt", entityId: 201, code: "PNK-0001", requestedBy: "Nguyenx Chi Dat", requestedAt: "2026-05-31T08:00:00Z", status: "Pending", amount: 1250000 }]) },
  { method: "GET", path: "/api/v1/approvals/history", auth: true, kind: "json", description: "Lich su phe duyet", sampleData: mockList([{ id: 1, entityType: "StockReceipt", entityId: 201, code: "PNK-0001", requestedBy: "Nguyenx Chi Dat", requestedAt: "2026-05-31T08:00:00Z", status: "Approved", amount: 1250000 }]) },

  { method: "GET", path: "/api/v1/cash-funds", auth: true, kind: "json", description: "Danh sach quy tien", sampleData: { items: [{ id: 1, fundName: "Tien mat", balance: 1000000 }] } },
  { method: "GET", path: "/api/v1/cash-transactions", auth: true, kind: "json", description: "Danh sach thu chi", sampleData: mockList([cashTransaction]) },
  { method: "POST", path: "/api/v1/cash-transactions", auth: true, kind: "json", description: "Tao giao dich thu chi", sampleData: cashTransaction },
  { method: "GET", path: "/api/v1/cash-transactions/{id}", auth: true, kind: "json", description: "Chi tiet thu chi", sampleData: cashTransaction },
  { method: "PATCH", path: "/api/v1/cash-transactions/{id}", auth: true, kind: "json", description: "Cap nhat thu chi", sampleData: cashTransaction },
  { method: "DELETE", path: "/api/v1/cash-transactions/{id}", auth: true, kind: "json", description: "Xoa thu chi", sampleData: null },
  { method: "GET", path: "/api/v1/finance-ledger", auth: true, kind: "json", permission: "can_view_finance", description: "So cai tai chinh", sampleData: mockList([{ id: 1, referenceCode: "DH-0001", amount: 64000, transactionDate: "2026-05-31" }]) },

  { method: "GET", path: "/api/v1/store-profile", auth: true, kind: "json", permission: "can_view_store_profile", description: "Thong tin cua hang", sampleData: { name: "Mini ERP Store", phone: "0900000000", email: "store@example.com" } },
  { method: "PATCH", path: "/api/v1/store-profile", auth: true, kind: "json", permission: "can_view_store_profile", description: "Cap nhat cua hang", sampleData: { name: "Mini ERP Store", phone: "0900000000", email: "store@example.com" } },
  { method: "POST", path: "/api/v1/store-profile/logo", auth: true, kind: "multipart", permission: "can_view_store_profile", description: "Tai logo cua hang", sampleData: { logoUrl: "https://example.com/logo.png" } },
  { method: "GET", path: "/api/v1/roles", auth: true, kind: "json", permission: "can_manage_staff", description: "Danh sach role", sampleData: { items: [{ id: 1, name: "Owner", permissions: ownerPermissions }] } },
  { method: "GET", path: "/api/v1/users", auth: true, kind: "json", permission: "can_manage_staff", description: "Danh sach nhan vien", sampleData: mockList([user]) },
  { method: "GET", path: "/api/v1/users/{id}", auth: true, kind: "json", permission: "can_manage_staff", description: "Chi tiet nhan vien", sampleData: user },
  { method: "GET", path: "/api/v1/users/next-staff-code", auth: true, kind: "json", permission: "can_manage_staff", description: "Goi y ma nhan vien", sampleData: { staffCode: "NV0001" } },
  { method: "POST", path: "/api/v1/users", auth: true, kind: "json", permission: "can_manage_staff", description: "Tao nhan vien", sampleData: user },
  { method: "PATCH", path: "/api/v1/users/{id}", auth: true, kind: "json", permission: "can_manage_staff", description: "Cap nhat nhan vien", sampleData: user },
  { method: "DELETE", path: "/api/v1/users/{id}", auth: true, kind: "json", permission: "can_manage_staff", description: "Xoa nhan vien", sampleData: null },
  { method: "GET", path: "/api/v1/alert-settings", auth: true, kind: "json", description: "Danh sach cau hinh canh bao", sampleData: { items: [{ id: 1, type: "LOW_STOCK", enabled: true }] } },
  { method: "POST", path: "/api/v1/alert-settings", auth: true, kind: "json", description: "Tao cau hinh canh bao", sampleData: { id: 1, type: "LOW_STOCK", enabled: true } },
  { method: "PATCH", path: "/api/v1/alert-settings/{id}", auth: true, kind: "json", description: "Cap nhat canh bao", sampleData: { id: 1, type: "LOW_STOCK", enabled: true } },
  { method: "DELETE", path: "/api/v1/alert-settings/{id}", auth: true, kind: "json", description: "Xoa canh bao", sampleData: null },
  { method: "GET", path: "/api/v1/system-logs", auth: true, kind: "json", description: "Danh sach system logs", sampleData: mockList([{ id: 1, action: "UPDATE", entity: "Inventory", createdAt: "2026-05-31T08:00:00Z" }]) },
  { method: "GET", path: "/api/v1/system-logs/{id}", auth: true, kind: "json", description: "Chi tiet system log", sampleData: { id: 1, action: "UPDATE", entity: "Inventory" } },
  { method: "DELETE", path: "/api/v1/system-logs/{id}", auth: true, kind: "json", description: "Xoa system log", sampleData: null },
  { method: "POST", path: "/api/v1/system-logs/bulk-delete", auth: true, kind: "json", description: "Xoa nhieu system log", sampleData: { deletedCount: 1 } },
  { method: "GET", path: "/api/v1/interface-settings/table-columns", auth: true, kind: "json", permission: "can_manage_inventory", description: "Cau hinh cot table Kho hang", sampleData: tableColumnSettings },
  { method: "PUT", path: "/api/v1/interface-settings/table-columns", auth: true, kind: "json", permission: "can_manage_inventory", description: "Luu cau hinh cot table Kho hang", sampleData: tableColumnSettings },

  { method: "POST", path: "/api/v1/ai/chat/stream", auth: true, kind: "sse", permission: "can_use_ai", description: "SSE tro ly AI", sampleData: [{ event: "message", data: { text: "Xin chao" } }, { event: "done", data: {} }] },
  { method: "POST", path: "/api/v1/ai/chat/transcribe", auth: true, kind: "multipart", permission: "can_use_ai", description: "Chuyen giong noi thanh text", sampleData: { text: "Ton kho sua tuoi con bao nhieu?" } },
  { method: "POST", path: "/api/v1/ai/chat/synthesize", auth: true, kind: "json", permission: "can_use_ai", description: "Chuyen text thanh audio", sampleData: { audioUrl: "data:audio/mpeg;base64,..." } },
  { method: "POST", path: "/api/v1/ai/catalog-drafts/validate", auth: true, kind: "json", permission: "can_use_ai", description: "Validate catalog draft", sampleData: catalogDraft },
  { method: "GET", path: "/api/v1/ai/catalog-drafts/{id}", auth: true, kind: "json", permission: "can_use_ai", description: "Chi tiet catalog draft", sampleData: catalogDraft },
  { method: "PATCH", path: "/api/v1/ai/catalog-drafts/{id}", auth: true, kind: "json", permission: "can_use_ai", description: "Cap nhat catalog draft", sampleData: catalogDraft },
  { method: "POST", path: "/api/v1/ai/catalog-drafts/{id}/commit", auth: true, kind: "json", permission: "can_use_ai", description: "Commit catalog draft", sampleData: { successCount: 1, failureCount: 0, outcomes: [{ rowId: "row-1", success: true, createdEntityId: 501 }], draft: catalogDraft } },
  { method: "DELETE", path: "/api/v1/ai/catalog-drafts/{id}", auth: true, kind: "json", permission: "can_use_ai", description: "Xoa catalog draft", sampleData: null },
  { method: "POST", path: "/api/v1/ai/inventory-drafts/validate", auth: true, kind: "json", permission: ["can_use_ai", "can_manage_inventory"], description: "Validate inventory draft", sampleData: inventoryDraft },
  { method: "GET", path: "/api/v1/ai/inventory-drafts/{id}", auth: true, kind: "json", permission: ["can_use_ai", "can_manage_inventory"], description: "Chi tiet inventory draft", sampleData: inventoryDraft },
  { method: "PATCH", path: "/api/v1/ai/inventory-drafts/{id}", auth: true, kind: "json", permission: ["can_use_ai", "can_manage_inventory"], description: "Cap nhat inventory draft", sampleData: inventoryDraft },
  { method: "POST", path: "/api/v1/ai/inventory-drafts/{id}/commit", auth: true, kind: "json", permission: ["can_use_ai", "can_manage_inventory"], description: "Commit inventory draft", sampleData: { successCount: 1, failureCount: 0, outcomes: [{ rowId: "row-1", success: true, createdEntityId: 101 }], draft: inventoryDraft } },
  { method: "DELETE", path: "/api/v1/ai/inventory-drafts/{id}", auth: true, kind: "json", permission: ["can_use_ai", "can_manage_inventory"], description: "Xoa inventory draft", sampleData: null },
]

export function getMockCatalogEntry(method: MockHttpMethod, path: string) {
  const cleanPath = path.split("?")[0]
  return frontendApiMockCatalog.find((entry) => entry.method === method && entry.path === cleanPath)
}

