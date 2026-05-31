import { apiJson, type ApiRequestError } from "@/lib/api/http"
import type { Customer } from "../types"

/** Query key prefix — list (Task048) + `invalidateQueries` sau DELETE/mutations. */
export const CUSTOMER_LIST_QUERY_KEY = ["product-management", "customers", "list"] as const

/** Task048 — `GET /api/v1/customers` — `docs/frontend/api/API_Task048_customers_get_list.md` + BE `CustomerJdbcRepository.resolveListOrderBy`. */
export const CUSTOMER_LIST_SORT_WHITELIST = [
  "name:asc",
  "name:desc",
  "customerCode:asc",
  "customerCode:desc",
  "updatedAt:asc",
  "updatedAt:desc",
  "createdAt:asc",
  "createdAt:desc",
  "loyaltyPoints:asc",
  "loyaltyPoints:desc",
] as const

export type CustomerListSort = (typeof CUSTOMER_LIST_SORT_WHITELIST)[number]

export type CustomerListItemDto = {
  id: number
  customerCode: string
  name: string
  phone: string
  email: string | null
  address: string | null
  loyaltyPoints: number
  totalSpent: number | string
  orderCount: number
  status: string
  createdAt: string
  updatedAt: string
}

export type CustomerListPageDto = {
  items: CustomerListItemDto[]
  page: number
  limit: number
  total: number
}

export type GetCustomerListParams = {
  search?: string
  status?: "all" | "Active" | "Inactive"
  page?: number
  limit?: number
  sort?: CustomerListSort
}

export function mapCustomerListItemDtoToCustomer(d: CustomerListItemDto): Customer {
  const totalSpentRaw = d.totalSpent
  const totalSpent = typeof totalSpentRaw === "number" ? totalSpentRaw : Number(totalSpentRaw)
  return {
    id: d.id,
    customerCode: d.customerCode,
    name: d.name,
    phone: d.phone,
    email: d.email ?? undefined,
    address: d.address ?? undefined,
    loyaltyPoints: d.loyaltyPoints,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
    totalSpent: Number.isFinite(totalSpent) ? totalSpent : 0,
    orderCount: typeof d.orderCount === "number" ? d.orderCount : Number(d.orderCount),
  }
}

export function getCustomerList(params: GetCustomerListParams = {}) {
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
  return apiJson<CustomerListPageDto>(`/api/v1/customers?${q.toString()}`, { method: "GET", auth: true })
}

// --- Task050 — `GET /api/v1/customers/{id}` — `docs/frontend/api/API_Task050_customers_get_by_id.md`
export type CustomerDetailDto = {
  id: number
  customerCode: string
  name: string
  phone: string
  email: string | null
  address: string | null
  loyaltyPoints: number
  totalSpent: number | string
  orderCount: number
  status: string
  createdAt: string
  updatedAt: string
}

export function mapCustomerDetailDtoToCustomer(d: CustomerDetailDto): Customer {
  const totalSpentRaw = d.totalSpent
  const totalSpent =
    typeof totalSpentRaw === "number" ? totalSpentRaw : Number(totalSpentRaw)
  return {
    id: d.id,
    customerCode: d.customerCode,
    name: d.name,
    phone: d.phone,
    email: d.email ?? undefined,
    address: d.address ?? undefined,
    loyaltyPoints: d.loyaltyPoints,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
    totalSpent: Number.isFinite(totalSpent) ? totalSpent : 0,
    orderCount: Number(d.orderCount),
  }
}

export function getCustomerById(id: number) {
  return apiJson<CustomerDetailDto>(`/api/v1/customers/${id}`, { method: "GET", auth: true })
}

// --- Task049 — `POST /api/v1/customers` — `docs/frontend/api/API_Task049_customers_post.md`

export type CustomerCreateBody = {
  customerCode: string
  name: string
  phone: string
  email?: string | null
  address?: string | null
  status?: string
}

export function buildCustomerCreateBody(input: {
  customerCode: string
  name: string
  phone: string
  email?: string
  address?: string
  status: "Active" | "Inactive"
}): CustomerCreateBody {
  const emailTrim = input.email?.trim() ?? ""
  return {
    customerCode: input.customerCode.trim(),
    name: input.name.trim(),
    phone: input.phone.trim(),
    email: emailTrim.length > 0 ? emailTrim : null,
    address: input.address?.trim() ? input.address.trim() : null,
    status: input.status,
  }
}

