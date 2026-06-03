import type { MenuPermissions } from "@/features/auth/types/menuPermissions"

const KEYS: (keyof MenuPermissions)[] = [
  "can_view_dashboard",
  "can_use_ai",
  "can_manage_inventory",
  "can_manage_products",
  "can_manage_customers",
  "can_manage_orders",
  "can_approve",
  "can_view_finance",
  "can_manage_staff",
  "can_configure_alerts",
  "can_manage_custom_builder",
  "can_use_custom_entities",
]

const DEFAULT_FALSE: MenuPermissions = KEYS.reduce((acc, k) => {
  acc[k] = false
  return acc
}, {} as MenuPermissions)

/**
 * Task101: đọc claim `mp` từ access JWT (payload đã mã hóa base64), không verify chữ ký
 * (chỉ dùng hiển thị menu; BE mới thực thi 403 theo từng API).
 */
export function parseMenuPermissionsFromAccessToken(accessToken: string | null): MenuPermissions {
  if (!accessToken?.trim()) {
    return { ...DEFAULT_FALSE }
  }
  const parts = accessToken.split(".")
  if (parts.length < 2) {
    return { ...DEFAULT_FALSE }
  }
  let b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/")
  const pad = (4 - (b64.length % 4)) % 4
  b64 += "=".repeat(pad)
  let payload: Record<string, unknown>
  try {
    const json = atob(b64)
    payload = JSON.parse(json) as Record<string, unknown>
  } catch {
    return { ...DEFAULT_FALSE }
  }
  const mp = payload["mp"] as Record<string, unknown> | undefined
  if (!mp || typeof mp !== "object") {
    return { ...DEFAULT_FALSE }
  }
  const out: MenuPermissions = { ...DEFAULT_FALSE }
  for (const k of KEYS) {
    const v = mp[k as string]
    if (v === true) {
      out[k] = true
    }
  }
  return out
}
