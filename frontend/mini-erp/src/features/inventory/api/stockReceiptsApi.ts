import { apiJson } from "@/lib/api/http"
import type { StockReceipt } from "../types"

/** Khớp validation BE `StockReceiptRejectRequest` — lý do từ chối phải ghi rõ. */
export const STOCK_RECEIPT_REJECT_REASON_MIN_LEN = 15

/**
 * Task013 — `GET /api/v1/stock-receipts` — `docs/frontend/api/API_Task013_stock_receipts_get_list.md` §7.
 * Sort BE: `id:asc|id:desc`, `createdAt:asc|createdAt:desc` (mặc định BE khi không gửi sort: `created_at` desc).
 */
export type StockReceiptListItemResponse = {
  id: number
  receiptCode: string
  supplierId: number
  supplierName: string
  staffId: number
  staffName: string
  receiptDate: string
  status: "Draft" | "Pending" | "Approved" | "Rejected"
  invoiceNumber: string | null
  totalAmount: number | string
  lineCount: number
  notes: string | null
  approvedBy: number | null
  approvedByName: string | null
  approvedAt: string | null
  reviewedBy: number | null
  reviewedByName: string | null
  reviewedAt: string | null
  rejectionReason: string | null
  createdAt: string
  updatedAt: string
}

export type StockReceiptListData = {
  items: StockReceiptListItemResponse[]
  page: number
  limit: number
  total: number
}

export type GetStockReceiptListParams = {
  search?: string
  status?: "all" | "Draft" | "Pending" | "Approved" | "Rejected"
  dateFrom?: string
  dateTo?: string
  supplierId?: number
  /** Lọc phiếu do user JWT tạo (`staff_id` = subject); không gửi `staffId` từ client. */
  mine?: boolean
  page?: number
  limit?: number
  /** `id:asc|id:desc` hoặc `createdAt:asc|createdAt:desc`. */
  sort?: string
}

function asNumber(v: number | string): number {
  return typeof v === "number" ? v : Number(v)
}

export function mapStockReceiptListItemToUi(row: StockReceiptListItemResponse): StockReceipt {
  const lineCount = row.lineCount ?? 0
  return {
    id: row.id,
    receiptCode: row.receiptCode,
    supplierId: row.supplierId,
    supplierName: row.supplierName,
    staffId: row.staffId,
    staffName: row.staffName?.trim() ? row.staffName : "—",
    receiptDate: row.receiptDate,
    status: row.status,
    invoiceNumber: row.invoiceNumber ?? undefined,
    totalAmount: asNumber(row.totalAmount),
    notes: row.notes ?? undefined,
    approvedBy: row.approvedBy ?? undefined,
    approvedByName: row.approvedByName ?? undefined,
    approvedAt: row.approvedAt ?? undefined,
    reviewedBy: row.reviewedBy ?? undefined,
    reviewedByName: row.reviewedByName ?? undefined,
    reviewedAt: row.reviewedAt ?? undefined,
    rejectionReason: row.rejectionReason ?? undefined,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
    lineCount,
    details: [],
  }
}

