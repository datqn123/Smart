/**
 * Chuẩn layout bảng danh sách (Data Table) — đồng bộ với `docs/rules/RULES_UI_TABLE.md`.
 * Import các constant này khi tạo bảng mới để giữ width / sticky / root class nhất quán.
 */

/** Gốc `<Table>`: một thead + tbody, `table-fixed`, không cuộn ngang trên desktop (fit window). */
export const DATA_TABLE_ROOT_CLASS =
  "bg-white border-none border-separate border-spacing-0 table-fixed w-full"

/** Vỏ bảng (wrapper) chuẩn: border + radius + shadow, dùng chung toàn project. */
export const DATA_TABLE_SHELL_CLASS =
  "flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md"

/** Vùng cuộn bảng (1 vùng cuộn cho thead sticky + tbody). */
export const DATA_TABLE_SCROLL_CLASS =
  "flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"

/**
 * Cột NV / Thao tác: tối thiểu ~168px để vừa 3 nút `size="icon"` h-8 w-8 + gap-1 + padding cell.
 * Không đặt `flex` trực tiếp trên `<td>` / `<th>` — bọc nút trong `<div className="flex ...">`.
 */
export const DATA_TABLE_ACTION_COL_WIDTH = "w-[168px]"

export const DATA_TABLE_ACTION_HEAD_CLASS = `${DATA_TABLE_ACTION_COL_WIDTH} text-center sticky right-0 z-30 bg-slate-50 shadow-[-4px_0_8px_-4px_rgba(15,23,42,0.12)]`

export const DATA_TABLE_ACTION_CELL_CLASS = `${DATA_TABLE_ACTION_COL_WIDTH} text-center sticky right-0 z-10 bg-white group-hover:bg-slate-50/50 shadow-[-4px_0_8px_-4px_rgba(15,23,42,0.08)]`

/** Một nút icon (vd: Tồn kho — xem lô; Kiểm kê — mở chi tiết). */
export const DATA_TABLE_ACTION_SINGLE_COL_WIDTH = "w-[96px]"

export const DATA_TABLE_ACTION_SINGLE_HEAD_CLASS = `${DATA_TABLE_ACTION_SINGLE_COL_WIDTH} text-center sticky right-0 z-30 bg-slate-50 shadow-[-4px_0_8px_-4px_rgba(15,23,42,0.12)]`

export const DATA_TABLE_ACTION_SINGLE_CELL_CLASS = `${DATA_TABLE_ACTION_SINGLE_COL_WIDTH} text-center sticky right-0 z-10 bg-white group-hover:bg-slate-50/50 shadow-[-4px_0_8px_-4px_rgba(15,23,42,0.08)]`

/** Phiếu nhập kho — width khớp thead/tbody */
export const RECEIPT_TABLE_COL = {
  receiptCode: "w-[116px]",
  supplierName: "w-[168px] min-w-0",
  receiptDate: "w-[100px]",
  staffName: "w-[140px]",
  invoiceNumber: "w-[92px]",
  lineCount: "w-[72px]",
  totalAmount: "w-[124px]",
  status: "w-[112px]",
} as const

/** Phiếu xuất kho */
export const DISPATCH_TABLE_COL = {
  dispatchCode: "w-[116px]",
  orderCode: "w-[116px] min-w-0",
  customerName: "w-[140px] min-w-0",
  dispatchDate: "w-[100px]",
  userName: "w-[188px] min-w-0",
  itemCount: "w-[72px]",
  status: "w-[144px]",
} as const

/** Tồn kho (danh sách SKU) — có cột checkbox */
export const STOCK_TABLE_COL = {
  select: "w-[48px]",
  skuCode: "w-[112px]",
  /** Cố định ~200px thay vì min-w lớn — phần dư bảng fixed chuyển sang cột cuối */
  productName: "w-[200px] min-w-0",
  location: "w-[120px]",
  quantity: "w-[120px]",
  expiryDate: "w-[120px]",
  status: "w-[120px]",
} as const

/** Đợt kiểm kê kho (danh sách phiên) */
export const AUDIT_SESSION_TABLE_COL = {
  auditCode: "w-[128px]",
  title: "min-w-[200px]",
  auditDate: "w-[104px]",
  createdByName: "w-[152px]",
  progress: "w-[104px]",
  varianceHint: "w-[100px]",
  status: "w-[120px]",
} as const

/** Sản phẩm (danh sách SKU) — tên có truncate; không dùng min-w lớn để tránh nuốt chỗ các cột số/trạng thái. */
export const PRODUCT_TABLE_COL = {
  select: "w-[48px]",
  skuCode: "w-[124px]",
  productName: "w-[200px] min-w-0",
  categoryName: "w-[200px]",
  stock: "w-[120px]",
  price: "w-[160px]",
  status: "w-[132px]",
} as const

