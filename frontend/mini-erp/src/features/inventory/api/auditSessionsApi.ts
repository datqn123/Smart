import { apiJson } from "@/lib/api/http"
import type { AuditItem, AuditSession, AuditStatus } from "../types"

/**
 * Task021 — `GET /api/v1/inventory/audit-sessions` — `docs/frontend/api/API_Task021_inventory_audit_sessions_get_list.md` §5–6.
 */
export type AuditSessionListItemResponse = {
  id: number
  auditCode: string
  title: string
  auditDate: string
  status: string
  locationFilter: string | null
  categoryFilter: string | null
  createdBy: number
  createdByName: string
  completedAt: string | null
  completedByName: string | null
  createdAt: string
  updatedAt: string
  totalLines: number
  countedLines: number
  varianceLines: number
}

export type AuditSessionListData = {
  items: AuditSessionListItemResponse[]
  page: number
  limit: number
  total: number
}

export type GetAuditSessionListParams = {
  search?: string
  status?: "all" | AuditStatus
  dateFrom?: string
  dateTo?: string
  page?: number
  limit?: number
}

export function mapAuditSessionListItemToUi(row: AuditSessionListItemResponse): AuditSession {
  return {
    id: row.id,
    auditCode: row.auditCode,
    title: row.title,
    auditDate: row.auditDate,
    status: row.status as AuditStatus,
    locationFilter: row.locationFilter ?? undefined,
    categoryFilter: row.categoryFilter ?? undefined,
    createdBy: row.createdBy,
    createdByName: row.createdByName?.trim() ? row.createdByName : "—",
    completedAt: row.completedAt ?? undefined,
    completedByName: row.completedByName ?? undefined,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
    items: [],
    totalLines: row.totalLines,
    countedLines: row.countedLines,
    varianceLines: row.varianceLines,
  }
}

export function getAuditSessionList(params: GetAuditSessionListParams) {
  const q = new URLSearchParams()
  if (params.search) {
    q.set("search", params.search)
  }
  if (params.status && params.status !== "all") {
    q.set("status", params.status)
  }
  if (params.dateFrom) {
    q.set("dateFrom", params.dateFrom)
  }
  if (params.dateTo) {
    q.set("dateTo", params.dateTo)
  }
  if (params.page != null) {
    q.set("page", String(params.page))
  }
  if (params.limit != null) {
    q.set("limit", String(params.limit))
  }
  const qs = q.toString()
  return apiJson<AuditSessionListData>(qs ? `/api/v1/inventory/audit-sessions?${qs}` : "/api/v1/inventory/audit-sessions", {
    method: "GET",
    auth: true,
  })
}

/**
 * Task022 — `POST /api/v1/inventory/audit-sessions` — `docs/frontend/api/API_Task022_inventory_audit_sessions_post.md` §5–6.
 */
export type AuditScopeCreateBody =
  | { mode: "by_location_ids"; locationIds: number[] }
  | { mode: "by_category_id"; categoryId: number }
  | { mode: "by_inventory_ids"; inventoryIds: number[] }

export type AuditSessionCreateBody = {
  title: string
  auditDate: string
  notes?: string | null
  scope: AuditScopeCreateBody
}

/**
 * Task023 — `GET /api/v1/inventory/audit-sessions/{id}` — `docs/frontend/api/API_Task023_inventory_audit_sessions_get_by_id.md` §6.
 * Cũng là body `data` của `POST` Task022 (201).
 */
export type AuditSessionLineItemResponse = {
  id: number
  auditSessionId: number
  inventoryId: number
  productId: number
  productName: string
  skuCode: string
  unitName: string
  locationId: number
  warehouseCode: string
  shelfCode: string
  batchNumber: string | null
  systemQuantity: number | string
  actualQuantity: number | string | null
  variance: number | string
  variancePercent: number | string | null
  isCounted: boolean
  notes: string | null
}

export type AuditSessionEventItemResponse = {
  id: number
  eventType: string
  payload?: string | null
  createdBy: number
  createdAt: string
}

export type AuditSessionDetailData = {
  id: number
  auditCode: string
  title: string
  auditDate: string
  status: string
  locationFilter: string | null
  categoryFilter: string | null
  notes: string | null
  createdBy: number
  createdByName: string
  completedAt: string | null
  completedByName: string | null
  cancelReason?: string | null
  createdAt: string
  updatedAt: string
  ownerNotes?: string | null
  events?: AuditSessionEventItemResponse[] | null
  items: AuditSessionLineItemResponse[] | null
}

function asNum(v: number | string | null | undefined, fallback = 0): number {
  if (v == null || v === "") return fallback
  return typeof v === "number" ? v : Number(v)
}

export function mapAuditSessionLineToAuditItem(row: AuditSessionLineItemResponse): AuditItem {
  const actualQty = row.actualQuantity == null || row.actualQuantity === "" ? undefined : asNum(row.actualQuantity)
  return {
    id: row.id,
    auditSessionId: row.auditSessionId,
    productId: row.productId,
    productName: row.productName,
    skuCode: row.skuCode,
    unitName: row.unitName?.trim() ? row.unitName : "—",
    locationId: row.locationId,
    warehouseCode: row.warehouseCode,
    shelfCode: row.shelfCode,
    batchNumber: row.batchNumber ?? undefined,
    systemQuantity: asNum(row.systemQuantity),
    actualQuantity: actualQty,
    variance: asNum(row.variance),
    variancePercent: row.variancePercent == null || row.variancePercent === "" ? 0 : asNum(row.variancePercent),
    isCounted: row.isCounted,
    notes: row.notes ?? undefined,
  }
}

