import { apiJson } from "@/lib/api/http"

export type InventoryDraftColumn = {
  key: string
  label?: string
  type?: string
  required?: boolean
}

export type InventoryDraftLine = {
  lineId: string
  values: Record<string, unknown>
}

export type ReceiptDraftHeader = {
  supplierName?: string
  supplierCode?: string
  receiptDate?: string
  invoiceNumber?: string
  notes?: string
  saveMode?: "draft" | "pending"
}

export type InventoryReceiptDraftPayload = {
  draftId: string
  entityType: string
  header: ReceiptDraftHeader
  lineColumns: InventoryDraftColumn[]
  lines: InventoryDraftLine[]
  status?: string
  previewMessage?: string
}

export type InventoryDraftResponseDto = {
  id: string
  entityType: string
  status: string
  header: ReceiptDraftHeader
  lineColumns: InventoryDraftColumn[]
  lines: InventoryDraftLine[]
  meta?: Record<string, unknown>
  commitResult?: unknown
  conversationId?: string | null
  createdAt?: string
  updatedAt?: string
  expiresAt?: string
}

export type InventoryDraftCommitResultDto = {
  success: boolean
  message?: string
  createdReceiptId?: number | null
  receiptCode?: string | null
  draft?: InventoryDraftResponseDto
}

export function getInventoryDraft(draftId: string) {
  return apiJson<InventoryDraftResponseDto>(`/api/v1/ai/inventory-drafts/${draftId}`, {
    method: "GET",
    auth: true,
  })
}

export function patchInventoryDraft(
  draftId: string,
  lines: InventoryDraftLine[],
  header?: ReceiptDraftHeader,
  lineColumns?: InventoryDraftColumn[]
) {
  const body: {
    lines: InventoryDraftLine[]
    header?: ReceiptDraftHeader
    lineColumns?: InventoryDraftColumn[]
  } = { lines }
  if (header) body.header = header
  if (lineColumns?.length) body.lineColumns = lineColumns
  return apiJson<InventoryDraftResponseDto>(`/api/v1/ai/inventory-drafts/${draftId}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function commitInventoryDraft(draftId: string) {
  return apiJson<InventoryDraftCommitResultDto>(
    `/api/v1/ai/inventory-drafts/${draftId}/commit`,
    {
      method: "POST",
      auth: true,
      body: JSON.stringify({}),
    }
  )
}

export function deleteInventoryDraft(draftId: string) {
  return apiJson<void>(`/api/v1/ai/inventory-drafts/${draftId}`, {
    method: "DELETE",
    auth: true,
  })
}
