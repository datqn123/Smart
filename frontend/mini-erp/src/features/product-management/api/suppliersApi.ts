import { apiJson } from "@/lib/api/http"
import type { Supplier } from "../types"

/** Task042 — `GET /api/v1/suppliers` — `docs/frontend/api/API_Task042_suppliers_get_list.md` + SRS §8.2. */
export const SUPPLIER_LIST_SORT_WHITELIST = [
  "name:asc",
  "name:desc",
  "supplierCode:asc",
  "supplierCode:desc",
  "updatedAt:asc",
  "updatedAt:desc",
  "createdAt:asc",
  "createdAt:desc",
] as const

export type SupplierListSort = (typeof SUPPLIER_LIST_SORT_WHITELIST)[number]

export type SupplierListItemDto = {
  id: number
  supplierCode: string
  name: string
  contactPerson: string
  phone: string
  email: string | null
  address: string | null
  taxCode: string | null
  status: string
  receiptCount: number
  createdAt: string
  updatedAt: string
}

export type SupplierListPageDto = {
  items: SupplierListItemDto[]
  page: number
  limit: number
  total: number
}

export type GetSupplierListParams = {
  search?: string
  status?: "all" | "Active" | "Inactive"
  page?: number
  limit?: number
  sort?: SupplierListSort
}

export function mapSupplierListItemDtoToSupplier(d: SupplierListItemDto): Supplier {
  return {
    id: d.id,
    supplierCode: d.supplierCode,
    name: d.name,
    contactPerson: d.contactPerson,
    phone: d.phone,
    email: d.email ?? undefined,
    address: d.address ?? undefined,
    taxCode: d.taxCode ?? undefined,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    receiptCount: typeof d.receiptCount === "number" ? d.receiptCount : Number(d.receiptCount),
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
  }
}

export function getSupplierList(params: GetSupplierListParams = {}) {
  const q = new URLSearchParams()
  if (params.search?.trim()) {
    q.set("search", params.search.trim())
  }
  if (params.status && params.status !== "all") {
    q.set("status", params.status)
  }
  q.set("page", String(params.page ?? 1))
  q.set("limit", String(params.limit ?? 20))
  const sort = params.sort ?? "updatedAt:desc"
  q.set("sort", sort)
  return apiJson<SupplierListPageDto>(`/api/v1/suppliers?${q.toString()}`, { method: "GET", auth: true })
}

// --- Task043 — `POST /api/v1/suppliers` — `docs/frontend/api/API_Task043_suppliers_post.md`

export type SupplierCreateBody = {
  supplierCode: string
  name: string
  contactPerson: string
  phone: string
  email?: string | null
  address?: string | null
  taxCode?: string | null
  status?: string
}

export type SupplierDetailDto = {
  id: number
  supplierCode: string
  name: string
  contactPerson: string
  phone: string
  email: string | null
  address: string | null
  taxCode: string | null
  status: string
  receiptCount: number
  lastReceiptAt: string | null
  createdAt: string
  updatedAt: string
}

export function mapSupplierDetailDtoToSupplier(d: SupplierDetailDto): Supplier {
  return {
    id: d.id,
    supplierCode: d.supplierCode,
    name: d.name,
    contactPerson: d.contactPerson,
    phone: d.phone,
    email: d.email ?? undefined,
    address: d.address ?? undefined,
    taxCode: d.taxCode ?? undefined,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    receiptCount: Number(d.receiptCount),
    lastReceiptAt: d.lastReceiptAt ?? undefined,
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
  }
}

/** Body JSON — `Task043` + SRS. */
export function buildSupplierCreateBody(input: {
  supplierCode: string
  name: string
  contactPerson: string
  phone: string
  email?: string
  address?: string
  taxCode?: string
  status: "Active" | "Inactive"
}): SupplierCreateBody {
  const emailTrim = input.email?.trim() ?? ""
  return {
    supplierCode: input.supplierCode.trim(),
    name: input.name.trim(),
    contactPerson: input.contactPerson.trim(),
    phone: input.phone.trim(),
    email: emailTrim.length ? emailTrim : null,
    address: input.address?.trim() || null,
    taxCode: input.taxCode?.trim() || null,
    status: input.status,
  }
}

