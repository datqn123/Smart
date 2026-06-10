import { useEffect, useMemo, useState } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { OrderTable } from "@/features/orders/components/OrderTable"
import { OrderDetailDialog } from "@/features/orders/components/OrderDetailDialog"
import type { Order } from "@/features/orders/types"
import { Button } from "@/components/ui/button"
import { CheckCircle2, XCircle, AlertCircle, Calendar, Search, RotateCcw } from "lucide-react"
import { toast } from "sonner"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { DATA_TABLE_SCROLL_CLASS, DATA_TABLE_SHELL_CLASS } from "@/lib/data-table-layout"
import { toastApiError } from "@/lib/api/toastApiError"
import {
  APPROVALS_HISTORY_QUERY_KEY,
  APPROVALS_PENDING_QUERY_KEY,
  getPendingApprovals,
} from "@/features/approvals/api/approvalsApi"
import {
  approveStockReceipt,
  rejectStockReceipt,
  STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS,
} from "@/features/inventory/api/stockReceiptsApi"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

type PendingTableRow = Order & { entityType: string; entityId: number }

function toNumber(v: number | string): number {
  return typeof v === "number" ? v : Number(v)
}

export default function PendingApprovalsPage() {
  const { setTitle } = usePageTitle()
  const queryClient = useQueryClient()

  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [rejectEntityId, setRejectEntityId] = useState<number | null>(null)
  const [rejectionReason, setRejectionReason] = useState("")

  const [approveEntityId, setApproveEntityId] = useState<number | null>(null)
  const [approveLocationId, setApproveLocationId] = useState<number>(1)

  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [searchCode, setSearchCode] = useState("")
  const debouncedSearch = useDebouncedValue(searchCode.trim(), SEARCH_DEBOUNCE_MS)
  const [typeFilter, setTypeFilter] = useState<"all" | "Inbound">("all")
  const [page, setPage] = useState(1)

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, startDate, endDate, typeFilter])

  useEffect(() => {
    setTitle("Chờ phê duyệt")
  }, [setTitle])

  const filters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      type: typeFilter,
      fromDate: startDate || undefined,
      toDate: endDate || undefined,
      page,
      limit: PAGE_SIZE,
    }),
    [debouncedSearch, typeFilter, startDate, endDate, page],
  )

  const pendingQuery = useQuery({
    queryKey: [...APPROVALS_PENDING_QUERY_KEY, filters],
    queryFn: () => getPendingApprovals(filters),
  })

  useEffect(() => {
    if (pendingQuery.isError) toastApiError(pendingQuery.error)
  }, [pendingQuery.isError, pendingQuery.error])

  const approveMutation = useMutation({
    mutationFn: ({ entityId, inboundLocationId }: { entityId: number; inboundLocationId: number }) =>
      approveStockReceipt(entityId, { inboundLocationId }),
    onSuccess: () => {
      toast.success("Đã phê duyệt phiếu nhập.")
      setApproveEntityId(null)
      void queryClient.invalidateQueries({ queryKey: APPROVALS_PENDING_QUERY_KEY })
      void queryClient.invalidateQueries({ queryKey: APPROVALS_HISTORY_QUERY_KEY })
    },
    onError: toastApiError,
  })

  const rejectMutation = useMutation({
    mutationFn: ({ entityId, reason }: { entityId: number; reason: string }) =>
      rejectStockReceipt(entityId, { reason }),
    onSuccess: () => {
      toast.success("Đã từ chối phiếu nhập.")
      setRejectEntityId(null)
      setRejectionReason("")
      void queryClient.invalidateQueries({ queryKey: APPROVALS_PENDING_QUERY_KEY })
      void queryClient.invalidateQueries({ queryKey: APPROVALS_HISTORY_QUERY_KEY })
    },
    onError: toastApiError,
  })

  const displayData: PendingTableRow[] = useMemo(() => {
    const items = pendingQuery.data?.items ?? []
    return items.map((it) => {
      const amt = toNumber(it.totalAmount)
      return {
        id: it.entityId,
        entityType: it.entityType,
        entityId: it.entityId,
        orderCode: it.transactionCode,
        type: it.type as Order["type"],
        customerName: it.creatorName,
        date: it.date,
        totalAmount: amt,
        finalAmount: amt,
        status: "Pending",
        itemsCount: 0,
        paymentStatus: "Unpaid",
        notes: it.notes ?? undefined,
      }
    })
  }, [pendingQuery.data?.items])

  const summary = pendingQuery.data?.summary
  const total = pendingQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const resetFilters = () => {
    setStartDate("")
    setEndDate("")
    setSearchCode("")
    setTypeFilter("all")
    setPage(1)
  }

  const handleApproveClick = (row: PendingTableRow) => {
    if (row.entityType !== "stock_receipt") {
      toast.error("Loại chứng từ này chưa hỗ trợ duyệt từ màn hình này.")
      return
    }
    setApproveEntityId(row.entityId)
    setApproveLocationId(STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS[0]?.id ?? 1)
  }

  const confirmApprove = () => {
    if (approveEntityId == null) return
    approveMutation.mutate({ entityId: approveEntityId, inboundLocationId: approveLocationId })
  }

  const handleRejectClick = (row: PendingTableRow) => {
    if (row.entityType !== "stock_receipt") {
      toast.error("Loại chứng từ này chưa hỗ trợ từ chối từ màn hình này.")
      return
    }
    setRejectEntityId(row.entityId)
    setRejectionReason("")
  }

  const confirmReject = () => {
    if (!rejectionReason.trim()) {
      toast.error("Vui lòng nhập lý do từ chối")
      return
    }
    if (rejectEntityId != null) {
      rejectMutation.mutate({ entityId: rejectEntityId, reason: rejectionReason.trim() })
    }
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-4 md:space-y-6 h-full flex flex-col bg-slate-50/30">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="text-left">
          <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight uppercase">Chờ phê duyệt</h1>
          <p className="text-sm text-slate-500 mt-1 font-medium">Danh sách các giao dịch đang chờ Chủ cửa hàng xét duyệt</p>
        </div>
        <div className="bg-amber-50 px-5 py-3 rounded-2xl border border-amber-100 flex items-center gap-3 shadow-sm shadow-amber-50">
          <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600">
            <AlertCircle size={20} />
          </div>
          <div>
            <p className="text-[10px] font-black uppercase text-amber-600/60 tracking-widest">Tiến độ xét duyệt</p>
            <p className="text-sm font-black text-amber-700">
              {pendingQuery.isFetching ? "…" : (summary?.totalPending ?? total)} Giao dịch cần xử lý
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white p-4 rounded-2xl border border-slate-200/60 shadow-sm flex flex-wrap items-end gap-5">
        <div className="space-y-2 flex-1 min-w-[200px]">
          <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
            <Search size={12} /> Tìm mã / người tạo
          </Label>
          <Input
            value={searchCode}
            onChange={(e) => setSearchCode(e.target.value)}
            placeholder="Mã phiếu, tên người tạo…"
            className="h-11 border-slate-200 focus:ring-0 focus:border-slate-900 rounded-xl bg-slate-50/30 text-sm font-bold"
          />
        </div>

        <div className="space-y-2 min-w-[140px]">
          <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 px-1">Loại</Label>
          <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v as "all" | "Inbound")}>
            <SelectTrigger className="h-11 rounded-xl font-bold">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tất cả</SelectItem>
              <SelectItem value="Inbound">Nhập kho</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
            <Calendar size={12} /> Từ ngày
          </Label>
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="h-11 border-slate-200 focus:ring-0 focus:border-slate-900 rounded-xl bg-slate-50/30 text-sm font-bold w-44"
          />
        </div>

        <div className="space-y-2">
          <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
            <Calendar size={12} /> Đến ngày
          </Label>
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="h-11 border-slate-200 focus:ring-0 focus:border-slate-900 rounded-xl bg-slate-50/30 text-sm font-bold w-44"
          />
        </div>

        <Button
          variant="outline"
          onClick={resetFilters}
          className="h-11 px-4 border-slate-200 rounded-xl text-slate-400 hover:text-slate-900 transition-all"
          title="Làm mới bộ lọc"
        >
          <RotateCcw size={18} />
        </Button>
      </div>

      {pendingQuery.isError ? (
        <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm font-medium text-red-800">
          Không tải được danh sách chờ phê duyệt.{" "}
          <Button variant="link" className="p-0 h-auto font-bold" onClick={() => void pendingQuery.refetch()}>
            Thử lại
          </Button>
        </div>
      ) : null}

      <div className={DATA_TABLE_SHELL_CLASS}>
        <div className={DATA_TABLE_SCROLL_CLASS}>
          <OrderTable
            data={displayData}
            selectedIds={[]}
            onSelect={() => {}}
            onSelectAll={() => {}}
            showCheckbox={false}
            onView={(item) => {
              setSelectedOrder(item)
              setIsDetailOpen(true)
            }}
            renderCustomActions={(item) => {
              const row = item as PendingTableRow
              return (
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleApproveClick(row)
                    }}
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                    title="Phê duyệt"
                  >
                    <CheckCircle2 size={18} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-400 hover:text-red-600 hover:bg-red-50 transition-all"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRejectClick(row)
                    }}
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                    title="Từ chối"
                  >
                    <XCircle size={18} />
                  </Button>
                </div>
              )
            }}
          />
        </div>
        {total > PAGE_SIZE ? (
          <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
            <span>
              Trang {page} / {totalPages} — {total} bản ghi
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page <= 1 || pendingQuery.isFetching}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Trước
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page >= totalPages || pendingQuery.isFetching}
                onClick={() => setPage((p) => p + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        ) : null}
      </div>

      <Dialog open={approveEntityId !== null} onOpenChange={(o) => !o && setApproveEntityId(null)}>
        <DialogContent className="max-w-md rounded-2xl border-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-black uppercase">Chọn vị trí nhập kho</DialogTitle>
            <DialogDescription>
              Phiếu nhập cần vị trí đích khi phê duyệt (Task019). Mặc định có thể đổi trước khi xác nhận.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label className="text-[10px] font-black uppercase text-slate-400">Vị trí</Label>
            <Select
              value={String(approveLocationId)}
              onValueChange={(v) => setApproveLocationId(Number(v))}
            >
              <SelectTrigger className="h-11 rounded-xl font-bold">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS.map((opt) => (
                  <SelectItem key={opt.id} value={String(opt.id)}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="ghost" onClick={() => setApproveEntityId(null)} className="rounded-xl font-bold">
              Hủy
            </Button>
            <Button
              className="rounded-xl font-black uppercase bg-emerald-600 hover:bg-emerald-700"
              onClick={confirmApprove}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? "Đang xử lý…" : "Phê duyệt"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rejectEntityId !== null} onOpenChange={(o) => !o && setRejectEntityId(null)}>
        <DialogContent className="max-w-md p-0 overflow-hidden border-slate-200 shadow-2xl rounded-2xl">
          <DialogHeader className="p-8 pb-6 bg-slate-50/50 border-b border-slate-100 relative overflow-hidden">
            <div className="absolute -right-4 -top-4 size-32 text-red-100/50 rotate-12">
              <XCircle size={128} />
            </div>
            <div className="flex items-center gap-4 mb-3 relative z-10">
              <div className="h-12 w-12 rounded-2xl bg-red-600 text-white flex items-center justify-center shadow-lg shadow-red-200">
                <AlertCircle size={24} />
              </div>
              <div>
                <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-0.5">Xác nhận hành động</p>
                <DialogTitle className="text-2xl font-black text-slate-900 uppercase italic">Từ chối phê duyệt</DialogTitle>
              </div>
            </div>
            <DialogDescription className="text-slate-500 font-medium relative z-10">
              Cần cung cấp lý do cụ thể để nhân viên liên quan nắm bắt và điều chỉnh lại giao dịch.
            </DialogDescription>
          </DialogHeader>

          <div className="p-8 space-y-6">
            <div className="space-y-2.5">
              <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
                Lý do từ chối (Bắt buộc)
              </Label>
              <Input
                placeholder="VD: Sai thông tin hóa đơn, sai số lượng..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="h-12 border-slate-200 focus:ring-0 focus:border-slate-900 rounded-xl bg-slate-50/30 text-sm font-bold"
                autoFocus
              />
            </div>
          </div>

          <DialogFooter className="p-6 bg-slate-50 border-t border-slate-100 flex gap-3">
            <Button variant="ghost" onClick={() => setRejectEntityId(null)} className="px-6 font-bold text-slate-400 hover:text-slate-900 rounded-xl">
              Hủy
            </Button>
            <Button
              variant="destructive"
              onClick={confirmReject}
              disabled={rejectMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white px-8 font-black uppercase tracking-widest shadow-lg shadow-red-100 rounded-xl"
            >
              {rejectMutation.isPending ? "Đang xử lý…" : "Xác nhận từ chối"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <OrderDetailDialog order={selectedOrder} isOpen={isDetailOpen} onClose={() => setIsDetailOpen(false)} />
    </div>
  )
}
