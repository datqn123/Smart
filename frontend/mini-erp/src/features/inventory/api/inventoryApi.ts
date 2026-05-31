import { apiJson } from "@/lib/api/http"
import type { InventoryItem, InventoryKPIs } from "../types"

function normBatch(s: string | undefined): string | null {
  if (s == null || s.trim() === "") {
    return null
  }
  return s.trim()
}

function normExpiryDay(s: string | undefined): string | null {
  if (s == null || s.trim() === "") {
    return null
  }
  return s.trim().split("T")[0] ?? null
}

/**
 * Task005 — `GET /api/v1/inventory` (màn Tồn kho) — hợp đồng
 * `docs/frontend/api/API_Task005_inventory_get_list.md` §7.
 * Task006 — `GET /api/v1/inventory/{id}` — `docs/frontend/api/API_Task006_inventory_get_by_id.md`.
 * Task007 — `PATCH /api/v1/inventory/{id}` — `docs/frontend/api/API_Task007_inventory_patch.md`.
 * Task008 — `PATCH /api/v1/inventory/bulk` — `docs/frontend/api/API_Task008_inventory_bulk_patch.md`.
 * Task009 — `GET /api/v1/inventory/summary` — `docs/frontend/api/API_Task009_inventory_get_summary.md`.
 */
export type InventoryListSummary = {
  totalSkus: number
  totalValue: number
  lowStockCount: number
  expiringSoonCount: number
}

export type InventoryListItemResponse = {
  id: number
  productId: number
  productName: string
  skuCode: string
  barcode: string | null
  locationId: number
  warehouseCode: string
  shelfCode: string
  batchNumber: string | null
  expiryDate: string | null
  quantity: number
  minQuantity: number
  unitId: number
  unitName: string
  costPrice: number
  updatedAt: string
  isLowStock: boolean
  isExpiringSoon: boolean
  totalValue: number
}

export type InventoryListData = {
  summary: InventoryListSummary
  items: InventoryListItemResponse[]
  page: number
  limit: number
  total: number
}

export type GetInventoryListParams = {
  search?: string
  stockLevel?: "all" | "in_stock" | "low_stock" | "out_of_stock"
  locationId?: number
  categoryId?: number
  /** Lọc theo `Inventory.product_id` (form phiếu nhập — danh sách lô tồn). */
  productId?: number
  page?: number
  limit?: number
  sort?: string
}

/** Khớp `InventoryListQuery.MAX_LIMIT` (BE) — vượt sẽ 400 "Giá trị phải từ 1 đến 100". */
export const INVENTORY_LIST_API_MAX_LIMIT = 100

/**
 * Tải mọi dòng tồn cho một sản phẩm (phân trang nội bộ, mỗi trang ≤ {@link INVENTORY_LIST_API_MAX_LIMIT}).
 * Dùng cho dropdown chọn lô khi một SP có nhiều vị trí/lô.
 */
export async function getInventoryListAllForProduct(
  productId: number,
  opts?: Pick<GetInventoryListParams, "stockLevel" | "sort">,
): Promise<InventoryListItemResponse[]> {
  const limit = INVENTORY_LIST_API_MAX_LIMIT
  const stockLevel = opts?.stockLevel ?? "all"
  const sort = opts?.sort
  const out: InventoryListItemResponse[] = []
  let page = 1
  const maxPages = 500
  while (page <= maxPages) {
    const data = await getInventoryList({
      productId,
      page,
      limit,
      stockLevel,
      ...(sort != null ? { sort } : {}),
    })
    out.push(...data.items)
    if (data.items.length < limit || out.length >= data.total) {
      break
    }
    page += 1
  }
  return out
}

/** Tham số lọc giống Task005 — KPI-only (Task009). */
export type GetInventorySummaryParams = Pick<
  GetInventoryListParams,
  "search" | "stockLevel" | "locationId" | "categoryId"
>

export function getInventorySummary(params: GetInventorySummaryParams = {}) {
  const q = new URLSearchParams()
  if (params.search) {
    q.set("search", params.search)
  }
  if (params.stockLevel) {
    q.set("stockLevel", params.stockLevel)
  }
  if (params.locationId != null && params.locationId > 0) {
    q.set("locationId", String(params.locationId))
  }
  if (params.categoryId != null && params.categoryId > 0) {
    q.set("categoryId", String(params.categoryId))
  }
  const qs = q.toString()
  return apiJson<InventoryListSummary>(qs ? `/api/v1/inventory/summary?${qs}` : "/api/v1/inventory/summary", {
    method: "GET",
    auth: true,
  })
}

export function getInventoryList(params: GetInventoryListParams) {
  const q = new URLSearchParams()
  if (params.search) {
    q.set("search", params.search)
  }
  if (params.stockLevel) {
    q.set("stockLevel", params.stockLevel)
  }
  if (params.locationId != null && params.locationId > 0) {
    q.set("locationId", String(params.locationId))
  }
  if (params.categoryId != null && params.categoryId > 0) {
    q.set("categoryId", String(params.categoryId))
  }
  if (params.productId != null && params.productId > 0) {
    q.set("productId", String(params.productId))
  }
  if (params.page != null) {
    q.set("page", String(params.page))
  }
  if (params.limit != null) {
    q.set("limit", String(params.limit))
  }
  if (params.sort) {
    q.set("sort", params.sort)
  }
  const qs = q.toString()
  return apiJson<InventoryListData>(qs ? `/api/v1/inventory?${qs}` : "/api/v1/inventory", {
    method: "GET",
    auth: true,
  })
}

