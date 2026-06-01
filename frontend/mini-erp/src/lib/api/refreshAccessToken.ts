import { getApiUrl } from "@/lib/api/config"
import { syncMenuPermissionsFromSessionStorage } from "@/features/auth/lib/syncMenuPermissionsFromSessionStorage"
import { buildClientSessionHeaders } from "@/features/auth/lib/clientSessionId"

/**
 * Task003 — POST /api/v1/auth/refresh (public, no Bearer).
 * Cập nhật sessionStorage nếu thành công.
 *
 * @returns true nếu đã lưu access + refresh mới
 */
export async function tryRefreshAccessToken(): Promise<boolean> {
  const refreshToken = sessionStorage.getItem("refreshToken")
  if (!refreshToken?.trim()) {
    return false
  }
  const url = getApiUrl("/api/v1/auth/refresh")
  const res = await fetch(url, {
    method: "POST",
    headers: buildClientSessionHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ refreshToken }),
  })
  let json: unknown
  try {
    json = await res.json()
  } catch {
    return false
  }
  const obj = json as Record<string, unknown>
  if (!res.ok || obj?.success !== true || typeof obj.data !== "object" || obj.data === null) {
    return false
  }
  const data = obj.data as { accessToken?: unknown; refreshToken?: unknown }
  if (typeof data.accessToken !== "string" || typeof data.refreshToken !== "string") {
    return false
  }
  sessionStorage.setItem("accessToken", data.accessToken)
  sessionStorage.setItem("refreshToken", data.refreshToken)
  syncMenuPermissionsFromSessionStorage()
  return true
}
