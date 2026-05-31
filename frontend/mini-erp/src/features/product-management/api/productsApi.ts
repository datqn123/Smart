import { apiFormData, apiJson } from "@/lib/api/http"
import type { Product } from "../types"

/** Task034 — `GET /api/v1/products` — `docs/frontend/api/API_Task034_products_get_list.md` + SRS §8.2. */
export const PRODUCT_LIST_SORT_WHITELIST = [
  "name:asc",
  "name:desc",
  "skuCode:asc",
  "skuCode:desc",
  "updatedAt:asc",
  "updatedAt:desc",
  "createdAt:asc",
  "createdAt:desc",
] as const

export type ProductListSort = (typeof PRODUCT_LIST_SORT_WHITELIST)[number]

/** Nhãn hiển thị cho dropdown Sắp xếp (giá trị gửi API vẫn là `field:dir`). */
export const PRODUCT_LIST_SORT_LABEL_VI: Record<ProductListSort, string> = {
  "name:asc": "Tên (A → Z)",
  "name:desc": "Tên (Z → A)",
  "skuCode:asc": "Mã SKU tăng dần",
  "skuCode:desc": "Mã SKU giảm dần",
  "updatedAt:asc": "Cập nhật (cũ nhất trước)",
  "updatedAt:desc": "Cập nhật (mới nhất trước)",
  "createdAt:asc": "Ngày tạo (cũ nhất trước)",
  "createdAt:desc": "Ngày tạo (mới nhất trước)",
}

export type ProductListItemDto = {
  id: number
  skuCode: string
  barcode: string | null
  name: string
  categoryId: number | null
  categoryName: string | null
  imageUrl: string | null
  status: string
  currentStock: number
  currentPrice: number | string | null
  createdAt: string
  updatedAt: string
}

export type ProductListPageDto = {
  items: ProductListItemDto[]
  page: number
  limit: number
  total: number
}

export type GetProductListParams = {
  search?: string
  categoryId?: number
  status?: "all" | "Active" | "Inactive"
  page?: number
  limit?: number
  sort?: ProductListSort
}

function parsePrice(v: unknown): number | undefined {
  if (v == null) return undefined
  if (typeof v === "number" && !Number.isNaN(v)) return v
  const n = Number(v)
  return Number.isFinite(n) ? n : undefined
}

export function mapProductListItemDtoToProduct(d: ProductListItemDto): Product {
  return {
    id: d.id,
    skuCode: d.skuCode,
    barcode: d.barcode ?? undefined,
    name: d.name,
    categoryId: d.categoryId ?? undefined,
    categoryName: d.categoryName ?? undefined,
    imageUrl: d.imageUrl ?? undefined,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    currentStock: typeof d.currentStock === "number" ? d.currentStock : Number(d.currentStock),
    currentPrice: parsePrice(d.currentPrice),
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
  }
}

export function getProductList(params: GetProductListParams = {}) {
  const q = new URLSearchParams()
  if (params.search?.trim()) {
    q.set("search", params.search.trim())
  }
  if (params.categoryId != null && params.categoryId > 0) {
    q.set("categoryId", String(params.categoryId))
  }
  if (params.status && params.status !== "all") {
    q.set("status", params.status)
  }
  q.set("page", String(params.page ?? 1))
  q.set("limit", String(params.limit ?? 20))
  const sort = params.sort ?? "updatedAt:desc"
  q.set("sort", sort)
  return apiJson<ProductListPageDto>(`/api/v1/products?${q.toString()}`, { method: "GET", auth: true })
}

const PRODUCT_LIST_MAX_PAGE_SIZE = 100

