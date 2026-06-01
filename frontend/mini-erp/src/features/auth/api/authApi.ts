import { apiJson } from "@/lib/api/http"
import { buildClientSessionHeaders } from "@/features/auth/lib/clientSessionId"

export type LoginUserDto = {
  id: number
  username: string
  fullName: string
  email: string
  role: string
}

export type LoginResponseData = {
  accessToken: string
  refreshToken: string
  user: LoginUserDto
}

export type RefreshResponseData = {
  accessToken: string
  refreshToken: string
}

/** Task001 — public */
export function postLogin(body: { email: string; password: string }) {
  return apiJson<LoginResponseData>("/api/v1/auth/login", {
    method: "POST",
    headers: buildClientSessionHeaders(),
    body: JSON.stringify(body),
  })
}

/** Task004 §1 — public */
export function postPasswordResetRequest(body: { username: string; message?: string }) {
  return apiJson<Record<string, unknown>>("/api/v1/auth/password-reset-requests", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

/** Task003 — public, no Bearer */
export function postRefresh(body: { refreshToken: string }) {
  return apiJson<RefreshResponseData>("/api/v1/auth/refresh", {
    method: "POST",
    headers: buildClientSessionHeaders(),
    body: JSON.stringify(body),
  })
}

/** Task002 — Bearer required */
export function postLogout(body: { refreshToken: string }) {
  return apiJson<Record<string, unknown>>("/api/v1/auth/logout", {
    method: "POST",
    body: JSON.stringify(body),
    auth: true,
  })
}