export function getStockReceiptList(params: GetStockReceiptListParams) {
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
  if (params.supplierId != null && params.supplierId > 0) {
    q.set("supplierId", String(params.supplierId))
  }
  if (params.mine === true) {
    q.set("mine", "true")
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
  return apiJson<StockReceiptListData>(qs ? `/api/v1/stock-receipts?${qs}` : "/api/v1/stock-receipts", {
    method: "GET",
    auth: true,
  })
}

/** Task014 — `POST /api/v1/stock-receipts` — `docs/frontend/api/API_Task014_stock_receipts_post.md` §5–6. */
export type StockReceiptCreateSaveMode = "draft" | "pending"

export type StockReceiptCreateDetailBody = {
  productId: number
  unitId: number
  quantity: number
  costPrice: number
  batchNumber?: string | null
  expiryDate?: string | null
}

export type StockReceiptCreateBody = {
  supplierId: number
  receiptDate: string
  invoiceNumber?: string
  notes?: string
  saveMode: StockReceiptCreateSaveMode
  details: StockReceiptCreateDetailBody[]
}

export type StockReceiptLineViewResponse = {
  id: number
  receiptId: number
  productId: number
  productName: string
  skuCode: string
  unitId: number
  unitName: string
  quantity: number
  costPrice: number | string
  batchNumber: string | null
  expiryDate: string | null
  lineTotal: number | string
}

export type StockReceiptViewResponse = {
  id: number
  receiptCode: string
  supplierId: number
  supplierName: string
  staffId: number
  staffName: string
  receiptDate: string
  status: string
  invoiceNumber: string | null
  totalAmount: number | string
  notes: string | null
  approvedBy: number | null
  approvedByName: string | null
  approvedAt: string | null
  reviewedBy: number | null
  reviewedByName: string | null
  reviewedAt: string | null
  rejectionReason: string | null
  createdAt: string
  updatedAt: string
  details: StockReceiptLineViewResponse[]
}

/** Task015 — map `StockReceiptViewData` → model UI (`ReceiptDetailDialog`, form sửa). */
export function mapStockReceiptViewToUi(v: StockReceiptViewResponse): StockReceipt {
  const details = (v.details ?? []).map((d) => ({
    id: d.id,
    receiptId: d.receiptId,
    productId: d.productId,
    productName: d.productName,
    skuCode: d.skuCode,
    unitId: d.unitId,
    unitName: d.unitName,
    quantity: d.quantity,
    costPrice: asNumber(d.costPrice),
    batchNumber: d.batchNumber ?? undefined,
    expiryDate: d.expiryDate ?? undefined,
    lineTotal: asNumber(d.lineTotal),
  }))
  const lineCount = details.length
  const st = v.status
  const status: StockReceipt["status"] =
    st === "Draft" || st === "Pending" || st === "Approved" || st === "Rejected" ? st : "Draft"
  return {
    id: v.id,
    receiptCode: v.receiptCode,
    supplierId: v.supplierId,
    supplierName: v.supplierName,
    staffId: v.staffId,
    staffName: v.staffName?.trim() ? v.staffName : "—",
    receiptDate: v.receiptDate,
    status,
    invoiceNumber: v.invoiceNumber ?? undefined,
    totalAmount: asNumber(v.totalAmount),
    notes: v.notes ?? undefined,
    approvedBy: v.approvedBy ?? undefined,
    approvedByName: v.approvedByName ?? undefined,
    approvedAt: v.approvedAt ?? undefined,
    reviewedBy: v.reviewedBy ?? undefined,
    reviewedByName: v.reviewedByName ?? undefined,
    reviewedAt: v.reviewedAt ?? undefined,
    rejectionReason: v.rejectionReason ?? undefined,
    createdAt: v.createdAt,
    updatedAt: v.updatedAt,
    lineCount,
    details,
  }
}

/** Task015 — `GET /api/v1/stock-receipts/{id}` — `docs/frontend/api/API_Task015_stock_receipts_get_by_id.md` §5–6. */
export function getStockReceiptById(id: number) {
  return apiJson<StockReceiptViewResponse>(`/api/v1/stock-receipts/${id}`, {
    method: "GET",
    auth: true,
  })
}

export function postStockReceipt(body: StockReceiptCreateBody) {
  return apiJson<StockReceiptViewResponse>("/api/v1/stock-receipts", {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

/** Task016 — body khớp `StockReceiptPatchRequest` (partial; FE gửi đủ field khi lưu form Draft). */
export type StockReceiptPatchBody = {
  supplierId?: number
  receiptDate?: string
  invoiceNumber?: string | null
  notes?: string | null
  details?: StockReceiptCreateDetailBody[]
}

/** Task016 — `PATCH /api/v1/stock-receipts/{id}` — `docs/frontend/api/API_Task016_stock_receipts_patch.md` §4–5. */
export function patchStockReceipt(id: number, body: StockReceiptPatchBody) {
  return apiJson<StockReceiptViewResponse>(`/api/v1/stock-receipts/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

/** Task017 — `DELETE /api/v1/stock-receipts/{id}` — `docs/frontend/api/API_Task017_stock_receipts_delete.md`. */
export function deleteStockReceipt(id: number) {
  return apiJson<null>(`/api/v1/stock-receipts/${id}`, {
    method: "DELETE",
    auth: true,
  })
}

/** Draft → Pending — `POST /api/v1/stock-receipts/{id}/submit` — `docs/frontend/api/API_Task018_stock_receipts_submit.md`. */
export function submitStockReceipt(id: number) {
  return apiJson<StockReceiptViewResponse>(`/api/v1/stock-receipts/${id}/submit`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({}),
  })
}

export type StockReceiptApproveBody = {
  inboundLocationId: number
}

/** Pending → Approved — `POST /api/v1/stock-receipts/{id}/approve` — `docs/frontend/api/API_Task019_stock_receipts_approve.md`. RBAC BE: `can_approve` + role Admin hoặc Owner. */
export function approveStockReceipt(id: number, body: StockReceiptApproveBody) {
  return apiJson<StockReceiptViewResponse>(`/api/v1/stock-receipts/${id}/approve`, {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

export type StockReceiptRejectBody = {
  reason: string
}

/** Pending → Rejected — `POST /api/v1/stock-receipts/{id}/reject` — `docs/frontend/api/API_Task020_stock_receipts_reject.md`. RBAC BE: giống approve. */
export function rejectStockReceipt(id: number, body: StockReceiptRejectBody) {
  return apiJson<StockReceiptViewResponse>(`/api/v1/stock-receipts/${id}/reject`, {
    method: "POST",
    auth: true,
    body: JSON.stringify(body),
  })
}

/** Gợi ý chọn vị trí nhập: seed V1 `WarehouseLocations` (id 1..5). */
export const STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS: readonly { id: number; label: string }[] = [
  { id: 1, label: "WH01 · A1 — Kệ A1" },
  { id: 2, label: "WH01 · A2 — Kệ A2" },
  { id: 3, label: "WH01 · B1 — Kệ B1" },
  { id: 4, label: "WH01 · B2 — Kệ B2" },
  { id: 5, label: "WH01 · C1 — Kệ C1" },
]
