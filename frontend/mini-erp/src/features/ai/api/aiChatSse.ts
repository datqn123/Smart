import { getApiUrl } from "@/lib/api/config"
import type { AiInteractionMode } from "../types"
import type { CatalogDraftTablePayload } from "./aiCatalogDraftApi"
import type { InventoryReceiptDraftPayload } from "./aiInventoryDraftApi"
import type { DomainClarifyPayload } from "./aiDomainClarifyTypes"
import type { QueryTablePayload } from "./aiQueryTableTypes"

type OpenAiChatStreamArgs = {
  query: string
  conversationId: string
  interactionMode?: AiInteractionMode
  onDelta: (delta: string) => void
  onDone: () => void
  onError: (message: string) => void
  /** When FastAPI emits SSE `chart` (JSON one line). */
  onChart?: (spec: Record<string, unknown>) => void
  /** When FastAPI emits SSE `draft` (catalog HITL table). */
  onDraft?: (payload: CatalogDraftTablePayload) => void
  /** When FastAPI emits SSE `inventory_draft` (stock receipt HITL). */
  onInventoryDraft?: (payload: InventoryReceiptDraftPayload) => void
  /** When FastAPI emits SSE `data_table` (read-only SQL rows). */
  onDataTable?: (payload: QueryTablePayload) => void
  /** When FastAPI emits SSE `clarify` (domain guard — scope/terminology). */
  onClarify?: (payload: DomainClarifyPayload) => void
}

export type AiChatStreamHandle = { abort: () => void }

function parseSseBlock(block: string): { event: string; data: string } | null {
  let event = ""
  const dataLines: string[] = []
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim()
    } else if (line.startsWith("data:")) {
      let d = line.slice(5)
      if (d.startsWith(" ")) d = d.slice(1)
      dataLines.push(d)
    }
  }
  if (!event) return null
  return { event, data: dataLines.join("\n") }
}

function parseClarifyPayload(raw: string): DomainClarifyPayload | null {
  try {
    const c = JSON.parse(raw) as DomainClarifyPayload
    if (c && Array.isArray(c.questions)) return c
  } catch {
    /* ignore */
  }
  return null
}

function parseQueryTablePayload(raw: string): QueryTablePayload | null {
  try {
    const table = JSON.parse(raw) as QueryTablePayload
    if (table && Array.isArray(table.columns) && Array.isArray(table.rows)) {
      return table
    }
  } catch {
    /* ignore */
  }
  return null
}

/**
 * POST + Bearer → Spring relay → FastAPI; SSE events `delta` | `clarify` | `chart` | `draft` | `data_table` | `done` | `error`.
 */
export function startAiChatPostStream(args: OpenAiChatStreamArgs): AiChatStreamHandle {
  const ac = new AbortController()

  void (async () => {
    try {
      const token = sessionStorage.getItem("accessToken")
      const url = getApiUrl("/api/v1/ai/chat/stream")
      const res = await fetch(url, {
        method: "POST",
        signal: ac.signal,
        headers: {
          "Content-Type": "application/json",
          ...(token?.trim() ? { Authorization: `Bearer ${token}` } : {}),
          "X-Correlation-Id": crypto.randomUUID(),
        },
        body: JSON.stringify({
          message: args.query,
          conversationId: args.conversationId,
          ...(args.interactionMode && args.interactionMode !== "auto"
            ? { interactionMode: args.interactionMode }
            : {}),
        }),
      })

      if (!res.ok) {
        let msg = `HTTP ${res.status}`
        try {
          const j = (await res.json()) as { error?: { message?: string } }
          const m = j.error?.message
          if (m) msg = m
        } catch {
          /* ignore non-JSON body */
        }
        args.onError(msg)
        return
      }

      const reader = res.body?.getReader()
      if (!reader) {
        args.onError("Không đọc được stream phản hồi.")
        return
      }

      const decoder = new TextDecoder()
      let buf = ""
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        let sep: number
        while ((sep = buf.indexOf("\n\n")) !== -1) {
          const block = buf.slice(0, sep)
          buf = buf.slice(sep + 2)
          const parsed = parseSseBlock(block)
          if (!parsed) continue
          if (parsed.event === "clarify" && parsed.data.length > 0 && args.onClarify) {
            const clarify = parseClarifyPayload(parsed.data)
            if (clarify) args.onClarify(clarify)
          }
          if (parsed.event === "delta" && parsed.data.length > 0) args.onDelta(parsed.data)
          if (parsed.event === "chart" && parsed.data.length > 0 && args.onChart) {
            try {
              const spec = JSON.parse(parsed.data) as Record<string, unknown>
              if (spec && typeof spec === "object") args.onChart(spec)
            } catch {
              /* ignore malformed chart payload */
            }
          }
          if (parsed.event === "draft" && parsed.data.length > 0 && args.onDraft) {
            try {
              const draft = JSON.parse(parsed.data) as CatalogDraftTablePayload
              if (draft?.draftId) args.onDraft(draft)
            } catch {
              /* ignore malformed draft payload */
            }
          }
          if (parsed.event === "inventory_draft" && parsed.data.length > 0 && args.onInventoryDraft) {
            try {
              const inv = JSON.parse(parsed.data) as InventoryReceiptDraftPayload
              if (inv?.draftId) args.onInventoryDraft(inv)
            } catch {
              /* ignore malformed inventory draft payload */
            }
          }
          if (parsed.event === "data_table" && parsed.data.length > 0 && args.onDataTable) {
            const table = parseQueryTablePayload(parsed.data)
            if (table) args.onDataTable(table)
          }
          if (parsed.event === "done") args.onDone()
          if (parsed.event === "error") {
            args.onError(parsed.data.length > 0 ? parsed.data : "Không thể kết nối trợ lý AI.")
          }
        }
      }

      const tail = buf.trim()
      if (tail) {
        const parsed = parseSseBlock(tail)
        if (parsed?.event === "clarify" && parsed.data.length > 0 && args.onClarify) {
          const clarify = parseClarifyPayload(parsed.data)
          if (clarify) args.onClarify(clarify)
        }
        if (parsed?.event === "delta" && parsed.data.length > 0) args.onDelta(parsed.data)
        if (parsed?.event === "chart" && parsed.data.length > 0 && args.onChart) {
          try {
            const spec = JSON.parse(parsed.data) as Record<string, unknown>
            if (spec && typeof spec === "object") args.onChart(spec)
          } catch {
            /* ignore */
          }
        }
        if (parsed?.event === "draft" && parsed.data.length > 0 && args.onDraft) {
          try {
            const draft = JSON.parse(parsed.data) as CatalogDraftTablePayload
            if (draft?.draftId) args.onDraft(draft)
          } catch {
            /* ignore */
          }
        }
        if (parsed?.event === "inventory_draft" && parsed.data.length > 0 && args.onInventoryDraft) {
          try {
            const inv = JSON.parse(parsed.data) as InventoryReceiptDraftPayload
            if (inv?.draftId) args.onInventoryDraft(inv)
          } catch {
            /* ignore */
          }
        }
        if (parsed?.event === "data_table" && parsed.data.length > 0 && args.onDataTable) {
          const table = parseQueryTablePayload(parsed.data)
          if (table) args.onDataTable(table)
        }
        if (parsed?.event === "done") args.onDone()
        if (parsed?.event === "error") {
          args.onError(parsed.data.length > 0 ? parsed.data : "Không thể kết nối trợ lý AI.")
        }
      }
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === "AbortError") return
      const err = e as Error
      args.onError(err?.message || "Không thể kết nối trợ lý AI.")
    }
  })()

  return { abort: () => ac.abort() }
}