export function mapListItemToUi(row: InventoryListItemResponse): InventoryItem {
  return {
    id: row.id,
    productId: row.productId,
    productName: row.productName,
    skuCode: row.skuCode,
    locationId: row.locationId,
    warehouseCode: row.warehouseCode,
    shelfCode: row.shelfCode,
    batchNumber: row.batchNumber ?? undefined,
    expiryDate: row.expiryDate ?? undefined,
    quantity: row.quantity,
    minQuantity: row.minQuantity,
    unitName: row.unitName,
    costPrice: row.costPrice,
    updatedAt: row.updatedAt,
    isLowStock: row.isLowStock,
    isExpiringSoon: row.isExpiringSoon,
    totalValue: row.totalValue,
    barcode: row.barcode ?? undefined,
    unitId: row.unitId,
  }
}

export function mapSummaryToKpis(s: InventoryListSummary): InventoryKPIs {
  return {
    totalSKUs: s.totalSkus,
    totalValue: s.totalValue,
    lowStockCount: s.lowStockCount,
    expiringSoonCount: s.expiringSoonCount,
  }
}

/** Dòng lô liên quan (cùng SP, khác id; BE chỉ trả lô còn hàng). */
export type InventoryRelatedLineResponse = {
  id: number
  batchNumber: string | null
  quantity: number
  expiryDate: string | null
  warehouseCode: string
  shelfCode: string
}

export type InventoryDetailResponse = InventoryListItemResponse & {
  relatedLines: InventoryRelatedLineResponse[]
}

export type GetInventoryByIdOptions = {
  /** Khi true gửi `?include=relatedLines` (SRS Task006 / PO OQ-2). */
  includeRelatedLines?: boolean
}

export function getInventoryById(id: number, opts?: GetInventoryByIdOptions) {
  const q = new URLSearchParams()
  if (opts?.includeRelatedLines) {
    q.set("include", "relatedLines")
  }
  const qs = q.toString()
  const path = qs ? `/api/v1/inventory/${id}?${qs}` : `/api/v1/inventory/${id}`
  return apiJson<InventoryDetailResponse>(path, {
    method: "GET",
    auth: true,
  })
}

/** Body PATCH (partial) — API Task007 §5.4. */
export type InventoryPatchBody = {
  locationId?: number
  minQuantity?: number
  batchNumber?: string | null
  expiryDate?: string | null
  unitId?: number | null
}

/**
 * Task007 — cập nhật meta một dòng; `data` cùng shape phần tử list Task005.
 */
export function patchInventory(id: number, body: InventoryPatchBody) {
  return apiJson<InventoryListItemResponse>(`/api/v1/inventory/${id}`, {
    method: "PATCH",
    auth: true,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
}

/** Một phần tử trong body bulk — `id` + field PATCH (chỉ gửi dòng có thay đổi). */
export type InventoryBulkPatchItemBody = { id: number } & InventoryPatchBody

export type InventoryBulkPatchData = {
  updated: InventoryListItemResponse[]
  failed: unknown[]
}

/**
 * Task008 — cập nhật meta nhiều dòng (all-or-nothing); `data.updated` cùng shape list Task005.
 */
export function patchBulkInventory(items: InventoryBulkPatchItemBody[]) {
  return apiJson<InventoryBulkPatchData>("/api/v1/inventory/bulk", {
    method: "PATCH",
    auth: true,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  })
}

/**
 * Từ các cặp before/after sau sửa dialog — chỉ thêm phần tử có ít nhất một field meta đổi (bỏ qua dòng không đổi).
 */
export function buildInventoryBulkPatchItems(
  pairs: { before: InventoryItem; after: InventoryItem }[],
): InventoryBulkPatchItemBody[] {
  const out: InventoryBulkPatchItemBody[] = []
  for (const { before, after } of pairs) {
    const body = buildInventoryPatchBody(before, after)
    if (body) {
      out.push({ id: after.id, ...body })
    }
  }
  return out
}

/**
 * So khớp trước/sau màn sửa để chỉ gửi field đổi (PATCH partial). Trả `null` nếu không có gì gửi.
 */
export function buildInventoryPatchBody(before: InventoryItem, after: InventoryItem): InventoryPatchBody | null {
  const body: InventoryPatchBody = {}
  if (after.locationId !== before.locationId) {
    body.locationId = after.locationId
  }
  if (after.minQuantity !== before.minQuantity) {
    body.minQuantity = after.minQuantity
  }
  if (normBatch(after.batchNumber) !== normBatch(before.batchNumber)) {
    body.batchNumber = normBatch(after.batchNumber)
  }
  if (normExpiryDay(after.expiryDate) !== normExpiryDay(before.expiryDate)) {
    body.expiryDate = normExpiryDay(after.expiryDate)
  }
  const uAfter = after.unitId ?? null
  const uBefore = before.unitId ?? null
  if (uAfter !== uBefore) {
    body.unitId = uAfter
  }
  return Object.keys(body).length > 0 ? body : null
}