export function postCustomer(body: CustomerCreateBody) {
  return apiJson<CustomerDetailDto>("/api/v1/customers", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

type CustomerCreateFormField =
  | "customerCode"
  | "name"
  | "phone"
  | "email"
  | "address"
  | "status"
  | "loyaltyPoints"
const CREATE_FORM_FIELDS = new Set<CustomerCreateFormField>([
  "customerCode",
  "name",
  "phone",
  "email",
  "address",
  "status",
  "loyaltyPoints",
])

/**
 * 400: `details` theo field (BE validation / `BusinessException`).
 * 409: trùng mã KH — `details.field` = `"customerCode"` + `message` chính.
 */
export function applyCustomerCreateApiError(
  setError: (name: CustomerCreateFormField, err: { message: string }) => void,
  e: ApiRequestError,
): number {
  const d = e.body?.details
  const msg = e.body?.message ?? e.message
  if (e.status === 409 && d && typeof d === "object") {
    const field = (d as Record<string, unknown>)["field"]
    if (typeof field === "string" && CREATE_FORM_FIELDS.has(field as CustomerCreateFormField)) {
      setError(field as CustomerCreateFormField, { message: msg })
      return 1
    }
  }
  if (e.status === 400 && d && typeof d === "object" && d !== null) {
    let n = 0
    for (const [key, val] of Object.entries(d as Record<string, unknown>)) {
      if (CREATE_FORM_FIELDS.has(key as CustomerCreateFormField) && val != null && String(val).length > 0) {
        setError(key as CustomerCreateFormField, { message: String(val) })
        n += 1
      }
    }
    return n
  }
  return 0
}

// --- Task051 — `PATCH /api/v1/customers/{id}` — `docs/frontend/api/API_Task051_customers_patch.md`

export type CustomerEditSnapshot = {
  customerCode: string
  name: string
  phone: string
  email: string | null
  address: string | null
  status: "Active" | "Inactive"
  loyaltyPoints: number
}

export function customerEditSnapshotFromDetail(d: CustomerDetailDto): CustomerEditSnapshot {
  return {
    customerCode: d.customerCode,
    name: d.name,
    phone: d.phone,
    email: d.email,
    address: d.address,
    status: d.status === "Inactive" ? "Inactive" : "Active",
    loyaltyPoints: d.loyaltyPoints,
  }
}

export function customerEditSnapshotFromListRow(c: Customer): CustomerEditSnapshot {
  return {
    customerCode: c.customerCode,
    name: c.name,
    phone: c.phone,
    email: c.email ?? null,
    address: c.address ?? null,
    status: c.status,
    loyaltyPoints: c.loyaltyPoints,
  }
}

/** Cùng shape form — `loyaltyPoints` chỉ đưa vào PATCH khi `includeLoyaltyPoints` (Staff: ẩn field → không gửi). */
export type CustomerFormPatchInput = {
  customerCode: string
  name: string
  phone: string
  email?: string
  address?: string
  status: "Active" | "Inactive"
  loyaltyPoints?: number
}

export function buildCustomerPatchBody(
  snap: CustomerEditSnapshot,
  data: CustomerFormPatchInput,
  opts: { includeLoyaltyPoints: boolean },
): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (data.customerCode.trim() !== snap.customerCode) {
    body.customerCode = data.customerCode.trim()
  }
  if (data.name.trim() !== snap.name) {
    body.name = data.name.trim()
  }
  if (data.phone.trim() !== snap.phone) {
    body.phone = data.phone.trim()
  }
  const emailVal = (data.email ?? "").trim() === "" ? null : (data.email ?? "").trim()
  if (emailVal !== (snap.email ?? null)) {
    body.email = emailVal
  }
  const addrVal = (data.address ?? "").trim() === "" ? null : (data.address ?? "").trim()
  if (addrVal !== (snap.address ?? null)) {
    body.address = addrVal
  }
  if (data.status !== snap.status) {
    body.status = data.status
  }
  if (
    opts.includeLoyaltyPoints &&
    data.loyaltyPoints !== undefined &&
    data.loyaltyPoints !== snap.loyaltyPoints
  ) {
    body.loyaltyPoints = data.loyaltyPoints
  }
  return body
}

export function patchCustomer(id: number, body: Record<string, unknown>) {
  return apiJson<CustomerDetailDto>(`/api/v1/customers/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

// --- Task052 — `DELETE /api/v1/customers/{id}` — `docs/frontend/api/API_Task052_customers_delete.md`

export type CustomerDeleteDto = {
  id: number
  deleted: boolean
}

export function deleteCustomer(id: number) {
  return apiJson<CustomerDeleteDto>(`/api/v1/customers/${id}`, { method: "DELETE", auth: true })
}

// --- Task053 — `POST /api/v1/customers/bulk-delete` — `docs/frontend/api/API_Task053_customers_bulk_delete.md`

export type CustomerBulkDeleteDto = {
  deletedIds: number[]
  deletedCount: number
}

/** Body `{ ids }` — BE dedupe + tối đa 50 id duy nhất; có thể gửi `[...new Set(ids)]` trước. */
export function postCustomersBulkDelete(ids: number[]) {
  return apiJson<CustomerBulkDeleteDto>("/api/v1/customers/bulk-delete", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ ids }),
  })
}
