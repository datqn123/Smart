import { useState, useEffect, useRef } from "react"
import { useLocation, Link } from "react-router-dom"
import { Bell, Home, Menu, X, CheckCheck, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { useUIStore } from "@/store/useUIStore"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  getNotifications,
  patchNotificationRead,
  postNotificationsMarkAllRead,
  type NotificationItemDto,
} from "@/features/notifications/api/notificationsApi"
import { formatRelativePastVi } from "@/features/notifications/lib/formatRelativePastVi"
import { ReceiptDetailDialog } from "@/features/inventory/components/ReceiptDetailDialog"
import { DispatchDetailDialog } from "@/features/inventory/components/DispatchDetailDialog"
import { getStockReceiptById, mapStockReceiptViewToUi } from "@/features/inventory/api/stockReceiptsApi"
import {
  approveStockDispatch,
  getStockDispatchDetail,
  mapStockDispatchDetailToUi,
} from "@/features/inventory/api/dispatchApi"
import type { StockDispatch, StockReceipt } from "@/features/inventory/types"
import type { StockDispatchDetailResponse } from "@/features/inventory/api/dispatchApi"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"

const PAGE_TITLE_VI: Record<string, string> = {
  dashboard: "Bảng điều khiển",
  "ai-insights": "Phân tích AI",
  stock: "Tồn kho",
  inbound: "Phiếu nhập kho",
  dispatch: "Phiếu xuất kho",
  locations: "Vị trí kho",
  categories: "Danh mục sản phẩm",
  list: "Quản lý sản phẩm",
  suppliers: "Nhà cung cấp",
  customers: "Khách hàng",
  retail: "Đơn bán lẻ",
  wholesale: "Lịch sử hóa đơn",
  returns: "Đơn trả hàng",
  transactions: "Giao dịch thu chi",
  debt: "Sổ nợ",
  ledger: "Sổ cái tài chính",
  revenue: "Doanh thu",
  "top-products": "Top sản phẩm",
  chat: "Trợ lý ảo AI",
  "store-info": "Thông tin cửa hàng",
  employees: "Quản lý nhân viên",
  alerts: "Cấu hình cảnh báo",
  "system-logs": "Nhật ký hệ thống",
}

function initialsFromName(name: string): string {
  const p = name.trim().split(/\s+/).filter(Boolean)
  if (p.length === 0) return "?"
  if (p.length === 1) return p[0].slice(0, 2).toUpperCase()
  return (p[0][0] + p[p.length - 1][0]).toUpperCase()
}

function isOpenableStockReceipt(n: NotificationItemDto): boolean {
  return n.referenceType === "StockReceipt" && n.referenceId != null && n.referenceId > 0
}

function isOpenableStockDispatch(n: NotificationItemDto): boolean {
  return n.referenceType === "StockDispatch" && n.referenceId != null && n.referenceId > 0
}

