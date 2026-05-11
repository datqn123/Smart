import { getApiUrl } from "@/lib/api/config"

type OpenAiChatStreamArgs = {
  query: string
  conversationId: string
  onDelta: (delta: string) => void
  onDone: () => void
  onError: (message: string) => void
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

/**
 * POST + Bearer → Spring relay → FastAPI; SSE events `delta` / `done` / `error` (same as legacy EventSource).
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
          if (parsed.event === "delta" && parsed.data.length > 0) args.onDelta(parsed.data)
          if (parsed.event === "done") args.onDone()
          if (parsed.event === "error") {
            args.onError(parsed.data.length > 0 ? parsed.data : "Không thể kết nối trợ lý AI.")
          }
        }
      }

      const tail = buf.trim()
      if (tail) {
        const parsed = parseSseBlock(tail)
        if (parsed?.event === "delta" && parsed.data.length > 0) args.onDelta(parsed.data)
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