/** Lấy toàn bộ sản phẩm (lặp trang) cho dropdown form — `limit` tối đa 100 theo API Task034. */
export async function getProductListAllPages(
  params: Omit<GetProductListParams, "page" | "limit"> = {},
): Promise<ProductListItemDto[]> {
  const sort = params.sort ?? "name:asc"
  const first = await getProductList({ ...params, page: 1, limit: PRODUCT_LIST_MAX_PAGE_SIZE, sort })
  const items = [...first.items]
  const totalPages = Math.max(1, Math.ceil(first.total / PRODUCT_LIST_MAX_PAGE_SIZE))
  for (let page = 2; page <= totalPages; page++) {
    const next = await getProductList({ ...params, page, limit: PRODUCT_LIST_MAX_PAGE_SIZE, sort })
    items.push(...next.items)
  }
  return items
}

// --- Task036 — `GET /api/v1/products/{id}` + Task037 — `PATCH /api/v1/products/{id}`

export type ProductUnitRowDto = {
  id: number
  unitName: string
  conversionRate: number | string
  isBaseUnit: boolean
  currentCostPrice: number | string | null
  currentSalePrice: number | string | null
}

export type ProductGalleryImageDto = {
  id: number
  url: string
  sortOrder: number
  isPrimary: boolean
}

/** Chi tiết sản phẩm (Task036) — dùng cho form sửa + invalidate cache. */
export type ProductDetailDto = {
  id: number
  skuCode: string
  barcode: string | null
  name: string
  categoryId: number | null
  categoryName: string | null
  description: string | null
  weight: number | string | null
  status: string
  imageUrl: string | null
  createdAt: string
  updatedAt: string
  units: ProductUnitRowDto[]
  images: ProductGalleryImageDto[]
}