export function Header() {
  const location = useLocation()
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false)
  const notificationRef = useRef<HTMLDivElement>(null)
  const { sidebarOpen, setSidebarOpen } = useUIStore()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)
  const role = user?.role
  const canApprovePerm = useAuthStore((s) => s.menuPermissions.can_approve)
  const userCanApproveReceipt = Boolean((role === "Admin" || role === "Owner") && canApprovePerm)
  const isAdmin = role === "Admin"
  const queryClient = useQueryClient()

  const [headerReceipt, setHeaderReceipt] = useState<StockReceipt | null>(null)
  const [headerReceiptOpen, setHeaderReceiptOpen] = useState(false)
  const [headerDispatch, setHeaderDispatch] = useState<StockDispatch | null>(null)
  const [headerDispatchDetail, setHeaderDispatchDetail] = useState<StockDispatchDetailResponse | null>(null)
  const [headerDispatchOpen, setHeaderDispatchOpen] = useState(false)
  const [notifBusyId, setNotifBusyId] = useState<number | null>(null)

  const notificationsQuery = useQuery({
    queryKey: ["notifications", "list"],
    queryFn: () => getNotifications({ page: 1, limit: 50 }),
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 12_000 : false,
  })

  const markOneRead = useMutation({
    mutationFn: (id: number) => patchNotificationRead(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications", "list"] })
    },
  })

  const markAllRead = useMutation({
    mutationFn: () => postNotificationsMarkAllRead(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notifications", "list"] })
    },
  })

  const approveHeaderDispatch = useMutation({
    mutationFn: (dispatchId: number) => approveStockDispatch(dispatchId),
    onSuccess: async (_data, dispatchId) => {
      toast.success("Đã duyệt phiếu — chuyển chờ xuất")
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatch-detail", dispatchId] })
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatches", "v1", "list"] })
      await queryClient.invalidateQueries({ queryKey: ["notifications", "list"] })
      try {
        const d = await getStockDispatchDetail(dispatchId)
        setHeaderDispatchDetail(d)
        setHeaderDispatch(mapStockDispatchDetailToUi(d))
      } catch {
        /* ignore refresh errors */
      }
    },
    onError: (e: unknown) => {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không duyệt được phiếu")
      } else {
        toast.error("Không duyệt được phiếu")
      }
    },
  })

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setIsNotificationsOpen(false)
      }
    }
    if (isNotificationsOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isNotificationsOpen])

  useEffect(() => {
    if (isNotificationsOpen && isAuthenticated) {
      void queryClient.invalidateQueries({ queryKey: ["notifications", "list"] })
    }
  }, [isNotificationsOpen, isAuthenticated, queryClient])

  const pathSegments = location.pathname.split("/").filter(Boolean)
  const lastSegment = pathSegments.length > 0 ? pathSegments[pathSegments.length - 1] : undefined
  const currentPage = lastSegment
    ? (PAGE_TITLE_VI[lastSegment] ?? lastSegment.charAt(0).toUpperCase() + lastSegment.slice(1))
    : "Bảng điều khiển"

  const notifData = notificationsQuery.data
  const items = notifData?.items ?? []
  const unreadTotal = notifData?.unreadTotal ?? 0
  const notifErr = notificationsQuery.error instanceof Error ? notificationsQuery.error.message : null

  async function handleNotificationActivate(n: NotificationItemDto) {
    if (isOpenableStockReceipt(n)) {
      setNotifBusyId(n.id)
      try {
        const raw = await getStockReceiptById(n.referenceId!)
        const ui = mapStockReceiptViewToUi(raw)
        setHeaderReceipt(ui)
        setHeaderReceiptOpen(true)
        setIsNotificationsOpen(false)
        await markOneRead.mutateAsync(n.id)
      } catch (e) {
        if (e instanceof ApiRequestError) {
          toast.error(e.body?.message ?? "Không mở được phiếu nhập. Thông báo có thể đã hết hiệu lực.")
        } else {
          toast.error("Không mở được phiếu nhập.")
        }
      } finally {
        setNotifBusyId(null)
      }
      return
    }
    if (isOpenableStockDispatch(n)) {
      setNotifBusyId(n.id)
      try {
        const detail = await getStockDispatchDetail(n.referenceId!)
        setHeaderDispatchDetail(detail)
        setHeaderDispatch(mapStockDispatchDetailToUi(detail))
        setHeaderDispatchOpen(true)
        setIsNotificationsOpen(false)
        await markOneRead.mutateAsync(n.id)
      } catch (e) {
        if (e instanceof ApiRequestError) {
          toast.error(e.body?.message ?? "Không mở được phiếu xuất. Thông báo có thể đã hết hiệu lực.")
        } else {
          toast.error("Không mở được phiếu xuất.")
        }
      } finally {
        setNotifBusyId(null)
      }
      return
    }
    if (!n.read) {
      markOneRead.mutate(n.id)
    }
    setIsNotificationsOpen(false)
  }

  return (
    <header className="h-14 bg-white border-b border-slate-200 flex items-center px-4 md:px-6 shadow-sm sticky top-0 z-50">
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center space-x-2 text-sm text-slate-600">
          <button
            type="button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden p-2 -ml-2 mr-1 hover:bg-slate-100 rounded-md transition-colors duration-200"
          >
            {sidebarOpen ? (
              <X className="h-5 w-5 text-slate-600" />
            ) : (
              <Menu className="h-5 w-5 text-slate-600" />
            )}
          </button>

          <Link to="/" className="flex items-center hover:text-slate-900 transition-colors">
            <Home className="w-4 h-4 md:mr-2" />
            <span className="hidden md:inline">Trang chủ</span>
          </Link>
          <span className="text-slate-300">/</span>
          <span className="font-medium text-slate-900">{currentPage}</span>
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative" ref={notificationRef}>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="relative hover:bg-slate-100 rounded-full h-11 w-11 min-h-11 min-w-11"
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              aria-label="Thông báo"
            >
              <Bell className="h-[18px] w-[18px] text-slate-600" />
              {isAuthenticated && unreadTotal > 0 && (
                <span className="absolute top-1.5 right-1.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center text-[10px] font-bold bg-red-500 text-white rounded-full border-2 border-white">
                  {unreadTotal > 99 ? "99+" : unreadTotal}
                </span>
              )}
            </Button>

            {isNotificationsOpen && (
              <div className="absolute right-0 mt-2 w-[400px] bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200 z-[100]">
                <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-white sticky top-0 z-10">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">Thông báo</span>
                    {unreadTotal > 0 ? (
                      <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        {unreadTotal} chưa đọc
                      </span>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    disabled={!isAuthenticated || unreadTotal === 0 || markAllRead.isPending}
                    onClick={() => markAllRead.mutate()}
                    className="text-[11px] font-bold text-slate-500 hover:text-blue-600 flex items-center gap-1 transition-colors disabled:opacity-40 disabled:pointer-events-none"
                  >
                    {markAllRead.isPending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <CheckCheck className="h-3.5 w-3.5" />
                    )}
                    Đánh dấu đã đọc
                  </button>
                </div>
                {!isAuthenticated ? (
                  <div className="p-6 text-center text-sm text-muted-foreground">Đăng nhập để xem thông báo.</div>
                ) : notificationsQuery.isLoading ? (
                  <div className="flex items-center justify-center py-16 text-muted-foreground">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : (
                  <div className="max-h-[400px] overflow-y-auto custom-scrollbar scroll-smooth">
                    {notifErr ? (
                      <div className="p-4 text-sm text-alert">{notifErr}</div>
                    ) : items.length === 0 ? (
                      <div className="p-8 text-center text-sm text-muted-foreground">
                        Không có thông báo nào.
                      </div>
                    ) : (
                      items.map((n) => (
                        <div
                          key={n.id}
                          role="button"
                          tabIndex={0}
                          onClick={() => void handleNotificationActivate(n)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault()
                              void handleNotificationActivate(n)
                            }
                          }}
                          className={cn(
                            "p-4 border-b border-slate-50 last:border-0 hover:bg-slate-50 cursor-pointer transition-colors relative text-left outline-none focus-visible:ring-2 focus-visible:ring-ring/50 min-h-[44px]",
                            !n.read && "bg-blue-50/30",
                            notifBusyId === n.id && "pointer-events-none opacity-70",
                          )}
                        >
                          {!n.read && (
                            <div className="absolute left-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-500 rounded-full" />
                          )}
                          <div className="flex justify-between items-start mb-1.5 gap-2 pl-3">
                            <span className="font-bold text-sm text-slate-900 leading-snug">{n.title}</span>
                            <span className="text-xs text-slate-400 whitespace-nowrap shrink-0 flex items-center gap-1">
                              {notifBusyId === n.id ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400" />
                              ) : null}
                              {formatRelativePastVi(n.createdAt)}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 leading-relaxed font-medium pl-3">{n.message}</p>
                        </div>
                      ))
                    )}
                    {(notificationsQuery.isFetching && !notificationsQuery.isLoading) || markOneRead.isPending ? (
                      <div className="py-3 flex justify-center text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="h-6 w-px bg-slate-200 hidden sm:block" />

          <div className="flex items-center space-x-2 hidden md:flex cursor-pointer hover:opacity-80 transition-opacity">
            <div className="text-right">
              <div className="text-sm font-medium text-slate-900 leading-none">
                {user?.fullName ?? "Người dùng"}
              </div>
              <div className="text-xs text-slate-500 leading-none mt-1">{user?.email ?? ""}</div>
            </div>
            <Avatar className="h-9 w-9 border border-slate-200">
              <AvatarImage src={undefined} alt={user?.fullName ?? "User"} />
              <AvatarFallback className="bg-slate-100 text-slate-600 text-xs">
                {initialsFromName(user?.fullName ?? user?.email ?? "?")}
              </AvatarFallback>
            </Avatar>
          </div>
        </div>
      </div>

      <ReceiptDetailDialog
        receipt={headerReceipt}
        isOpen={headerReceiptOpen}
        onClose={() => {
          setHeaderReceiptOpen(false)
          setHeaderReceipt(null)
        }}
        canApprove={userCanApproveReceipt}
        isLoadingDetail={false}
        onAfterApprove={async () => {
          await queryClient.invalidateQueries({ queryKey: ["notifications", "list"] })
          await queryClient.invalidateQueries({ queryKey: ["stock-receipts"] })
        }}
      />

      <DispatchDetailDialog
        dispatch={headerDispatch}
        isOpen={headerDispatchOpen}
        onClose={() => {
          setHeaderDispatchOpen(false)
          setHeaderDispatch(null)
          setHeaderDispatchDetail(null)
        }}
        canApprove
        canApproveStockLines={isAdmin}
        onApproveStockDispatch={() => {
          if (headerDispatch?.id) {
            approveHeaderDispatch.mutate(headerDispatch.id)
          }
        }}
        approveStockDispatchPending={approveHeaderDispatch.isPending}
        detailFromApi={headerDispatchDetail}
        detailLoading={false}
      />
    </header>
  )
}
