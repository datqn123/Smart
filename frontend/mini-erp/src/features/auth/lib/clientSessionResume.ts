const CLOCK_SKEW_MS = 60_000

function decodeJwtPayload(accessToken: string): Record<string, unknown> | null {
  const parts = accessToken.split(".")
  if (parts.length < 2) {
    return null
  }
  let b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/")
  const pad = (4 - (b64.length % 4)) % 4
  b64 += "=".repeat(pad)
  try {
    const json = atob(b64)
    return JSON.parse(json) as Record<string, unknown>
  } catch {
    return null
  }
}

/**
 * Kiểm tra `exp` trên JWT (không verify chữ ký — chỉ UX điều hướng; BE vẫn validate).
 * @returns true nếu không có exp hợp lệ hoặc đã hết hạn (kèm leeway đồng hồ).
 */
export function isClientAccessTokenExpired(accessToken: string | null): boolean {
  if (!accessToken?.trim()) {
    return true
  }
  const payload = decodeJwtPayload(accessToken)
  if (!payload) {
    return true
  }
  const exp = payload["exp"]
  if (typeof exp !== "number" || !Number.isFinite(exp)) {
    return true
  }
  const expMs = exp * 1000
  return expMs <= Date.now() + CLOCK_SKEW_MS
}

/** Có accessToken + user trong sessionStorage và access (theo claim exp) còn dùng được. */
export function hasResumeSessionInSessionStorage(): boolean {
  const token = sessionStorage.getItem("accessToken")
  const user = sessionStorage.getItem("user")
  if (!token?.trim() || !user?.trim()) {
    return false
  }
  return !isClientAccessTokenExpired(token)
}