export function parseProductDecimal(v: unknown): number {
  if (v == null) return 0
  if (typeof v === "number" && !Number.isNaN(v)) return v
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

export function getProductById(id: number) {
  return apiJson<ProductDetailDto>(`/api/v1/products/${id}`, { method: "GET", auth: true })
}

export function patchProduct(id: number, body: Record<string, unknown>) {
  return apiJson<ProductDetailDto>(`/api/v1/products/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

/** Task038 — `DELETE /api/v1/products/{id}` — `docs/frontend/api/API_Task038_products_delete.md`. */
export type ProductDeleteDto = {
  id: number
  deleted: boolean
}

export function deleteProduct(id: number) {
  return apiJson<ProductDeleteDto>(`/api/v1/products/${id}`, { method: "DELETE", auth: true })
}

/** Snapshot server để chỉ gửi field thay đổi (Task037 partial PATCH). */
export type ProductEditSnapshot = {
  name: string
  skuCode: string
  barcode: string | null
  categoryId: number | null
  description: string | null
  weight: number | null
  status: "Active" | "Inactive"
  salePrice: number
  costPrice: number
}

export type ProductFormPatchInput = {
  name: string
  skuCode: string
  barcode?: string
  categoryId: number
  description?: string
  weight?: number
  status: "Active" | "Inactive"
  salePrice: number
  costPrice: number
  priceEffectiveDate?: string
}

export function productDetailToEditSnapshot(d: ProductDetailDto): ProductEditSnapshot {
  const base = d.units?.find((u) => u.isBaseUnit)
  return {
    name: d.name,
    skuCode: d.skuCode,
    barcode: d.barcode,
    categoryId: d.categoryId ?? null,
    description: d.description,
    weight: d.weight != null ? parseProductDecimal(d.weight) : null,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    salePrice: base != null ? parseProductDecimal(base.currentSalePrice) : 0,
    costPrice: base != null ? parseProductDecimal(base.currentCostPrice) : 0,
  }
}

function normBarcodePatch(s: string | undefined): string | null {
  const t = (s ?? "").trim()
  return t === "" ? null : t
}

function normDescPatch(s: string | undefined): string | null {
  const t = (s ?? "").trim()
  return t === "" ? null : t
}

function normWeightPatch(v: number | undefined): number | null {
  if (v == null || Number.isNaN(v) || v === 0) return null
  return v
}

/**
 * Body PATCH chỉ gồm field khác snapshot — không gửi key nếu không đổi (Task037).
 * Giá: nếu đổi sale hoặc cost thì luôn gửi cả hai + `priceEffectiveDate` khi có.
 */
export function buildProductPatchBody(
  snap: ProductEditSnapshot,
  values: ProductFormPatchInput,
): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (values.name.trim() !== snap.name) {
    body.name = values.name.trim()
  }
  if (values.skuCode.trim() !== snap.skuCode) {
    body.skuCode = values.skuCode.trim()
  }
  const newBc = normBarcodePatch(values.barcode)
  if (newBc !== snap.barcode) {
    body.barcode = newBc
  }
  const newCat = values.categoryId > 0 ? values.categoryId : null
  if (newCat !== snap.categoryId) {
    body.categoryId = newCat
  }
  const newDesc = normDescPatch(values.description)
  const descOld = snap.description ?? null
  if (newDesc !== descOld) {
    body.description = newDesc
  }
  const wNew = normWeightPatch(values.weight)
  const wOld = snap.weight
  if (wNew !== wOld) {
    body.weight = wNew === null ? null : wNew
  }
  if (values.status !== snap.status) {
    body.status = values.status
  }
  const priceChanged = values.salePrice !== snap.salePrice || values.costPrice !== snap.costPrice
  if (priceChanged) {
    body.salePrice = values.salePrice
    body.costPrice = values.costPrice
    const pe = (values.priceEffectiveDate ?? "").trim()
    if (pe) {
      body.priceEffectiveDate = pe
    }
  }
  return body
}

// --- Task039 — `POST /api/v1/products/{id}/images` — `docs/frontend/api/API_Task039_products_post_image.md` + SRS §4.3

/** Kích thước tối đa một ảnh phía client (khớp Spring multipart + Cloudinary mặc định 5MB). */
export const PRODUCT_IMAGE_MAX_BYTES = 5 * 1024 * 1024

export const PRODUCT_IMAGE_ALLOWED_MIME = new Set(["image/jpeg", "image/png", "image/webp"])

export type ProductImageDto = {
  id: number
  productId: number
  url: string
  sortOrder: number
  isPrimary: boolean
}

export type PostProductImageJsonBody = {
  url: string
  sortOrder?: number
  isPrimary?: boolean
}

export function postProductImageJson(productId: number, body: PostProductImageJsonBody) {
  return apiJson<ProductImageDto>(`/api/v1/products/${productId}/images`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({
      url: body.url,
      sortOrder: body.sortOrder ?? 0,
      isPrimary: body.isPrimary ?? false,
    }),
  })
}

export type PostProductImageMultipartOptions = {
  sortOrder?: number
  isPrimary?: boolean
}

export function postProductImageMultipart(
  productId: number,
  file: File,
  options: PostProductImageMultipartOptions = {},
) {
  return apiFormData<ProductImageDto>(`/api/v1/products/${productId}/images`, () => {
    const form = new FormData()
    form.append("file", file)
    if (options.sortOrder != null) {
      form.append("sortOrder", String(options.sortOrder))
    }
    if (options.isPrimary != null) {
      form.append("isPrimary", String(options.isPrimary))
    }
    return form
  }, { method: "POST", auth: true })
}

// --- Task041 — `POST /api/v1/products/bulk-delete` — `docs/frontend/api/API_Task041_products_bulk_delete.md` + SRS §8.8 (Owner-only xóa).

export type ProductsBulkDeleteDto = {
  deletedIds: number[]
  deletedCount: number
}

export function postProductsBulkDelete(ids: number[]) {
  return apiJson<ProductsBulkDeleteDto>("/api/v1/products/bulk-delete", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ ids }),
  })
}

/** Task035 — `POST /api/v1/products` — `docs/frontend/api/API_Task035_products_post.md`. */
export type ProductCreateBody = {
  skuCode: string
  name: string
  barcode?: string | null
  categoryId?: number | null
  description?: string | null
  weight?: number | null
  status?: string
  imageUrl?: string | null
  baseUnitName: string
  costPrice: number
  salePrice: number
  priceEffectiveDate?: string | null
}

export type ProductCreatedDto = {
  id: number
  skuCode: string
  barcode: string | null
  name: string
  categoryId: number | null
  categoryName: string | null
  imageUrl: string | null
  status: string
  currentStock: number
  currentPrice: number | string | null
  createdAt: string
  updatedAt: string
  unitId: number
}

/** Ảnh chỉ gửi khi bấm Lưu — BR-10 / SRS §14 (state cục bộ trên form). */
export type StagedProductImages = {
  files: File[]
  urlAdds: { url: string; sortOrder: number; isPrimary: boolean }[]
}

/**
 * Tổng dung lượng các part `file` trong một `POST /api/v1/products` multipart
 * phải thấp hơn `spring.servlet.multipart.max-request-size` (server) trừ metadata.
 */
export const PRODUCT_CREATE_STAGED_FILES_MAX_TOTAL_BYTES = 65 * 1024 * 1024

/** Trả về thông báo lỗi tiếng Việt hoặc `null` nếu OK. */
export function getStagedProductFilesTotalSizeError(files: File[]): string | null {
  if (files.length === 0) return null
  const total = files.reduce((s, f) => s + f.size, 0)
  if (total > PRODUCT_CREATE_STAGED_FILES_MAX_TOTAL_BYTES) {
    const mb = (total / (1024 * 1024)).toFixed(1)
    const maxMb = Math.floor(PRODUCT_CREATE_STAGED_FILES_MAX_TOTAL_BYTES / (1024 * 1024))
    return `Tổng dung lượng ảnh (${mb} MB) vượt giới hạn một lần tạo (~${maxMb} MB). Hãy bớt ảnh hoặc giảm kích thước từng file.`
  }
  return null
}

export type ProductCreateFormValues = {
  skuCode: string
  name: string
  barcode?: string
  categoryId?: number
  description?: string
  weight?: number
  status: string
  baseUnitName: string
  costPrice: number
  salePrice: number
  priceEffectiveDate?: string
}

export function buildProductCreateBody(values: ProductCreateFormValues): ProductCreateBody {
  const barcode = values.barcode?.trim()
  const description = values.description?.trim()
  const body: ProductCreateBody = {
    skuCode: values.skuCode.trim(),
    name: values.name.trim(),
    barcode: barcode ? barcode : null,
    categoryId: values.categoryId != null && values.categoryId > 0 ? values.categoryId : null,
    description: description ? description : null,
    weight: values.weight != null && values.weight > 0 ? values.weight : null,
    status: values.status?.trim() || "Active",
    imageUrl: null,
    baseUnitName: values.baseUnitName.trim(),
    costPrice: values.costPrice,
    salePrice: values.salePrice,
  }
  const pe = values.priceEffectiveDate?.trim()
  if (pe) {
    body.priceEffectiveDate = pe
  }
  return body
}

export function postProduct(body: ProductCreateBody) {
  return apiJson<ProductCreatedDto>("/api/v1/products", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

/**
 * Task035 + SRS §14 — `POST /api/v1/products` `multipart/form-data`: part `metadata` (JSON) + nhiều part `file`.
 * Upload song song phía server; cần Cloudinary bật nếu gửi file.
 */
export function postProductCreateMultipart(
  body: ProductCreateBody,
  files: File[],
  options: { primaryImageIndex?: number } = {},
) {
  const { primaryImageIndex = 0 } = options
  return apiFormData<ProductCreatedDto>("/api/v1/products", () => {
    const form = new FormData()
    const metaBlob = new Blob([JSON.stringify(body)], { type: "application/json" })
    form.append("metadata", metaBlob, "metadata.json")
    for (const f of files) {
      form.append("file", f)
    }
    form.append("primaryImageIndex", String(primaryImageIndex))
    return form
  }, { method: "POST", auth: true })
}
