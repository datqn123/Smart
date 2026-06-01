import { useEffect, useMemo, useRef, useState } from "react"
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import { usePageTitle } from "@/context/PageTitleContext"
import { Truck, Search, Calendar, Plus, Check } from "lucide-react"
import type { StockDispatch } from "../types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "sonner"

import { DispatchTable } from "../components/DispatchTable"
import { DispatchDetailDialog } from "../components/DispatchDetailDialog"
import { DispatchForm, type DispatchFormData } from "../components/DispatchForm"
import { ManualDispatchEditDialog } from "../components/ManualDispatchEditDialog"
import {
  approveStockDispatch,
  getStockDispatchDetail,
  getStockDispatchList,
  mapStockDispatchListItemToUi,
  postStockDispatch,
  softDeleteStockDispatch,
} from "../api/dispatchApi"
import { ApiRequestError } from "@/lib/api/http"
import { cn } from "@/lib/utils"
import { DATA_TABLE_SHELL_CLASS, DATA_TABLE_SCROLL_CLASS } from "@/lib/data-table-layout"
import { useTableColumnOrder } from "../hooks/useTableVisibleColumns"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

const statusOptions = [
  { value: "all", label: "Tất cả trạng thái" },
  { value: "WaitingDispatch", label: "Chờ xuất (xuất tay)" },
  { value: "Delivering", label: "Đang giao" },
  { value: "Delivered", label: "Đã giao" },
  { value: "Pending", label: "Chờ duyệt (đơn)" },
  { value: "Full", label: "Đủ hàng" },
  { value: "Partial", label: "Một phần" },
  { value: "Cancelled", label: "Đã hủy" },
]