/** Danh mục sản phẩm (cấu trúc cây) */
export const CATEGORY_TABLE_COL = {
  select: "w-[48px]",
  categoryCode: "w-[180px]",
  categoryName: "min-w-[240px]",
  productCount: "w-[92px]",
  description: "min-w-[240px]",
  status: "w-[120px]",
} as const
/** Khách hàng */
export const CUSTOMER_TABLE_COL = {
  select: "w-[48px]",
  code: "w-[112px]",
  name: "min-w-[200px]",
  phone: "w-[128px]",
  email: "w-[200px]",
  orders: "w-[80px]",
  status: "w-[120px]",
} as const

/** Nhà cung cấp — `address` dùng `w-[1%]` để hút phần dư trong `table-fixed` (RULES_UI_TABLE). */
export const SUPPLIER_TABLE_COL = {
  select: "w-[48px]",
  code: "w-[100px]",
  name: "w-[180px] min-w-0",
  contact: "w-[120px] min-w-0",
  email: "w-[200px] min-w-0",
  address: "min-w-[200px] w-[1%]",
  status: "w-[112px]",
} as const

/** Đơn hàng (Wholesale / Retail — `OrderTable`): `code` hút phần dư; `customer` cố định + truncate, tránh cột Khách hàng quá rộng. */
export const ORDER_TABLE_COL = {
  select: "w-[48px]",
  code: "min-w-[108px] w-[1%]",
  customer: "w-[176px] min-w-0",
  date: "w-[104px]",
  items: "w-[84px]",
  total: "w-[136px]",
  payment: "w-[112px]",
  status: "w-[128px]",
} as const

/** Nhân viên / Người dùng */
export const USER_TABLE_COL = {
  select: "w-[48px]",
  avatar: "w-[56px]",
  fullName: "min-w-[160px]", // Fix key to fullName as used in table
  role: "w-[120px]",
  email: "w-[180px]",
  phone: "w-[124px]",
  status: "w-[112px]",
} as const

/** Giao dịch tài chính (Thu chi) */
export const TRANSACTION_TABLE_COL = {
  select: "w-[48px]",
  code: "w-[116px]",
  date: "w-[120px]",
  type: "w-[100px]",
  category: "w-[140px]",
  amount: "w-[140px]",
  method: "w-[112px]",
  status: "w-[112px]",
  description: "min-w-[200px]",
} as const

/** Sổ nợ */
export const DEBT_TABLE_COL = {
  select: "w-[48px]",
  code: "w-[116px]",
  partner: "min-w-[180px]",
  type: "w-[100px]",
  total: "w-[124px]",
  paid: "w-[124px]",
  remaining: "w-[124px]",
  lastUpdate: "w-[120px]",
  status: "w-[112px]",
} as const

/** Sổ cái */
export const LEDGER_TABLE_COL = {
  date: "w-[104px]",
  type: "w-[148px]",
  reference: "w-[168px]",
  code: "w-[116px]",
  description: "min-w-[180px]",
  amount: "w-[120px]",
  debit: "w-[112px]",
  credit: "w-[112px]",
  balance: "w-[128px]",
} as const

/**
 * Typography Standards — đồng bộ với ADR-005.
 * Dùng cho các thẻ <th>, <td>, <Label>, <Input>.
 */

export const TABLE_HEAD_CLASS = "text-[12px] font-bold uppercase tracking-wider text-slate-500 bg-slate-50 border-b border-slate-200"

export const TABLE_CELL_PRIMARY_CLASS = "text-sm font-semibold text-slate-900"
export const TABLE_CELL_SECONDARY_CLASS = "text-sm text-slate-600"
export const TABLE_CELL_MONO_CLASS = "text-[13px] font-mono font-medium text-slate-500"
export const TABLE_CELL_NUMBER_CLASS = "text-sm font-medium text-slate-900 tabular-nums"

export const FORM_LABEL_CLASS = "text-sm font-semibold text-slate-700 block mb-1.5"
export const FORM_INPUT_CLASS = "h-11 border-slate-200 focus:ring-slate-100 focus:border-slate-900"
export const FORM_HELPER_CLASS = "text-xs text-slate-500 mt-1"

/** Checkbox chuẩn cho các bảng records. */
export const DATA_TABLE_CHECKBOX_CLASS =
  "border-slate-300 data-[state=checked]:bg-slate-800 data-[state=checked]:text-white data-[state=checked]:border-slate-800"