export function mapAuditSessionDetailToUi(d: AuditSessionDetailData): AuditSession {
  return {
    id: d.id,
    auditCode: d.auditCode,
    title: d.title,
    auditDate: d.auditDate,
    status: d.status as AuditStatus,
    locationFilter: d.locationFilter ?? undefined,
    categoryFilter: d.categoryFilter ?? undefined,
    notes: d.notes ?? undefined,
    createdBy: d.createdBy,
    createdByName: d.createdByName?.trim() ? d.createdByName : "—",
    completedAt: d.completedAt ?? undefined,
    completedByName: d.completedByName ?? undefined,
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
    items: (d.items ?? []).map(mapAuditSessionLineToAuditItem),
  }
}

export function getAuditSessionById(id: number) {
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${id}`, {
    method: "GET",
    auth: true,
  })
}

/**
 * Task024 — `PATCH /api/v1/inventory/audit-sessions/{id}` — `docs/frontend/api/API_Task024_inventory_audit_sessions_patch.md` §5–6.
 * BE: `AuditSessionPatchRequest` — chỉ gửi field có cập nhật (ít nhất một).
 */
export type AuditSessionPatchBody = Partial<{
  title: string
  notes: string | null
  ownerNotes: string | null
  status: string
}>

export function patchAuditSession(id: number, body: AuditSessionPatchBody) {
  const payload: Record<string, string | null> = {}
  if (body.title !== undefined) payload.title = body.title
  if (body.notes !== undefined) payload.notes = body.notes
  if (body.ownerNotes !== undefined) payload.ownerNotes = body.ownerNotes
  if (body.status !== undefined) payload.status = body.status
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  })
}

/**
 * Task025 — `PATCH /api/v1/inventory/audit-sessions/{id}/lines` — `docs/frontend/api/API_Task025_inventory_audit_sessions_patch_lines.md` §5–6.
 * BE: `AuditLinesPatchRequest` / `AuditLinePatchRow` (`lineId`, `actualQuantity`, `notes`).
 */
export type AuditLinePatchRowBody = {
  lineId: number
  actualQuantity: number
  notes?: string | null
}

export type AuditLinesPatchBody = {
  lines: AuditLinePatchRowBody[]
}

export function patchAuditSessionLines(sessionId: number, body: AuditLinesPatchBody) {
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${sessionId}/lines`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

/**
 * Task026 — `POST /api/v1/inventory/audit-sessions/{id}/complete` — `docs/frontend/api/API_Task026_inventory_audit_sessions_complete.md` §5–6.
 * BE: chỉ khi **In Progress** → chuyển **Pending Owner Approval** (gửi chờ Owner), không set Completed tại bước này.
 */
export type AuditSessionCompleteBody = {
  requireAllCounted?: boolean
}

export function postAuditSessionComplete(sessionId: number, body: AuditSessionCompleteBody = {}) {
  const requireAllCounted = body.requireAllCounted !== false
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${sessionId}/complete`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({ requireAllCounted }),
  })
}

/**
 * Task027 — `POST /api/v1/inventory/audit-sessions/{id}/cancel` — `docs/frontend/api/API_Task027_inventory_audit_sessions_cancel.md` §4.
 * BE: `AuditSessionCancelRequest` — `cancelReason` bắt buộc, max 1000 ký tự.
 */
export type AuditSessionCancelBody = {
  cancelReason: string
}

export function postAuditSessionCancel(sessionId: number, body: AuditSessionCancelBody) {
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${sessionId}/cancel`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({ cancelReason: body.cancelReason.trim() }),
  })
}

/**
 * GAP SRS Task030 — `POST …/{id}/approve` — BE: `AuditSessionApproveRequest` (`notes` tuỳ chọn max 500); `assertOwnerOnly`.
 */
export type AuditSessionOwnerNotesBody = {
  notes?: string | null
}

export function postAuditSessionApprove(sessionId: number, body: AuditSessionOwnerNotesBody = {}) {
  const n = body.notes?.trim()
  const payload = n && n.length > 0 ? { notes: n.slice(0, 500) } : {}
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${sessionId}/approve`, {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  })
}

/** GAP SRS Task031 — `POST …/{id}/reject` — BE: `AuditSessionRejectRequest` (`notes` tuỳ chọn); `assertOwnerOnly`. */
export function postAuditSessionReject(sessionId: number, body: AuditSessionOwnerNotesBody = {}) {
  const n = body.notes?.trim()
  const payload = n && n.length > 0 ? { notes: n.slice(0, 500) } : {}
  return apiJson<AuditSessionDetailData>(`/api/v1/inventory/audit-sessions/${sessionId}/reject`, {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  })
}

/**
 * GAP SRS Task029 — `DELETE …/{id}` — xóa mềm; BE: `assertOwnerOnly`; 200 `data: null`.
 */
export function deleteAuditSessionSoft(sessionId: number) {
  return apiJson<null>(`/api/v1/inventory/audit-sessions/${sessionId}`, {
    method: "DELETE",
    auth: true,
  })
}

export function postAuditSession(body: AuditSessionCreateBody) {
  const payload = {
    title: body.title.trim(),
    auditDate: body.auditDate,
    notes: body.notes == null || String(body.notes).trim() === "" ? null : String(body.notes).trim(),
    scope: body.scope,
  }
  return apiJson<AuditSessionDetailData>("/api/v1/inventory/audit-sessions", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  })
}
