const CLIENT_SESSION_STORAGE_KEY = "smartErpClientSessionId"
export const CLIENT_SESSION_ID_HEADER = "X-Client-Session-Id"

function makeClientSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`
}

/**
 * Cùng browser profile => cùng clientSessionId, kể cả khi đóng/mở lại tab.
 */
export function getOrCreateClientSessionId(): string | null {
  if (typeof window === "undefined") {
    return null
  }
  try {
    const existing = window.localStorage.getItem(CLIENT_SESSION_STORAGE_KEY)?.trim()
    if (existing) {
      return existing
    }
    const created = makeClientSessionId()
    window.localStorage.setItem(CLIENT_SESSION_STORAGE_KEY, created)
    return created
  } catch {
    return null
  }
}

export function buildClientSessionHeaders(init?: HeadersInit): Headers {
  const headers = new Headers(init)
  const clientSessionId = getOrCreateClientSessionId()
  if (clientSessionId) {
    headers.set(CLIENT_SESSION_ID_HEADER, clientSessionId)
  }
  return headers
}
