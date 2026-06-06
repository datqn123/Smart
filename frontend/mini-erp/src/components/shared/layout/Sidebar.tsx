import { useRef, useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { 
  LayoutDashboard,
  Package, 
  ShoppingCart, 
  Banknote, 
  Settings, 
  LogOut,
  Brain,
  ChevronDown,
  FolderTree
} from "lucide-react"
import { useSidebarStore, type NavItemKey } from "@/store/sidebarStore"
import { useAuthStore, type UserRole } from "@/features/auth/store/useAuthStore"
import { logoutAndGoToLogin } from "@/features/auth/lib/sessionAuth"
import type { MenuPermissions } from "@/features/auth/types/menuPermissions"
import { useUIStore } from "@/store/useUIStore"
import { Button } from "@/components/ui/button"
import { getRuntimeCustomMenuForUser } from "@/features/custom-builder/runtime/customMenuRuntime"
import type { RuntimeCustomMenuFolder } from "@/features/custom-builder/runtime/customMenuRuntime"
import { getRuntimeCustomMenu } from "@/features/custom-builder/api/customInterfaceApi"
import { getMockRuntimeCustomMenu } from "@/features/custom-builder/api/customBuilderMockAdapter"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

/** Mục con: `always` (SRS *Thông tin cửa hàng* / tạm *Nhật ký*); hoặc một boolean trong `MenuPermissions`. */
type SubItemSpec = {
  label: string
  path: string
  always?: boolean
  perm?: keyof MenuPermissions
  /** Chỉ hiện khi `user.role === "Admin"` và đã thỏa quyền nhóm cha (`allSubsPerm` / `perm`). */
  adminOnly?: boolean
}

interface NavItemConfig {
  id: NavItemKey
  label: string
  icon: React.ReactNode
  /** Tất cả mục con cùng một quyền (SRS: nhóm Kho, Sản phẩm, …). */
  allSubsPerm?: keyof MenuPermissions
  subItems: SubItemSpec[]
}

type NavItem = Pick<NavItemConfig, "id" | "label" | "icon"> & {
  subItems: { label: string; path: string }[]
}

interface SidebarProps {
  isMobile?: boolean
}

const navConfig: NavItemConfig[] = [
  {
    id: "dashboard",
    label: "Tổng quan",
    icon: <LayoutDashboard className="h-[18px] w-[18px]" />,
    subItems: [
      { label: "Dashboard", path: "/dashboard", perm: "can_view_dashboard" },
    ],
  },
  {
    id: "inventory",
    label: "Kho hàng",
    icon: <Package className="h-[18px] w-[18px]" />,
    allSubsPerm: "can_manage_inventory",
    subItems: [
      { label: "Tồn kho", path: "/inventory/stock" },
      { label: "Phiếu nhập kho", path: "/inventory/inbound" },
      { label: "Phiếu xuất kho", path: "/inventory/dispatch" },
    ],
  },
  {
    id: "products",
    label: "Sản phẩm",
    icon: <Package className="h-[18px] w-[18px]" />,
    subItems: [
      { label: "Danh mục sản phẩm", path: "/products/categories", perm: "can_manage_products" },
      { label: "Quản lý sản phẩm", path: "/products/list", perm: "can_manage_products" },
      { label: "Nhà cung cấp", path: "/products/suppliers", perm: "can_manage_products" },
      { label: "Khách hàng", path: "/products/customers", perm: "can_manage_customers" },
    ],
  },
  {
    id: "orders",
    label: "Đơn hàng",
    icon: <ShoppingCart className="h-[18px] w-[18px]" />,
    allSubsPerm: "can_manage_orders",
    subItems: [
      { label: "Đơn bán lẻ", path: "/orders/retail" },
      { label: "Lịch sử hóa đơn", path: "/orders/wholesale" },
    ],
  },
  {
    id: "cashflow",
    label: "Dòng tiền",
    icon: <Banknote className="h-[18px] w-[18px]" />,
    allSubsPerm: "can_view_finance",
    subItems: [
      { label: "Giao dịch thu chi", path: "/cashflow/transactions" },
      { label: "Sổ nợ", path: "/cashflow/debt" },
      { label: "Sổ cái tài chính", path: "/cashflow/ledger", adminOnly: true },
    ],
  },
  {
    id: "ai-tools",
    label: "AI & Trợ lý",
    icon: <Brain className="h-[18px] w-[18px]" />,
    allSubsPerm: "can_use_ai",
    subItems: [
      { label: "Trợ lý ảo AI", path: "/ai/chat" },
    ],
  },
  {
    id: "settings",
    label: "Cài đặt",
    icon: <Settings className="h-[18px] w-[18px]" />,
    subItems: [
      { label: "Thông tin cửa hàng", path: "/settings/store-info", always: true },
      { label: "Cấu hình giao diện", path: "/settings/interface", always: true },
      { label: "Trình thiết kế dữ liệu", path: "/settings/custom-builder", perm: "can_manage_custom_builder" },
      { label: "Quản lý nhân viên", path: "/settings/employees", perm: "can_manage_staff" },
      { label: "Cấu hình cảnh báo", path: "/settings/alerts", perm: "can_configure_alerts" },
      { label: "Nhật ký hệ thống", path: "/settings/system-logs", always: true },
    ],
  },
]

function subItemVisible(
  s: SubItemSpec,
  p: MenuPermissions,
  all?: keyof MenuPermissions,
  role?: UserRole | null,
): boolean {
  if (s.always) {
    return true
  }
  if (s.adminOnly) {
    return role === "Admin" && (all ? Boolean(p[all]) : s.perm ? Boolean(p[s.perm]) : false)
  }
  if (all) {
    return Boolean(p[all])
  }
  if (s.perm) {
    return Boolean(p[s.perm])
  }
  return false
}

function buildNavForPermissions(
  p: MenuPermissions,
  role: UserRole | null,
  runtimeFolders: RuntimeCustomMenuFolder[],
): NavItem[] {
  const out: NavItem[] = []
  for (const c of navConfig) {
    const subs = c.subItems
      .filter((s) => subItemVisible(s, p, c.allSubsPerm, role))
      .map((s) => ({ label: s.label, path: s.path }))
    if (subs.length === 0) {
      continue
    }
    out.push({ id: c.id, label: c.label, icon: c.icon, subItems: subs })
  }
  const customFolders = getRuntimeCustomMenuForUser(p, role, runtimeFolders).map((folder) => ({
    id: `custom-${folder.key}` as NavItemKey,
    label: folder.label,
    icon: <FolderTree className="h-[18px] w-[18px]" />,
    subItems: folder.children.map((page) => ({ label: page.label, path: page.routePath })),
  }))
  const settingsItem = out.find((item) => item.id === "settings")
  const staticBeforeSettings = out.filter((item) => item.id !== "settings")
  return settingsItem ? [...staticBeforeSettings, ...customFolders, settingsItem] : [...out, ...customFolders]
}

export function Sidebar({ isMobile = false }: SidebarProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const { expandedItems, toggleItem, expandItem } = useSidebarStore()
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen)
  const sidebarWidth = useUIStore((s) => s.sidebarWidth)
  const setSidebarWidth = useUIStore((s) => s.setSidebarWidth)
  const isResizing = useRef(false)
  const zustandLogout = useAuthStore((state) => state.logout)
  const menuPermissions = useAuthStore((state) => state.menuPermissions)
  const userRole = useAuthStore((state) => state.user?.role ?? null)
  const [loggingOut, setLoggingOut] = useState(false)
  const [runtimeFolders, setRuntimeFolders] = useState<RuntimeCustomMenuFolder[]>([])

  useEffect(() => {
    let alive = true
    getRuntimeCustomMenu()
      .then((data) => {
        if (alive) {
          setRuntimeFolders(data.folders ?? [])
        }
      })
      .catch(() => {
        getMockRuntimeCustomMenu().then((data) => {
          if (alive) {
            setRuntimeFolders(data.folders ?? [])
          }
        })
      })
    return () => {
      alive = false
    }
  }, [menuPermissions, userRole])

  const filteredNavItems = useMemo(
    () => buildNavForPermissions(menuPermissions, userRole, runtimeFolders),
    [menuPermissions, userRole, runtimeFolders],
  )

  const isActiveRoute = (path: string) => location.pathname === path || location.pathname.startsWith(`${path}/`)
  
  const isParentActive = (item: NavItem) => {
    return item.subItems?.some(sub => isActiveRoute(sub.path))
  }

  useEffect(() => {
    // Find parent of current route and expand it automatically
    const activeParent = filteredNavItems.find(item => 
      item.subItems?.some(sub => isActiveRoute(sub.path))
    )
    if (activeParent && !expandedItems.has(activeParent.id)) {
      expandItem(activeParent.id)
    }
  }, [location.pathname, expandItem, filteredNavItems, expandedItems])

  const handleNavigation = (path: string) => {
    navigate(path)
    // Close sidebar on mobile after navigation
    if (isMobile) {
      setSidebarOpen(false)
    }
  }

  const startResizing = (e: React.MouseEvent) => {
    e.preventDefault()
    isResizing.current = true
    document.body.style.cursor = 'col-resize'
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return
      
      const newWidth = e.clientX
      if (newWidth >= 192 && newWidth <= 320) {
        setSidebarWidth(newWidth)
      }
    }

    const handleMouseUp = () => {
      isResizing.current = false
      document.body.style.cursor = 'default'
    }

    window.addEventListener("mousemove", handleMouseMove)
    window.addEventListener("mouseup", handleMouseUp)

    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }
  }, [setSidebarWidth])

  return (
    <aside
      className={`relative bg-slate-100 flex flex-col flex-shrink-0 h-screen ${
        isMobile ? "w-full" : "border-r border-slate-200"
      } ${!isResizing.current ? "transition-[width] duration-300 ease-in-out" : ""}`}
      style={{ width: isMobile ? '100%' : sidebarWidth }}
    >
      {/* Resizer Handle */}
      {!isMobile && (
        <div
          className="absolute top-0 right-[-3px] w-1.5 h-full cursor-col-resize z-50 hover:bg-slate-300/50 active:bg-slate-400/50 transition-colors"
          onMouseDown={startResizing}
        />
      )}

      {/* Logo Section */}
      <div className="h-14 flex items-center justify-center border-b border-slate-200 px-4 flex-shrink-0">
        <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center shadow-sm flex-shrink-0">
          <span className="text-white font-bold text-sm">M</span>
        </div>
        <span className="ml-3 font-semibold text-slate-900 text-sm whitespace-nowrap truncate overflow-hidden">
          Mini ERP
        </span>
      </div>

      {/* Navigation Items - Scrollable */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-3">
        {filteredNavItems.map((item) => (
          <div key={item.id} className="space-y-2">
            <Collapsible
              open={expandedItems.has(item.id)}
              onOpenChange={() => toggleItem(item.id)}
            >
              <CollapsibleTrigger asChild>
                <button 
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md transition-all duration-200 h-11 ${
                    isParentActive(item) 
                      ? "text-slate-900 bg-slate-200/50" 
                      : "text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className={`${isParentActive(item) ? "text-primary" : "text-slate-600"} flex-shrink-0`}>
                      {item.icon}
                    </div>
                    <span className={`text-sm ${isParentActive(item) ? "font-semibold" : "font-medium"} truncate`}>
                      {item.label}
                    </span>
                  </div>
                  {item.subItems && (
                    <ChevronDown
                      className={`h-4 w-4 transition-transform duration-200 flex-shrink-0 ${
                        isParentActive(item) ? "text-primary" : "text-slate-600"
                      } ${
                        expandedItems.has(item.id) ? "rotate-180" : ""
                      }`}
                    />
                  )}
                </button>
              </CollapsibleTrigger>

              {/* Sub Items - No 1px borders, use whitespace */}
              {item.subItems && (
                <CollapsibleContent className="space-y-1 mt-1.5 pl-6 overflow-hidden">
                  {item.subItems.map((subItem) => (
                    <button
                      key={subItem.path}
                      onClick={() => handleNavigation(subItem.path)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm transition-all duration-200 h-10 flex items-center truncate ${
                        isActiveRoute(subItem.path)
                          ? "relative bg-slate-200 text-slate-900 font-medium before:absolute before:left-0 before:top-0 before:bottom-0 before:w-1 before:bg-primary overflow-hidden"
                          : "text-slate-700 hover:bg-slate-200/50 hover:text-slate-900"
                      }`}
                    >
                      {subItem.label}
                    </button>
                  ))}
                </CollapsibleContent>
              )}
            </Collapsible>

            {/* Reduced vertical whitespace between groups: 12px */}
            {item.id !== "settings" && <div className="h-3" />}
          </div>
        ))}
      </nav>

      {/* Footer - Logout (Task002: POST /api/v1/auth/logout + clear session) */}
      <div className="border-t border-slate-200 p-3 flex-shrink-0">
        <Button
          variant="ghost"
          disabled={loggingOut}
          onClick={async () => {
            if (loggingOut) return
            setLoggingOut(true)
            try {
              await logoutAndGoToLogin(navigate, () => {
                zustandLogout()
                if (isMobile) setSidebarOpen(false)
              })
            } finally {
              setLoggingOut(false)
            }
          }}
          className="w-full h-11 justify-start space-x-3 text-alert hover:bg-alert-light rounded-md transition-all truncate"
        >
          <LogOut className="h-[18px] w-[18px] flex-shrink-0" />
          <span className="text-sm font-medium">{loggingOut ? "Đang đăng xuất…" : "Đăng xuất"}</span>
        </Button>
      </div>
    </aside>
  )
}
