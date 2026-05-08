import { getApiUrl } from "@/lib/api/config"

type OpenAiChatStreamArgs = {
  query: string
  onDelta: (delta: string) => void
  onDone: () => void
  onError: (message: string) => void
}

export function openAiChatStream({ query, onDelta, onDone, onError }: OpenAiChatStreamArgs): EventSource {
  const url = getApiUrl(`/api/v1/ai/chat/stream?q=${encodeURIComponent(query)}`)
  const es = new EventSource(url)

  es.addEventListener("delta", (evt) => {
    const data = (evt as MessageEvent).data
    if (typeof data === "string" && data.length > 0) {
      onDelta(data)
    }
  })

  es.addEventListener("done", () => {
    onDone()
    es.close()
  })

  es.addEventListener("error", (evt) => {
    const data = (evt as MessageEvent).data
    const message = typeof data === "string" && data.length > 0 ? data : "Không thể kết nối trợ lý AI."
    onError(message)
    es.close()
  })

  return es
}

