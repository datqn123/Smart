export type TableKey = "inventory_stock" | "inventory_receipts" | "inventory_dispatch"

export type TableColumnConfig = {
  key: string
  label: string
  required: boolean
  visible: boolean
  order: number
  description?: string
}

export type TableColumnSetting = {
  tableKey: TableKey
  tableLabel: string
  columns: TableColumnConfig[]
  updatedAt?: string
  updatedByName?: string
}

export type SaveTableColumnSettingsBody = {
  items: {
    tableKey: TableKey
    hiddenColumns: string[]
    columnOrder: string[]
  }[]
}

type StoredTableColumnSetting = {
  hiddenColumns?: string[]
  columnOrder?: string[]
}

const STORAGE_KEY = "mini_erp_table_column_settings_v1"
export const TABLE_COLUMN_SETTINGS_UPDATED_EVENT = "table-column-settings-updated"

const TABLE_COLUMN_DEFAULTS: TableColumnSetting[] = [
  {
    tableKey: "inventory_stock",
    tableLabel: "Tồn kho",
    columns: [
      { key: "skuCode", label: "Mã SP", required: true, visible: true, order: 0 },
      { key: "productName", label: "Tên sản phẩm", required: true, visible: true, order: 1 },
      { key: "location", label: "Vị trí", required: false, visible: true, order: 2 },
      { key: "quantity", label: "Tồn kho", required: false, visible: true, order: 3 },
      { key: "expiryDate", label: "Hạn SD", required: false, visible: true, order: 4 },
      { key: "status", label: "Trạng thái", required: false, visible: true, order: 5 },
    ],
  },
  {
    tableKey: "inventory_receipts",
    tableLabel: "Phiếu nhập kho",
    columns: [
      { key: "receiptCode", label: "Mã phiếu", required: true, visible: true, order: 0 },
      { key: "supplierName", label: "Nhà cung cấp", required: false, visible: true, order: 1 },
      { key: "receiptDate", label: "Ngày nhập", required: false, visible: true, order: 2 },
      { key: "staffName", label: "Người tạo", required: false, visible: true, order: 3 },
      { key: "invoiceNumber", label: "Số hóa đơn", required: false, visible: true, order: 4 },
      { key: "lineCount", label: "Số dòng hàng", required: false, visible: true, order: 5 },
      { key: "totalAmount", label: "Tổng tiền", required: false, visible: true, order: 6 },
      { key: "status", label: "Trạng thái", required: false, visible: true, order: 7 },
    ],
  },
  {
    tableKey: "inventory_dispatch",
    tableLabel: "Xuất kho & Điều phối",
    columns: [
      { key: "dispatchCode", label: "Mã phiếu", required: true, visible: true, order: 0 },
      { key: "orderCode", label: "Mã đơn hàng", required: false, visible: true, order: 1 },
      { key: "customerName", label: "Khách hàng", required: false, visible: true, order: 2 },
      { key: "dispatchDate", label: "Ngày xuất", required: false, visible: true, order: 3 },
      { key: "userName", label: "Người xuất", required: false, visible: true, order: 4 },
      { key: "itemCount", label: "Số lượng", required: false, visible: true, order: 5 },
      { key: "status", label: "Trạng thái", required: false, visible: true, order: 6 },
    ],
  },
]

function cloneDefaults(): TableColumnSetting[] {
  return TABLE_COLUMN_DEFAULTS.map((t) => ({
    ...t,
    columns: t.columns.map((c) => ({ ...c })),
  }))
}

function normalizeStoredValue(rawValue: unknown): StoredTableColumnSetting {
  if (Array.isArray(rawValue)) {
    return { hiddenColumns: rawValue.filter((v): v is string => typeof v === "string") }
  }
  if (!rawValue || typeof rawValue !== "object") {
    return {}
  }
  const value = rawValue as StoredTableColumnSetting
  return {
    hiddenColumns: Array.isArray(value.hiddenColumns)
      ? value.hiddenColumns.filter((v): v is string => typeof v === "string")
      : [],
    columnOrder: Array.isArray(value.columnOrder)
      ? value.columnOrder.filter((v): v is string => typeof v === "string")
      : undefined,
  }
}

function readSettingsMap(): Record<string, StoredTableColumnSetting> {
  if (typeof window === "undefined") {
    return {}
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return {}
    }
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== "object") {
      return {}
    }
    return Object.entries(parsed).reduce<Record<string, StoredTableColumnSetting>>((acc, [key, value]) => {
      acc[key] = normalizeStoredValue(value)
      return acc
    }, {})
  } catch {
    return {}
  }
}

function writeSettingsMap(value: Record<string, StoredTableColumnSetting>) {
  if (typeof window === "undefined") {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  window.dispatchEvent(new CustomEvent(TABLE_COLUMN_SETTINGS_UPDATED_EVENT))
}

function applyOrder(columns: TableColumnConfig[], columnOrder?: string[]) {
  const knownKeys = new Set(columns.map((column) => column.key))
  const orderedKeys = [
    ...(columnOrder ?? []).filter((key) => knownKeys.has(key)),
    ...columns.map((column) => column.key).filter((key) => !(columnOrder ?? []).includes(key)),
  ]
  const orderMap = new Map(orderedKeys.map((key, index) => [key, index]))
  return columns
    .map((column) => ({ ...column, order: orderMap.get(column.key) ?? column.order }))
    .sort((a, b) => a.order - b.order)
}

export async function getTableColumnSettings(): Promise<TableColumnSetting[]> {
  const defaults = cloneDefaults()
  const storedMap = readSettingsMap()
  return defaults.map((table) => {
    const stored = storedMap[table.tableKey] ?? {}
    const hidden = new Set(stored.hiddenColumns ?? [])
    return {
      ...table,
      columns: applyOrder(table.columns, stored.columnOrder).map((column, index) => ({
        ...column,
        order: index,
        visible: column.required ? true : !hidden.has(column.key),
      })),
    }
  })
}

export async function saveTableColumnSettings(body: SaveTableColumnSettingsBody): Promise<void> {
  const defaults = cloneDefaults()
  const baseMap = readSettingsMap()
  for (const item of body.items) {
    const table = defaults.find((t) => t.tableKey === item.tableKey)
    if (!table) {
      continue
    }
    const knownKeys = new Set(table.columns.map((c) => c.key))
    const requiredKeys = new Set(table.columns.filter((c) => c.required).map((c) => c.key))
    const columnOrder = [
      ...item.columnOrder.filter((key) => knownKeys.has(key)),
      ...table.columns.map((c) => c.key).filter((key) => !item.columnOrder.includes(key)),
    ]
    baseMap[item.tableKey] = {
      hiddenColumns: item.hiddenColumns.filter((key) => knownKeys.has(key) && !requiredKeys.has(key)),
      columnOrder,
    }
  }
  writeSettingsMap(baseMap)
}

export function getDefaultTableColumnSettings(): TableColumnSetting[] {
  return cloneDefaults()
}

