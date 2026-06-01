import { apiJson } from "@/lib/api/http"

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
  scopeType?: "GLOBAL" | "USER"
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

function dispatchSettingsUpdatedEvent() {
  if (typeof window === "undefined") {
    return
  }
  window.dispatchEvent(new CustomEvent(TABLE_COLUMN_SETTINGS_UPDATED_EVENT))
}

function normalizeColumns(columns: TableColumnConfig[]) {
  return [...columns]
    .sort((a, b) => a.order - b.order)
    .map((column, index) => ({
      ...column,
      order: index,
      visible: column.required ? true : column.visible,
    }))
}

type GetTableColumnSettingsResponse = {
  items?: {
    tableKey?: string
    tableLabel?: string
    scopeType?: "GLOBAL" | "USER"
    columns?: {
      key?: string
      label?: string
      required?: boolean
      visible?: boolean
      order?: number
    }[]
    updatedAt?: string
    updatedByName?: string
  }[]
}

function normalizeApiSettings(raw: GetTableColumnSettingsResponse | null | undefined): TableColumnSetting[] {
  const defaults = cloneDefaults()
  const byKey = new Map((raw?.items ?? [])
    .filter((item): item is NonNullable<GetTableColumnSettingsResponse["items"]>[number] => !!item?.tableKey)
    .map((item) => [item.tableKey as string, item]))
  return defaults.map((table) => {
    const item = byKey.get(table.tableKey)
    if (!item?.columns || item.columns.length === 0) {
      return { ...table, columns: normalizeColumns(table.columns) }
    }
    const mergedColumns = table.columns.map((defaultColumn) => {
      const fromApi = item.columns?.find((c) => c?.key === defaultColumn.key)
      if (!fromApi) {
        return { ...defaultColumn }
      }
      return {
        ...defaultColumn,
        label: typeof fromApi.label === "string" && fromApi.label.trim() ? fromApi.label : defaultColumn.label,
        required: Boolean(fromApi.required ?? defaultColumn.required),
        visible: Boolean(fromApi.visible ?? defaultColumn.visible),
        order: typeof fromApi.order === "number" ? fromApi.order : defaultColumn.order,
      }
    })
    return {
      ...table,
      tableLabel: typeof item.tableLabel === "string" && item.tableLabel.trim() ? item.tableLabel : table.tableLabel,
      scopeType: item.scopeType,
      updatedAt: item.updatedAt,
      updatedByName: item.updatedByName,
      columns: normalizeColumns(mergedColumns),
    }
  })
}

export async function getTableColumnSettings(): Promise<TableColumnSetting[]> {
  try {
    const data = await apiJson<GetTableColumnSettingsResponse>("/api/v1/interface-settings/table-columns?scope=inventory", {
      auth: true,
    })
    return normalizeApiSettings(data)
  } catch {
    return getDefaultTableColumnSettings()
  }
}

export async function saveTableColumnSettings(body: SaveTableColumnSettingsBody): Promise<void> {
  await apiJson("/api/v1/interface-settings/table-columns", {
    method: "PUT",
    auth: true,
    body: JSON.stringify(body),
  })
  dispatchSettingsUpdatedEvent()
}

export function getDefaultTableColumnSettings(): TableColumnSetting[] {
  return cloneDefaults()
}
