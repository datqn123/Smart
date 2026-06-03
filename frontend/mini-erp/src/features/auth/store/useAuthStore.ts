import { create } from "zustand"
import { persist } from "zustand/middleware"
import { parseMenuPermissionsFromAccessToken } from "@/features/auth/lib/parseAccessTokenMenuPermissions"
import type { MenuPermissions } from "@/features/auth/types/menuPermissions"

export type UserRole = "Owner" | "Admin" | "Manager" | "Staff" | "Warehouse"

export interface User {
  id: number
  fullName: string
  email: string
  username?: string
  role: UserRole
}

const EMPTY_PERMS: MenuPermissions = {
  can_view_dashboard: false,
  can_use_ai: false,
  can_manage_inventory: false,
  can_manage_products: false,
  can_manage_customers: false,
  can_manage_orders: false,
  can_approve: false,
  can_view_finance: false,
  can_manage_staff: false,
  can_configure_alerts: false,
  can_manage_custom_builder: false,
  can_use_custom_entities: false,
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  menuPermissions: MenuPermissions
  setMenuPermissions: (p: MenuPermissions) => void
  login: (user: User, accessToken: string) => void
  logout: () => void
  /** Task101 — F5: đồng bộ user + `mp` từ sessionStorage (token là nguồn sự thật cho `mp`). */
  hydrateFromSession: () => void
}

function readUserFromSessionStorage(): User | null {
  const raw = sessionStorage.getItem("user")
  if (!raw) {
    return null
  }
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      menuPermissions: EMPTY_PERMS,
      setMenuPermissions: (p) => set({ menuPermissions: p }),
      login: (user, accessToken) =>
        set({
          user,
          isAuthenticated: true,
          menuPermissions: parseMenuPermissionsFromAccessToken(accessToken),
        }),
      logout: () => set({ user: null, isAuthenticated: false, menuPermissions: EMPTY_PERMS }),
      hydrateFromSession: () => {
        const token = sessionStorage.getItem("accessToken")
        const u = readUserFromSessionStorage()
        if (token?.trim() && u) {
          set({
            user: u,
            isAuthenticated: true,
            menuPermissions: parseMenuPermissionsFromAccessToken(token),
          })
        } else {
          set({ user: null, isAuthenticated: false, menuPermissions: EMPTY_PERMS })
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (s) => ({
        user: s.user,
        isAuthenticated: s.isAuthenticated,
        menuPermissions: s.menuPermissions,
      }),
    },
  ),
)
