import { apiJson } from "@/lib/api/http"
import type { Category } from "../types"

/** Task029 — `GET /api/v1/categories` — `docs/frontend/api/API_Task029_categories_get_list.md`. */
export type CategoryNodeDto = {
  id: number
  categoryCode: string
  name: string
  description: string | null
  parentId: number | null
  sortOrder: number
  status: string
  productCount: number
  createdAt: string
  updatedAt: string
  children?: CategoryNodeDto[] | null
}

export type CategoryListData = {
  items: CategoryNodeDto[]
}

export type CategoryBreadcrumbItemDto = {
  id: number
  name: string
  categoryCode: string
}

/** Task031 — `GET /api/v1/categories/{id}`. */
export type CategoryDetailDto = {
  id: number
  categoryCode: string
  name: string
  description: string | null
  parentId: number | null
  parentName: string | null
  sortOrder: number
  status: string
  productCount: number
  createdAt: string
  updatedAt: string
  breadcrumb: CategoryBreadcrumbItemDto[] | null
}

export type GetCategoryListParams = {
  format?: "tree" | "flat"
  search?: string
  status?: "all" | "Active" | "Inactive"
}

export function mapNodeDtoToCategory(d: CategoryNodeDto): Category {
  const children = d.children?.length ? d.children.map(mapNodeDtoToCategory) : undefined
  return {
    id: d.id,
    categoryCode: d.categoryCode,
    name: d.name,
    description: d.description ?? undefined,
    parentId: d.parentId ?? undefined,
    sortOrder: d.sortOrder,
    status: d.status as Category["status"],
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
    productCount: typeof d.productCount === "number" ? d.productCount : Number(d.productCount),
    children,
  }
}

export function mapDetailDtoToCategory(d: CategoryDetailDto): Category {
  const breadcrumb =
    d.breadcrumb?.length ?
      d.breadcrumb.map((b) => ({
        id: b.id,
        name: b.name,
        categoryCode: b.categoryCode,
      }))
    : undefined
  return {
    id: d.id,
    categoryCode: d.categoryCode,
    name: d.name,
    description: d.description ?? undefined,
    parentId: d.parentId ?? undefined,
    parentName: d.parentName?.trim() ? d.parentName : undefined,
    sortOrder: d.sortOrder,
    status: d.status as Category["status"],
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
    productCount: typeof d.productCount === "number" ? d.productCount : Number(d.productCount),
    breadcrumb,
  }
}

export function getCategoryList(params: GetCategoryListParams = {}) {
  const q = new URLSearchParams()
  q.set("format", params.format ?? "tree")
  if (params.search?.trim()) {
    q.set("search", params.search.trim())
  }
  if (params.status && params.status !== "all") {
    q.set("status", params.status)
  }
  const qs = q.toString()
  return apiJson<CategoryListData>(`/api/v1/categories?${qs}`, { method: "GET", auth: true })
}

export function getCategoryById(id: number) {
  return apiJson<CategoryDetailDto>(`/api/v1/categories/${id}`, { method: "GET", auth: true })
}

export type CategoryCreateBody = {
  categoryCode: string
  name: string
  description?: string | null
  parentId?: number | null
  sortOrder?: number
  status?: string
}

/** Task030 — `POST /api/v1/categories` — `docs/frontend/api/API_Task030_categories_post.md`. */
export function postCategory(body: CategoryCreateBody) {
  const payload = {
    categoryCode: body.categoryCode.trim(),
    name: body.name.trim(),
    description:
      body.description == null || String(body.description).trim() === ""
        ? null
        : String(body.description).trim(),
    parentId: body.parentId != null && body.parentId > 0 ? body.parentId : null,
    sortOrder: body.sortOrder ?? 0,
    status: body.status?.trim() || "Active",
  }
  return apiJson<CategoryNodeDto>("/api/v1/categories", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  })
}

export const createCategory = postCategory

/**
 * Task032 — `PATCH /api/v1/categories/{id}` partial body — `docs/frontend/api/API_Task032_categories_patch.md` §5.
 * Gửi **ít nhất một** field đổi. JSON `null` trên một key = không đổi (BE). Xóa mô tả: gửi `description: ""` (BE chuẩn hoá empty → NULL).
 * Không dùng PATCH để kéo về gốc: không gửi `parentId: null` khi đổi cha (v1 — `CategoriesPage.buildPatchBody`).
 */
export type CategoryPatchBody = {
  categoryCode?: string
  name?: string
  /** `""` xóa mô tả lưu DB (BE `normalizeDescriptionForStore`). */
  description?: string | null
  /** Chỉ gửi khi đổi sang cha khác (số dương). Không gửi `null` để đưa về gốc. */
  parentId?: number
  sortOrder?: number
  status?: string
}

export function patchCategory(id: number, body: CategoryPatchBody) {
  return apiJson<CategoryNodeDto>(`/api/v1/categories/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

export type CategoryDeleteResult = {
  id: number
  deleted: boolean
}

/** Task033 — `DELETE /api/v1/categories/{id}` (soft delete, BE chỉ **Owner**). */
export function deleteCategory(id: number) {
  return apiJson<CategoryDeleteResult>(`/api/v1/categories/${id}`, {
    method: "DELETE",
    auth: true,
  })
}

export const deleteCategorySoft = deleteCategory
