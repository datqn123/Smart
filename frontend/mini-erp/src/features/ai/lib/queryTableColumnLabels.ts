/** Vietnamese headers for AI query-result tables (fallback when BE sends raw SQL keys). */

const COLUMN_LABELS_VI: Record<string, string> = {
  id: "ID",
  tenant_id: "Mã tenant",
  category_id: "Mã danh mục",
  product_id: "Mã sản phẩm",
  customer_id: "Mã khách hàng",
  supplier_id: "Mã nhà cung cấp",
  order_id: "Mã đơn hàng",
  sku_code: "Mã SKU",
  sku: "Mã SKU",
  barcode: "Mã vạch",
  code: "Mã",
  receipt_code: "Mã phiếu nhập",
  dispatch_code: "Mã phiếu xuất",
  order_code: "Mã đơn hàng",
  name: "Tên",
  product_name: "Tên sản phẩm",
  category_name: "Tên danh mục",
  customer_name: "Tên khách hàng",
  supplier_name: "Tên nhà cung cấp",
  description: "Mô tả",
  image_url: "Ảnh (URL)",
  weight: "Khối lượng (g)",
  status: "Trạng thái",
  quantity: "Số lượng",
  amount: "Số tiền",
  total_amount: "Tổng giá trị",
  total_value: "Tổng giá trị",
  cost_price: "Giá vốn",
  selling_price: "Giá bán",
  revenue: "Doanh thu",
  created_at: "Ngày tạo",
  updated_at: "Ngày cập nhật",
}

const WORD_VI: Record<string, string> = {
  total: "tổng",
  value: "giá trị",
  amount: "số tiền",
  receipt: "phiếu nhập",
  order: "đơn",
  product: "sản phẩm",
  customer: "khách hàng",
  supplier: "nhà cung cấp",
  category: "danh mục",
  quantity: "số lượng",
  price: "giá",
  status: "trạng thái",
  name: "tên",
  code: "mã",
  created: "tạo",
  updated: "cập nhật",
  image: "ảnh",
  url: "URL",
  description: "mô tả",
  weight: "khối lượng",
  barcode: "mã vạch",
  sku: "SKU",
}

function looksLikeRawKey(label: string, key: string): boolean {
  const a = label.trim().replace(/\s+/g, "_").toLowerCase()
  const b = key.trim().toLowerCase()
  return a === b || label.trim().toUpperCase() === key.trim().toUpperCase()
}

function columnLabelVi(key: string): string {
  const k = key.trim().toLowerCase()
  if (COLUMN_LABELS_VI[k]) return COLUMN_LABELS_VI[k]
  if (k.endsWith("_id") && k !== "id") {
    return `Mã ${k.slice(0, -3).replace(/_/g, " ")}`
  }
  const parts = k.split("_")
  if (parts.length >= 2 && parts[parts.length - 1] === "at") {
    const verb = parts[parts.length - 2] === "created" ? "tạo" : "cập nhật"
    if (parts[parts.length - 2] === "created" || parts[parts.length - 2] === "updated") {
      return `Ngày ${verb}`
    }
  }
  const translated = parts.map((p) => WORD_VI[p] ?? p)
  if (parts.every((p) => WORD_VI[p] || COLUMN_LABELS_VI[p])) {
    const text = translated.join(" ")
    return text.charAt(0).toUpperCase() + text.slice(1)
  }
  return key.replace(/_/g, " ")
}

export function getQueryTableColumnLabel(key: string, label?: string): string {
  if (label?.trim() && !looksLikeRawKey(label, key)) return label.trim()
  return columnLabelVi(key)
}

/** Hidden in chat query table UI (still in row data for edits / optional export). */
const HIDDEN_QUERY_TABLE_KEYS = new Set(["id", "category_id"])

export function isHiddenQueryTableColumn(key: string): boolean {
  return HIDDEN_QUERY_TABLE_KEYS.has(key.trim().toLowerCase())
}

export function filterVisibleQueryTableColumns(columns: { key: string; label?: string; type?: string }[]) {
  return columns.filter((c) => !isHiddenQueryTableColumn(c.key))
}

/** Visible columns: hide only id/category_id; include every other key present in rows. */
export function buildVisibleQueryTableColumns(
  columns: { key: string; label?: string; type?: string }[],
  rows: Record<string, unknown>[],
): { key: string; label?: string; type?: string }[] {
  const filtered = filterVisibleQueryTableColumns(columns)
  const byLower = new Map<string, { key: string; label?: string; type?: string }>()
  for (const c of filtered) {
    byLower.set(c.key.toLowerCase(), c)
  }

  const orderedKeys: string[] = []
  const seen = new Set<string>()
  for (const c of filtered) {
    const kl = c.key.toLowerCase()
    if (!seen.has(kl)) {
      orderedKeys.push(c.key)
      seen.add(kl)
    }
  }

  if (rows.length > 0) {
    for (const key of Object.keys(rows[0])) {
      const kl = key.toLowerCase()
      if (isHiddenQueryTableColumn(key) || seen.has(kl)) continue
      if (!byLower.has(kl)) {
        byLower.set(kl, { key, label: getQueryTableColumnLabel(key) })
      }
      orderedKeys.push(key)
      seen.add(kl)
    }
  }

  return orderedKeys
    .map((k) => byLower.get(k.toLowerCase()))
    .filter((c): c is { key: string; label?: string; type?: string } => Boolean(c))
}
