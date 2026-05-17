import { apiJson } from "@/lib/api/http"

export type CatalogDraftColumn = {
  key: string
  label?: string
  type?: string
  required?: boolean
  options?: string[]
  ref?: string
}

export type CatalogDraftRow = {
  rowId: string
  values: Record<string, unknown>
  committedAt?: string | null
  createdEntityId?: number | null
  lastError?: string | null
}

export type CatalogDraftTablePayload = {
  draftId: string
  entityType: string
  columns: CatalogDraftColumn[]
  rows: CatalogDraftRow[]
  status?: string
  previewMessage?: string
}

export type CatalogDraftResponseDto = {
  id: string
  entityType: string
  status: string
  columns: CatalogDraftColumn[]
  rows: CatalogDraftRow[]
  meta?: Record<string, unknown>
  commitResult?: unknown
  conversationId?: string | null
  createdAt?: string
  updatedAt?: string
  expiresAt?: string
}

export type CatalogDraftRowOutcome = {
  rowId: string
  success: boolean
  createdEntityId?: number | null
  message?: string
  fieldErrors?: Record<string, string>
}

export type CatalogDraftCommitResultDto = {
  committedCount: number
  failedCount: number
  skippedCount: number
  outcomes: CatalogDraftRowOutcome[]
  draft?: CatalogDraftResponseDto
}

export function getCatalogDraft(draftId: string) {
  return apiJson<CatalogDraftResponseDto>(`/api/v1/ai/catalog-drafts/${draftId}`, {
    method: "GET",
    auth: true,
  })
}

export function patchCatalogDraft(draftId: string, rows: CatalogDraftRow[], columns?: CatalogDraftColumn[]) {
  const body: { rows: CatalogDraftRow[]; columns?: CatalogDraftColumn[] } = { rows }
  if (columns?.length) body.columns = columns
  return apiJson<CatalogDraftResponseDto>(`/api/v1/ai/catalog-drafts/${draftId}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(body),
  })
}

export function commitCatalogDraft(draftId: string) {
  return apiJson<CatalogDraftCommitResultDto>(`/api/v1/ai/catalog-drafts/${draftId}/commit`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({}),
  })
}

export function deleteCatalogDraft(draftId: string) {
  return apiJson<void>(`/api/v1/ai/catalog-drafts/${draftId}`, {
    method: "DELETE",
    auth: true,
  })
}
