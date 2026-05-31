import { apiJson } from "@/lib/api/http"

/** Task059 — `GET /api/v1/pos/products` — `docs/frontend/api/API_Task059_pos_products_get_search.md` + BE `PosProductsController`. */
export const POS_PRODUCTS_SEARCH_QUERY_KEY = ["orders", "pos-products", "v1", "search"] as const

export type PosProductRowDto = {
  productId: number
  productName: string
  skuCode: string
  barcode: string | null
  unitId: number
  unitName: string
  unitPrice: number | string | null
  availableQty: number
  imageUrl: string | null
}

export type PosProductSearchDataDto = {
  items: PosProductRowDto[]
}

export type SearchPosProductsParams = {
  search?: string
  categoryId?: number
  locationId?: number
  /** Mặc định 40, tối đa 100 (BE clamp). */
  limit?: number
}

export function numUnitPrice(v: number | string | null | undefined): number {
  if (v == null) return 0
  const n = typeof v === "number" ? v : Number(v)
  return Number.isFinite(n) ? n : 0
}

export function searchPosProducts(params: SearchPosProductsParams = {}) {
  const q = new URLSearchParams()
  const s = params.search?.trim()
  if (s) q.set("search", s)
  if (params.categoryId != null && params.categoryId > 0) {
    q.set("categoryId", String(params.categoryId))
  }
  if (params.locationId != null && params.locationId > 0) {
    q.set("locationId", String(params.locationId))
  }
  const lim = params.limit ?? 40
  q.set("limit", String(Math.min(100, Math.max(1, lim))))
  return apiJson<PosProductSearchDataDto>(`/api/v1/pos/products?${q.toString()}`, { method: "GET", auth: true })
}
