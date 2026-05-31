import { apiJson } from "@/lib/api/http"

/** Task061 — `GET /api/v1/approvals/pending` — `docs/frontend/api/API_Task061_approvals_pending_get_list.md`. */
export const APPROVALS_PENDING_QUERY_KEY = ["approvals", "pending"] as const

export type ApprovalsPendingSummary = {
  totalPending: number
  byType: Record<string, number>
}

export type ApprovalsPendingItem = {
  entityType: string
  entityId: number
  transactionCode: string
  type: string
  creatorName: string
  date: string
  totalAmount: number | string
  status: string
  notes?: string | null
}

export type ApprovalsPendingPage = {
  summary: ApprovalsPendingSummary
  items: ApprovalsPendingItem[]
  page: number
  limit: number
  total: number
}

export type GetPendingApprovalsParams = {
  search?: string
  type?: string
  fromDate?: string
  toDate?: string
  page?: number
  limit?: number
}

export function getPendingApprovals(params: GetPendingApprovalsParams = {}) {
  const sp = new URLSearchParams()
  if (params.search?.trim()) sp.set("search", params.search.trim())
  if (params.type && params.type !== "all") sp.set("type", params.type)
  if (params.fromDate) sp.set("fromDate", params.fromDate)
  if (params.toDate) sp.set("toDate", params.toDate)
  if (params.page != null && params.page >= 1) sp.set("page", String(params.page))
  if (params.limit != null) sp.set("limit", String(params.limit))
  const qs = sp.toString()
  return apiJson<ApprovalsPendingPage>(qs ? `/api/v1/approvals/pending?${qs}` : "/api/v1/approvals/pending", {
    auth: true,
  })
}

/** Task062 — `GET /api/v1/approvals/history` — `docs/frontend/api/API_Task062_approvals_history_get_list.md`. */
export const APPROVALS_HISTORY_QUERY_KEY = ["approvals", "history"] as const

export type ApprovalsHistoryItem = {
  entityType: string
  entityId: number
  transactionCode: string
  type: string
  creatorName: string
  date: string
  reviewedAt: string
  totalAmount: number | string
  resolution: string
  rejectionReason?: string | null
  notes?: string | null
  reviewedByUserId?: number | null
  reviewerName?: string | null
  approvedByUserId?: number | null
  approvedAt?: string | null
}

export type ApprovalsHistoryPage = {
  items: ApprovalsHistoryItem[]
  page: number
  limit: number
  total: number
}

export type GetApprovalsHistoryParams = {
  resolution?: string
  search?: string
  type?: string
  fromDate?: string
  toDate?: string
  page?: number
  limit?: number
}

export function getApprovalsHistory(params: GetApprovalsHistoryParams = {}) {
  const sp = new URLSearchParams()
  if (params.resolution && params.resolution !== "all") sp.set("resolution", params.resolution)
  if (params.search?.trim()) sp.set("search", params.search.trim())
  if (params.type && params.type !== "all") sp.set("type", params.type)
  if (params.fromDate) sp.set("fromDate", params.fromDate)
  if (params.toDate) sp.set("toDate", params.toDate)
  if (params.page != null && params.page >= 1) sp.set("page", String(params.page))
  if (params.limit != null) sp.set("limit", String(params.limit))
  const qs = sp.toString()
  return apiJson<ApprovalsHistoryPage>(qs ? `/api/v1/approvals/history?${qs}` : "/api/v1/approvals/history", {
    auth: true,
  })
}