export function postSupplier(body: SupplierCreateBody) {
  return apiJson<SupplierDetailDto>("/api/v1/suppliers", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

// --- Task044 — `GET /api/v1/suppliers/{id}` — `docs/frontend/api/API_Task044_suppliers_get_by_id.md`

export function getSupplierById(id: number) {
  return apiJson<SupplierDetailDto>(`/api/v1/suppliers/${id}`, { method: "GET", auth: true })
}

// --- Task045 — `PATCH /api/v1/suppliers/{id}` — `docs/frontend/api/API_Task045_suppliers_patch.md`

/** Cùng shape với `SupplierFormData` (Zod) — tách để tránh vòng phụ thuộc với `SupplierForm`. */
export type SupplierFormPatchInput = {
  supplierCode: string
  name: string
  contactPerson: string
  phone: string
  email?: string
  address?: string
  taxCode?: string
  status: "Active" | "Inactive"
}

export type SupplierEditSnapshot = {
  supplierCode: string
  name: string
  contactPerson: string
  phone: string
  email: string | null
  address: string | null
  taxCode: string | null
  status: "Active" | "Inactive"
}

export function supplierEditSnapshotFromDetail(d: SupplierDetailDto): SupplierEditSnapshot {
  return {
    supplierCode: d.supplierCode,
    name: d.name,
    contactPerson: d.contactPerson,
    phone: d.phone,
    email: d.email,
    address: d.address,
    taxCode: d.taxCode,
    status: d.status === "Inactive" ? "Inactive" : "Active",
  }
}

export function supplierEditSnapshotFromListRow(s: Supplier): SupplierEditSnapshot {
  return {
    supplierCode: s.supplierCode,
    name: s.name,
    contactPerson: s.contactPerson ?? "",
    phone: s.phone ?? "",
    email: s.email ?? null,
    address: s.address ?? null,
    taxCode: s.taxCode ?? null,
    status: s.status,
  }
}

/**
 * Chỉ gửi field khác snapshot — `SupplierService#patch` bắt buộc ít nhất một trường hợp lệ.
 */
export function buildSupplierPatchBody(
  snap: SupplierEditSnapshot,
  data: SupplierFormPatchInput,
): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (data.supplierCode.trim() !== snap.supplierCode) {
    body.supplierCode = data.supplierCode.trim()
  }
  if (data.name.trim() !== snap.name) {
    body.name = data.name.trim()
  }
  if (data.contactPerson.trim() !== snap.contactPerson) {
    body.contactPerson = data.contactPerson.trim()
  }
  if (data.phone.trim() !== snap.phone) {
    body.phone = data.phone.trim()
  }
  const emailVal = (data.email ?? "").trim() === "" ? null : (data.email ?? "").trim()
  if (emailVal !== snap.email) {
    body.email = emailVal
  }
  const addrVal = (data.address ?? "").trim() === "" ? null : (data.address ?? "").trim()
  if (addrVal !== (snap.address ?? null)) {
    body.address = addrVal
  }
  const taxVal = (data.taxCode ?? "").trim() === "" ? null : (data.taxCode ?? "").trim()
  if (taxVal !== (snap.taxCode ?? null)) {
    body.taxCode = taxVal
  }
  if (data.status !== snap.status) {
    body.status = data.status
  }
  return body
}

export function patchSupplier(id: number, body: Record<string, unknown>) {
  return apiJson<SupplierDetailDto>(`/api/v1/suppliers/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

// --- Task046 — `DELETE /api/v1/suppliers/{id}` — `docs/frontend/api/API_Task046_suppliers_delete.md`

export type SupplierDeleteDto = {
  id: number
  deleted: boolean
}

export function deleteSupplier(id: number) {
  return apiJson<SupplierDeleteDto>(`/api/v1/suppliers/${id}`, { method: "DELETE", auth: true })
}

// --- Task047 — `POST /api/v1/suppliers/bulk-delete` — `docs/frontend/api/API_Task047_suppliers_bulk_delete.md`

export type SupplierBulkDeleteDto = {
  deletedIds: number[]
  deletedCount: number
}

/** Body `{ ids }` — tối đa 50, không trùng (BE 400 nếu trùng). Có thể gọi `[...new Set(ids)]` trước. */
export function postSuppliersBulkDelete(ids: number[]) {
  return apiJson<SupplierBulkDeleteDto>("/api/v1/suppliers/bulk-delete", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ ids }),
  })
}
