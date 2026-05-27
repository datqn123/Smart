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
  onDeltaFull?: (text: string) => void
  onDone: () => void
  onError: (message: string) => void
  /** When FastAPI emits SSE `progress` (user-facing status text). */
  onProgress?: (text: string) => void
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

export type TranscribeAudioResult = {
  transcript: string
  language?: string | null
  correlationId: string
}

export type TranscribeAudioErrorCode =
  | "network"
  | "stt_unavailable"
  | "empty_transcript"
  | "validation"
  | "unknown"

export class TranscribeAudioError extends Error {
  readonly code: TranscribeAudioErrorCode

  constructor(code: TranscribeAudioErrorCode, message: string) {
    super(message)
    this.name = "TranscribeAudioError"
    this.code = code
  }
}

/** POST multipart → Spring relay → Python STT (FPT Whisper). */
export async function transcribeAudio(
  wavBlob: Blob,
  options?: { language?: string }
): Promise<TranscribeAudioResult> {
  const token = sessionStorage.getItem("accessToken")
  const correlationId = crypto.randomUUID()
  const formData = new FormData()
  formData.append("file", wavBlob, "recording.wav")
  if (options?.language) {
    formData.append("language", options.language)
  }

  let res: Response
  try {
    res = await fetch(getApiUrl("/api/v1/ai/chat/transcribe"), {
      method: "POST",
      headers: {
        ...(token?.trim() ? { Authorization: `Bearer ${token}` } : {}),
        "X-Correlation-Id": correlationId,
      },
      body: formData,
    })
  } catch {
    throw new TranscribeAudioError("network", "Lỗi kết nối khi gửi ghi âm.")
  }

  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    let code: TranscribeAudioErrorCode = "unknown"
    try {
      const j = (await res.json()) as { error?: { message?: string; code?: string } }
      if (j.error?.message) msg = j.error.message
      if (res.status === 503 || j.error?.code === "AI_STT_UNAVAILABLE") {
        code = "stt_unavailable"
        msg = "Dịch vụ chuyển giọng thành văn bản tạm thời không khả dụng."
      } else if (res.status === 400) {
        code = "validation"
      }
    } catch {
      /* ignore */
    }
    throw new TranscribeAudioError(code, msg)
  }

  const data = (await res.json()) as {
    transcript?: string
    language?: string | null
    correlation_id?: string
  }
  const transcript = (data.transcript ?? "").trim()
  if (!transcript) {
    throw new TranscribeAudioError(
      "empty_transcript",
      "Không thể nhận diện giọng nói. Vui lòng thử lại."
    )
  }
  return {
    transcript,
    language: data.language,
    correlationId: data.correlation_id ?? correlationId,
  }
}

export type SynthesizeSpeechErrorCode =
  | "network"
  | "tts_unavailable"
  | "validation"
  | "unknown"

export class SynthesizeSpeechError extends Error {
  readonly code: SynthesizeSpeechErrorCode

  constructor(code: SynthesizeSpeechErrorCode, message: string) {
    super(message)
    this.name = "SynthesizeSpeechError"
    this.code = code
  }
}

/** POST JSON → Spring relay → Python TTS (FPT.AI-VITs) → audio/wav blob. */
export async function synthesizeSpeech(
  text: string,
  options?: { voice?: string }
): Promise<Blob> {
  const token = sessionStorage.getItem("accessToken")
  const correlationId = crypto.randomUUID()
  const body: { text: string; voice?: string } = { text: text.trim() }
  if (options?.voice?.trim()) body.voice = options.voice.trim()

  let res: Response
  try {
    res = await fetch(getApiUrl("/api/v1/ai/chat/synthesize"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token?.trim() ? { Authorization: `Bearer ${token}` } : {}),
        "X-Correlation-Id": correlationId,
      },
      body: JSON.stringify(body),
    })
  } catch {
    throw new SynthesizeSpeechError("network", "Lỗi kết nối khi tạo giọng đọc.")
  }

  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    let code: SynthesizeSpeechErrorCode = "unknown"
    try {
      const j = (await res.json()) as { error?: { message?: string; code?: string } }
      if (j.error?.message) msg = j.error.message
      if (res.status === 503 || j.error?.code === "AI_TTS_UNAVAILABLE") {
        code = "tts_unavailable"
        msg = "Dịch vụ đọc văn bản tạm thời không khả dụng."
      } else if (res.status === 400) {
        code = "validation"
      }
    } catch {
      /* ignore non-JSON error body */
    }
    throw new SynthesizeSpeechError(code, msg)
  }

  const blob = await res.blob()
  if (!blob.size) {
    throw new SynthesizeSpeechError("unknown", "Dịch vụ đọc văn bản trả về dữ liệu rỗng.")
  }
  return blob
}

function parseSseBlock(block: string): { event: string; data: string } | null {
  let event = ""
  const dataLines: string[] = []
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim()
    } else if (line.startsWith("data:")) {
      // Preserve meaningful leading spaces in payload chunks.
      // Only drop a single separator space when the wire line is explicitly "data: <payload>".
      const d = line.startsWith("data: ") ? line.slice(6) : line.slice(5)
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

/** Dev: Vite proxy có thể buffer POST SSE — gọi thẳng Spring (CORS đã bật localhost). */
function resolveAiChatStreamUrl(): string {
  const fromEnv = import.meta.env.VITE_AI_STREAM_URL as string | undefined
  if (fromEnv?.trim()) {
    return fromEnv.trim()
  }
  if (import.meta.env.DEV) {
    return "http://127.0.0.1:8080/api/v1/ai/chat/stream"
  }
  return getApiUrl("/api/v1/ai/chat/stream")
}

/**
 * POST + Bearer → Spring relay → FastAPI; SSE events `progress` | `delta` | `clarify` | …
 */
export function startAiChatPostStream(args: OpenAiChatStreamArgs): AiChatStreamHandle {
  const ac = new AbortController()

  void (async () => {
    try {
      const token = sessionStorage.getItem("accessToken")
      const url = resolveAiChatStreamUrl()
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
          if (parsed.event === "progress" && parsed.data.length > 0 && args.onProgress) {
            args.onProgress(parsed.data)
          }
          if (parsed.event === "delta_full" && parsed.data.length > 0 && args.onDeltaFull) {
            args.onDeltaFull(parsed.data)
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
        if (parsed?.event === "progress" && parsed.data.length > 0 && args.onProgress) {
          args.onProgress(parsed.data)
        }
        if (parsed?.event === "delta_full" && parsed.data.length > 0 && args.onDeltaFull) {
          args.onDeltaFull(parsed.data)
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
