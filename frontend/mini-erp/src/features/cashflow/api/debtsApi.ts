import { apiJson } from "@/lib/api/http"
import type { PartnerDebt } from "../types"

export const DEBTS_LIST_QUERY_KEY = ["debts", "list"] as const
export const DEBT_DETAIL_QUERY_KEY = ["debts", "detail"] as const

export type DebtListPageDto = {
  items: PartnerDebt[]
  page: number
  limit: number
  total: number
}

export type PartnerDebtItemDto = PartnerDebt

export type GetDebtsListParams = {
  partnerType?: "Customer" | "Supplier"
  status?: "InDebt" | "Cleared"
  search?: string
  dueDateFrom?: string
  dueDateTo?: string
  page?: number
  limit?: number
}

export type DebtCreateBody = {
  partnerType: "Customer" | "Supplier"
  customerId?: number | null
  supplierId?: number | null
  totalAmount: number
  paidAmount?: number
  dueDate?: string | null
  notes?: string | null
}

export function getDebtsList(params: GetDebtsListParams = {}) {
  const q = new URLSearchParams()
  if (params.partnerType) q.set("partnerType", params.partnerType)
  if (params.status) q.set("status", params.status)
  if (params.search?.trim()) q.set("search", params.search.trim())
  if (params.dueDateFrom?.trim()) q.set("dueDateFrom", params.dueDateFrom.trim())
  if (params.dueDateTo?.trim()) q.set("dueDateTo", params.dueDateTo.trim())
  q.set("page", String(params.page ?? 1))
  q.set("limit", String(params.limit ?? 20))

  const qs = q.toString()
  return apiJson<DebtListPageDto>(`/api/v1/debts${qs ? `?${qs}` : ""}`, {
    method: "GET",
    auth: true,
  })
}

export function postDebt(body: DebtCreateBody) {
  return apiJson<PartnerDebt>("/api/v1/debts", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function getDebtById(id: number) {
  return apiJson<PartnerDebt>(`/api/v1/debts/${id}`, {
    method: "GET",
    auth: true,
  })
}

export function patchDebt(id: number, body: Record<string, unknown>) {
  return apiJson<PartnerDebt>(`/api/v1/debts/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}
