import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { OrderDetailDialog } from "@/features/orders/components/OrderDetailDialog"
import type { Order } from "@/features/orders/types"
import { Button } from "@/components/ui/button"
import { History, Search, Calendar, RotateCcw, Filter } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { DATA_TABLE_SCROLL_CLASS, DATA_TABLE_SHELL_CLASS } from "@/lib/data-table-layout"
import { toastApiError } from "@/lib/api/toastApiError"
import {
  APPROVALS_HISTORY_QUERY_KEY,
  getApprovalsHistory,
  type ApprovalsHistoryItem,
} from "@/features/approvals/api/approvalsApi"
import { ApprovalHistoryTable } from "@/features/approvals/components/ApprovalHistoryTable"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

function toNumber(v: number | string): number {
  return typeof v === "number" ? v : Number(v)
}

function historyRowToOrder(row: ApprovalsHistoryItem): Order {
  const amt = toNumber(row.totalAmount)
  const noteParts = [
    row.resolution === "Rejected" && row.rejectionReason ? `Lý do: ${row.rejectionReason}` : null,
    row.reviewerName ? `Người xử lý: ${row.reviewerName}` : null,
    row.reviewedAt ? `Thời điểm xử lý: ${row.reviewedAt}` : null,
  ].filter(Boolean)
  return {
    id: row.entityId,
    orderCode: row.transactionCode,
    customerName: row.creatorName,
    date: row.date,
    totalAmount: amt,
    finalAmount: amt,
    status: row.resolution as unknown as Order["status"],
    type: "Wholesale",
    itemsCount: 0,
    paymentStatus: "Paid",
    notes: noteParts.length ? noteParts.join("\n") : row.notes ?? undefined,
  }
}

export default function ApprovalHistoryPage() {
  const { setTitle } = usePageTitle()

  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)

  const [searchCode, setSearchCode] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [resolutionFilter, setResolutionFilter] = useState<"all" | "Approved" | "Rejected">("all")
  const [typeFilter, setTypeFilter] = useState<"all" | "Inbound">("all")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [page, setPage] = useState(1)

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(searchCode.trim()), SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(t)
  }, [searchCode])

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, resolutionFilter, typeFilter, startDate, endDate])

  useEffect(() => {
    setTitle("Lịch sử phê duyệt")
  }, [setTitle])

  const filters = useMemo(
    () => ({
      resolution: resolutionFilter,
      search: debouncedSearch || undefined,
      type: typeFilter,
      fromDate: startDate || undefined,
      toDate: endDate || undefined,
      page,
      limit: PAGE_SIZE,
    }),
    [resolutionFilter, debouncedSearch, typeFilter, startDate, endDate, page],
  )

  const historyQuery = useQuery({
    queryKey: [...APPROVALS_HISTORY_QUERY_KEY, filters],
    queryFn: () => getApprovalsHistory(filters),
  })

  useEffect(() => {
    if (historyQuery.isError) toastApiError(historyQuery.error)
  }, [historyQuery.isError, historyQuery.error])

  const items = historyQuery.data?.items ?? []
  const total = historyQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const resetFilters = () => {
    setSearchCode("")
    setResolutionFilter("all")
    setTypeFilter("all")
    setStartDate("")
    setEndDate("")
    setPage(1)
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 space-y-4 md:space-y-6 h-full flex flex-col bg-slate-50/30">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="text-left">
          <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight uppercase">Lịch sử phê duyệt</h1>
          <p className="text-sm text-slate-500 mt-1 font-medium">Tra cứu các giao dịch đã được xử lý trong quá khứ</p>
        </div>
        <div className="bg-slate-100 px-5 py-3 rounded-2xl border border-slate-200 flex items-center gap-3 shadow-sm">
          <div className="h-10 w-10 rounded-full bg-white flex items-center justify-center text-slate-600 shadow-sm">
            <History size={20} />
          </div>
          <div>
            <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Tổng lưu trữ</p>
            <p className="text-sm font-black text-slate-700">
              {historyQuery.isFetching ? "…" : total} Giao dịch
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white p-4 rounded-2xl border border-slate-200/60 shadow-sm flex flex-wrap items-end gap-5">
        <div className="space-y-2 flex-1 min-w-[200px]">
          <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
            <Search size={12} /> Tìm kiếm
          </Label>
          <Input
            value={searchCode}
            onChange={(e) => setSearchCode(e.target.value)}
            placeholder="Mã phiếu, người tạo hoặc người duyệt…"
            className="h-11 border-slate-200 focus:ring-0 focus:border-slate-900 rounded-xl bg-slate-50/30 text-sm font-bold"
          />
        </div>

        <div className="space-y-2 min-w-[160px]">
          <Label className="text-[10px] font-black uppercase tracking-widest text-slate-400 flex items-center gap-2 px-1">
            <Filter size={12} /> Kết quả
          </Label>
          <Select
            value={resolutionFilter}
            onValueChange={(v) => setResolutionFilter(v as "all" | "Approved" | "Rejected")}
          >
            <SelectTrigger className="h-11 border-slate-200 focus:ring-0 focus:border-slate-900 rounded-xl bg-slate-50/30 text-sm font-bold">
              <SelectValue placeholder="Tất cả" />
            </SelectTrigger>
            <SelectContent className="rounded-xl border-slate-200 shadow-xl">
              <SelectItem value="all" className="font-bold">
                Tất cả
              </SelectItem>
              <SelectItem value="Approved" className="text-emerald-600 font-bold">
                Đã phê duyệt
              </SelectItem>
              <SelectItem value="Rejected" className="text-red-600 font-bold">
                Đã từ chối
              </SelectItem>
            </SelectContent>
          </Select>
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
            <Calendar size={12} /> Từ ngày (theo ngày xử lý)
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
        >
          <RotateCcw size={18} />
        </Button>
      </div>

      {historyQuery.isError ? (
        <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm font-medium text-red-800">
          Không tải được lịch sử phê duyệt.{" "}
          <Button variant="link" className="p-0 h-auto font-bold" onClick={() => void historyQuery.refetch()}>
            Thử lại
          </Button>
        </div>
      ) : null}

      <div className={DATA_TABLE_SHELL_CLASS}>
        <div className={DATA_TABLE_SCROLL_CLASS}>
          <ApprovalHistoryTable
            items={items}
            onView={(row) => {
              setSelectedOrder(historyRowToOrder(row))
              setIsDetailOpen(true)
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
                disabled={page <= 1 || historyQuery.isFetching}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Trước
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page >= totalPages || historyQuery.isFetching}
                onClick={() => setPage((p) => p + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        ) : null}
      </div>

      <OrderDetailDialog order={selectedOrder} isOpen={isDetailOpen} onClose={() => setIsDetailOpen(false)} />
    </div>
  )
}