export function DispatchPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const role = useAuthStore((s) => s.user?.role)
  const isAdmin = role === "Admin"
  const [searchParams, setSearchParams] = useSearchParams()
  const { setTitle } = usePageTitle()

  const [search, setSearch] = useState("")
  const visibleColumnKeys = useTableColumnOrder("inventory_dispatch", [
    "dispatchCode",
    "orderCode",
    "customerName",
    "dispatchDate",
    "userName",
    "itemCount",
    "status",
  ])
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [onlyMine, setOnlyMine] = useState(false)

  const [selectedDispatch, setSelectedDispatch] = useState<StockDispatch | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingDispatch, setEditingDispatch] = useState<StockDispatch | undefined>()
  const [manualEditOpen, setManualEditOpen] = useState(false)
  const [manualEditId, setManualEditId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)
  const [deleteReason, setDeleteReason] = useState("")
  const scrollRootRef = useRef<HTMLDivElement>(null)
  const loadMoreSentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setTitle("Phiếu xuất kho")
  }, [setTitle])

  const highlightId = searchParams.get("highlight")
  useEffect(() => {
    if (!highlightId) {
      return
    }
    const id = parseInt(highlightId, 10)
    if (Number.isNaN(id)) {
      return
    }
    toast.success(`Đã tạo phiếu xuất #${id}`)
    setSearchParams({}, { replace: true })
  }, [highlightId, setSearchParams])

  const listQueryKey = useMemo(
    () =>
      [
        "stock-dispatches",
        "v1",
        "list",
        debouncedSearch,
        statusFilter,
        dateFrom,
        dateTo,
        onlyMine,
        PAGE_SIZE,
      ] as const,
    [debouncedSearch, statusFilter, dateFrom, dateTo, onlyMine],
  )

  const panelDetailQuery = useQuery({
    queryKey: ["stock-dispatch-detail", selectedDispatch?.id ?? 0],
    queryFn: () => getStockDispatchDetail(selectedDispatch!.id),
    enabled: isPanelOpen && selectedDispatch != null && selectedDispatch.id > 0,
  })

  const approveStockDispatchMutation = useMutation({
    mutationFn: async () => approveStockDispatch(selectedDispatch!.id),
    onSuccess: async () => {
      toast.success("Đã duyệt phiếu — chuyển chờ xuất")
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatch-detail", selectedDispatch!.id] })
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatches", "v1", "list"] })
    },
    onError: (e: unknown) => {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không duyệt được phiếu")
      }
      else {
        toast.error("Không duyệt được phiếu")
      }
    },
  })

  const softDeleteMutation = useMutation({
    mutationFn: () =>
      softDeleteStockDispatch(
        confirmDeleteId!,
        deleteReason.trim(),
      ),
    onSuccess: async () => {
      toast.success("Đã xóa mềm phiếu")
      setConfirmDeleteId(null)
      setDeleteReason("")
      setIsPanelOpen(false)
      setSelectedDispatch(null)
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatches", "v1", "list"] })
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatch-detail"] })
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không xóa được phiếu")
      }
      else {
        toast.error("Không xóa được phiếu")
      }
    },
  })

  const { data, isPending, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
      queryKey: listQueryKey,
      initialPageParam: 1,
      queryFn: async ({ pageParam }) => {
        const page = pageParam as number
        return getStockDispatchList({
          search: debouncedSearch.trim() || undefined,
          page,
          limit: PAGE_SIZE,
          status: statusFilter === "all" ? undefined : statusFilter,
          dateFrom: dateFrom || undefined,
          dateTo: dateTo || undefined,
          mine: onlyMine ? true : undefined,
        })
      },
      getNextPageParam: (lastPage) => {
        if (lastPage.items.length < PAGE_SIZE) {
          return undefined
        }
        if (lastPage.page * lastPage.limit >= lastPage.total) {
          return undefined
        }
        return lastPage.page + 1
      },
    })

  const dispatches = useMemo(() => {
    const pages = data?.pages ?? []
    const rows: StockDispatch[] = []
    for (const p of pages) {
      for (const it of p.items) {
        rows.push(mapStockDispatchListItemToUi(it))
      }
    }
    return rows
  }, [data?.pages])

  useEffect(() => {
    const root = scrollRootRef.current
    const sentinel = loadMoreSentinelRef.current
    if (!root || !sentinel) {
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const e = entries[0]
        if (e?.isIntersecting && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      },
      { root, rootMargin: "80px", threshold: 0 },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage, data?.pages])

  useEffect(() => {
    if (isError && error instanceof ApiRequestError) {
      toast.error(error.body?.message ?? "Không tải được danh sách phiếu xuất")
    }
  }, [isError, error])

  const handleCreateDispatch = () => {
    setEditingDispatch(undefined)
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (data: DispatchFormData) => {
    try {
      const created = await postStockDispatch({
        dispatchDate: data.dispatchDate,
        referenceLabel: data.referenceLabel?.trim() || undefined,
        notes: data.notes?.trim() || undefined,
        lines: data.items.map((it) => ({
          inventoryId: it.inventoryId,
          quantity: it.dispatchQty,
          unitPriceSnapshot: Number(it.unitPriceSnapshot),
        })),
      })
      toast.success(`Đã tạo phiếu ${created.dispatchCode}`)
      await queryClient.invalidateQueries({ queryKey: ["stock-dispatches", "v1", "list"] })
      navigate(`/inventory/dispatch?highlight=${created.id}`)
    }
    catch (e) {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không tạo được phiếu")
      }
      else {
        toast.error("Không tạo được phiếu")
      }
      throw e
    }
  }

  const total = data?.pages[0]?.total ?? 0

  return (
    <div className="h-full flex flex-col p-4 md:p-6 lg:p-8 gap-4 md:gap-5 overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-medium text-slate-900" style={{ letterSpacing: "-0.02em" }}>
            Phiếu xuất kho
          </h1>
          <p className="text-sm text-slate-500 mt-1">Danh sách phiếu xuất từ hệ thống</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleCreateDispatch} className="h-11 bg-slate-900 hover:bg-slate-800 text-white">
            <Plus className="h-4 w-4 mr-2" /> Tạo phiếu xuất
          </Button>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg border border-slate-200 space-y-3 shrink-0">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Tìm theo mã phiếu, đơn hàng, khách…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-11 bg-slate-50/50 border-slate-200 focus:bg-white transition-all"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-11 px-3 border border-slate-200 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400 w-full sm:w-[180px] rounded-md transition-all"
          >
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-slate-400" />
              <span className="text-xs text-slate-500">Từ ngày:</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="h-9 px-2 border border-slate-200 text-sm rounded bg-slate-50/50"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Đến ngày:</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="h-9 px-2 border border-slate-200 text-sm rounded bg-slate-50/50"
              />
            </div>
            <button
              type="button"
              onClick={() => setOnlyMine((v) => !v)}
              aria-pressed={onlyMine}
              className={cn(
                "inline-flex items-center gap-2 h-9 px-3 rounded-md border text-sm font-semibold transition-colors shrink-0",
                onlyMine
                  ? "border-slate-900 bg-slate-900 text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
              )}
            >
              <span
                className={cn(
                  "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
                  onlyMine ? "border-white bg-white" : "border-slate-300 bg-white",
                )}
                aria-hidden
              >
                {onlyMine ? <Check className="h-3 w-3 text-slate-900" strokeWidth={3} /> : null}
              </span>
              Phiếu của tôi
            </button>
          </div>
        </div>
      </div>

      <div className={DATA_TABLE_SHELL_CLASS}>
        <div
          ref={scrollRootRef}
          data-testid="dispatch-list-container"
          className={DATA_TABLE_SCROLL_CLASS}
        >
          {isPending && dispatches.length === 0 ? (
            <div className="text-center py-20 text-slate-500 text-sm">Đang tải…</div>
          ) : dispatches.length === 0 ? (
            <div className="text-center py-20 bg-white">
              <Truck className="h-16 w-16 text-slate-200 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">Không tìm thấy phiếu nào</h3>
              <p className="text-slate-500 text-sm max-w-xs mx-auto">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm</p>
              <Button
                onClick={() => {
                  setSearch("")
                  setStatusFilter("all")
                  setDateFrom("")
                  setDateTo("")
                  setOnlyMine(false)
                }}
                variant="link"
                className="mt-2 text-slate-900"
              >
                Xóa tất cả bộ lọc
              </Button>
            </div>
          ) : (
            <>
              <DispatchTable
                dispatches={dispatches}
                visibleColumnKeys={visibleColumnKeys}
                onAction={(d) => {
                  setSelectedDispatch(d)
                  setIsPanelOpen(true)
                }}
                onEdit={(d) => {
                  setManualEditId(d.id)
                  setManualEditOpen(true)
                }}
                onDelete={(id) => {
                  setConfirmDeleteId(id)
                  setDeleteReason("")
                }}
              />
              {isFetchingNextPage && (
                <div className="flex justify-center p-6 bg-slate-50/30">
                  <div className="animate-spin h-6 w-6 border-2 border-slate-300 border-t-slate-900 rounded-full" />
                </div>
              )}
              {hasNextPage && !isFetchingNextPage && <div ref={loadMoreSentinelRef} className="h-10" />}
            </>
          )}
        </div>
        {data && total > 0 && !isError && (
          <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
            <span>
              Đang hiển thị {dispatches.length} / {total} bản ghi
            </span>
            {isFetchingNextPage && (
              <span className="text-slate-500">Đang tải thêm…</span>
            )}
            {hasNextPage && !isFetchingNextPage && (
              <span className="text-slate-400 text-xs hidden sm:inline">Cuộn xuống để tải thêm</span>
            )}
          </div>
        )}
      </div>

      <DispatchDetailDialog
        dispatch={selectedDispatch}
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
        canApprove={true}
        canApproveStockLines={isAdmin}
        onApproveStockDispatch={() => approveStockDispatchMutation.mutate()}
        approveStockDispatchPending={approveStockDispatchMutation.isPending}
        detailFromApi={panelDetailQuery.data ?? null}
        detailLoading={panelDetailQuery.isFetching}
      />

      <ManualDispatchEditDialog
        open={manualEditOpen}
        dispatchId={manualEditId}
        onOpenChange={(o) => {
          setManualEditOpen(o)
          if (!o) {
            setManualEditId(null)
          }
        }}
      />

      <Dialog
        open={confirmDeleteId != null}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmDeleteId(null)
            setDeleteReason("")
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Xóa mềm phiếu xuất</DialogTitle>
            <DialogDescription>
              Ghi rõ lý do để người tạo phiếu tra cứu sau này. Thao tác không khôi phục từ giao diện này.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="dispatch-del-reason">Lý do xóa</Label>
            <Textarea
              id="dispatch-del-reason"
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              placeholder="Tối thiểu 3 ký tự"
              rows={3}
              className="resize-none"
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setConfirmDeleteId(null)
                setDeleteReason("")
              }}
              disabled={softDeleteMutation.isPending}
            >
              Hủy
            </Button>
            <Button
              type="button"
              className="bg-red-600 hover:bg-red-700 text-white"
              disabled={softDeleteMutation.isPending || deleteReason.trim().length < 3}
              onClick={() => softDeleteMutation.mutate()}
            >
              {softDeleteMutation.isPending ? "Đang xóa…" : "Xóa mềm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <DispatchForm open={isFormOpen} onOpenChange={setIsFormOpen} dispatch={editingDispatch} onSubmit={handleFormSubmit} />
    </div>
  )
}
