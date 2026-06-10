import { useEffect, useMemo, useRef, useState } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { Plus, Search, Calendar, Check } from "lucide-react"
import type { StockReceipt } from "../types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { ReceiptTable } from "../components/ReceiptTable"
import { ReceiptDetailDialog } from "../components/ReceiptDetailDialog"
import { ReceiptForm, type ReceiptFormData } from "../components/ReceiptForm"
import {
  getStockReceiptList,
  getStockReceiptById,
  mapStockReceiptListItemToUi,
  mapStockReceiptViewToUi,
  patchStockReceipt,
  postStockReceipt,
  deleteStockReceipt,
  submitStockReceipt,
  type GetStockReceiptListParams,
  type StockReceiptCreateSaveMode,
} from "../api/stockReceiptsApi"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import { DATA_TABLE_SHELL_CLASS, DATA_TABLE_SCROLL_CLASS } from "@/lib/data-table-layout"
import { useTableColumnOrder } from "../hooks/useTableVisibleColumns"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

const RECEIPT_STATUS_FILTERS = [
  { value: "all", label: "Tất cả" },
  { value: "Draft", label: "Nháp" },
  { value: "Pending", label: "Chờ duyệt" },
  { value: "Approved", label: "Đã duyệt" },
  { value: "Rejected", label: "Từ chối" },
] as const

function parseSupplierId(raw: string): number | undefined {
  const t = raw.trim()
  if (!/^\d+$/.test(t)) {
    return undefined
  }
  const n = parseInt(t, 10)
  return n > 0 ? n : undefined
}

// ─── Main Page ────────────────────────────────────────────
export function InboundPage() {
  const queryClient = useQueryClient()
  const { setTitle } = usePageTitle()
  const user = useAuthStore((s) => s.user)
  const role = user?.role
  const canApprovePerm = useAuthStore((s) => s.menuPermissions.can_approve)
  const userCanApprove = Boolean(role === "Admin" || role === "Owner") && canApprovePerm

  const canDeleteReceipt = (r: StockReceipt) => {
    if (r.status === "Pending") return role === "Staff" || role === "Admin" || role === "Owner"
    if (r.status === "Draft") return role === "Owner"
    return false
  }
  const scrollRootRef = useRef<HTMLDivElement>(null)
  const loadMoreSentinelRef = useRef<HTMLDivElement>(null)

  const [search, setSearch] = useState("")
  const visibleColumnKeys = useTableColumnOrder("inventory_receipts", [
    "receiptCode",
    "supplierName",
    "receiptDate",
    "staffName",
    "invoiceNumber",
    "lineCount",
    "totalAmount",
    "status",
  ])
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS)
  const [statusFilter, setStatusFilter] = useState("all")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [supplierFilter, setSupplierFilter] = useState("")
  const [onlyMine, setOnlyMine] = useState(false)

  const [selectedReceipt, setSelectedReceipt] = useState<StockReceipt | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingReceipt, setEditingReceipt] = useState<StockReceipt | undefined>()

  const supplierIdParam = parseSupplierId(supplierFilter)

  useEffect(() => { setTitle("Phiếu nhập kho") }, [setTitle])

  const listQueryKey = useMemo(
    () =>
      [
        "stock-receipts",
        "v1",
        "list",
        debouncedSearch,
        statusFilter,
        dateFrom,
        dateTo,
        supplierIdParam ?? "",
        onlyMine,
        user?.id ?? 0,
        PAGE_SIZE,
      ] as const,
    [debouncedSearch, statusFilter, dateFrom, dateTo, supplierIdParam, onlyMine, user?.id],
  )

  const {
    data: receiptDetail,
    isPending: isDetailPending,
    isError: isDetailError,
    error: detailError,
  } = useQuery({
    queryKey: ["stock-receipts", "v1", "detail", selectedReceipt?.id],
    queryFn: async () => {
      const raw = await getStockReceiptById(selectedReceipt!.id)
      return mapStockReceiptViewToUi(raw)
    },
    enabled: isPanelOpen && selectedReceipt != null,
  })

  const receiptForDialog = receiptDetail ?? selectedReceipt

  const { data, isPending, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: listQueryKey,
    initialPageParam: 1,
    queryFn: ({ pageParam }) => {
      const base: GetStockReceiptListParams = {
        search: debouncedSearch.trim() || undefined,
        status: statusFilter as GetStockReceiptListParams["status"],
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
        supplierId: supplierIdParam,
        mine: onlyMine && user != null && user.id > 0 ? true : undefined,
        page: pageParam,
        limit: PAGE_SIZE,
        sort: "createdAt:desc",
      }
      return getStockReceiptList(base)
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.items.length < lastPage.limit) {
        return undefined
      }
      if (lastPage.page * lastPage.limit >= lastPage.total) {
        return undefined
      }
      return lastPage.page + 1
    },
  })

  const mergedRows: StockReceipt[] = useMemo(
    () => (data?.pages ? data.pages.flatMap((p) => p.items.map(mapStockReceiptListItemToUi)) : []),
    [data],
  )

  const supplierTrim = supplierFilter.trim().toLowerCase()
  const displayRows = useMemo(() => {
    if (supplierIdParam != null) {
      return mergedRows
    }
    if (!supplierTrim) {
      return mergedRows
    }
    return mergedRows.filter((r) => r.supplierName.toLowerCase().includes(supplierTrim))
  }, [mergedRows, supplierIdParam, supplierTrim])

  const firstPage = data?.pages[0]
  const serverTotal = firstPage?.total ?? 0

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
      const dr = error.body?.details?.dateRange
      if (error.status === 400 && dr) {
        toast.error(dr)
        return
      }
      if (error.status === 401 || error.status === 403) {
        toast.error(error.body?.message ?? "Bạn chưa đủ quyền xem phiếu nhập (can_manage_inventory).")
      } else {
        toast.error(error.body?.message ?? "Không tải được danh sách phiếu nhập")
      }
    }
  }, [isError, error])

  useEffect(() => {
    if (isDetailError && detailError instanceof ApiRequestError) {
      toast.error(detailError.body?.message ?? "Không tải được chi tiết phiếu nhập")
    }
  }, [isDetailError, detailError])

  const handleCreateReceipt = () => {
    setEditingReceipt(undefined)
    setIsFormOpen(true)
  }

  const handleEditReceipt = async (receipt: StockReceipt) => {
    try {
      const raw = await getStockReceiptById(receipt.id)
      setEditingReceipt(mapStockReceiptViewToUi(raw))
      setIsFormOpen(true)
    } catch (e) {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không tải được chi tiết phiếu để sửa")
      } else {
        toast.error("Không tải được chi tiết phiếu để sửa")
      }
    }
  }

  const handleDeleteReceipt = async (id: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa phiếu nhập này?")) {
      return
    }
    try {
      await deleteStockReceipt(id)
      toast.success("Đã xóa phiếu nhập kho")
      if (selectedReceipt?.id === id) {
        setIsPanelOpen(false)
        setSelectedReceipt(null)
      }
      await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "list"] })
      await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "detail", id] })
    } catch (e) {
      if (e instanceof ApiRequestError) {
        const det = e.body?.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body?.message ?? "Không xóa được phiếu nhập", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không xóa được phiếu nhập")
        }
      } else {
        toast.error("Không xóa được phiếu nhập")
      }
    }
  }

  const handleFormSubmit = async (data: ReceiptFormData, saveMode: StockReceiptCreateSaveMode) => {
    if (editingReceipt) {
      const patchBody = {
        supplierId: data.supplierId,
        receiptDate: data.receiptDate,
        invoiceNumber: data.invoiceNumber?.trim() ?? "",
        notes: data.notes?.trim() ? data.notes.trim() : null,
        details: data.details.map((d) => ({
          productId: d.productId,
          unitId: d.unitId,
          quantity: Math.floor(Number(d.quantity)),
          costPrice: d.costPrice,
          batchNumber: d.batchNumber?.trim() ? d.batchNumber.trim() : null,
          expiryDate: d.expiryDate?.trim() ? d.expiryDate.trim() : null,
        })),
      }
      try {
        await patchStockReceipt(editingReceipt.id, patchBody)
        if (saveMode === "pending") {
          await submitStockReceipt(editingReceipt.id)
          toast.success("Đã gửi phiếu chờ duyệt")
        } else {
          toast.success("Đã cập nhật phiếu nhập kho")
        }
        await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "list"] })
        await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "detail", editingReceipt.id] })
      } catch (e) {
        if (e instanceof ApiRequestError) {
          const det = e.body?.details
          if (det && typeof det === "object") {
            const desc = Object.entries(det)
              .map(([k, v]) => `${k}: ${v}`)
              .join("\n")
            toast.error(e.body?.message ?? "Không cập nhật được phiếu nhập", { description: desc })
          } else {
            toast.error(e.body?.message ?? "Không cập nhật được phiếu nhập")
          }
        } else {
          toast.error("Không cập nhật được phiếu nhập")
        }
        throw e
      }
      return
    }

    try {
      await postStockReceipt({
        supplierId: data.supplierId,
        receiptDate: data.receiptDate,
        invoiceNumber: data.invoiceNumber?.trim() || undefined,
        notes: data.notes?.trim() || undefined,
        saveMode,
        details: data.details.map((d) => ({
          productId: d.productId,
          unitId: d.unitId,
          quantity: Math.floor(Number(d.quantity)),
          costPrice: d.costPrice,
          batchNumber: d.batchNumber?.trim() ? d.batchNumber.trim() : null,
          expiryDate: d.expiryDate?.trim() ? d.expiryDate.trim() : null,
        })),
      })
      toast.success(saveMode === "draft" ? "Đã lưu nháp phiếu nhập kho" : "Đã gửi phiếu chờ duyệt")
      await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "list"] })
    } catch (e) {
      if (e instanceof ApiRequestError) {
        const det = e.body?.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body?.message ?? "Không tạo được phiếu nhập", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không tạo được phiếu nhập")
        }
      } else {
        toast.error("Không tạo được phiếu nhập")
      }
      throw e
    }
  }
  const showEmpty = !isPending && !isError && displayRows.length === 0
  const listLoaded = displayRows.length > 0

  return (
    <div className="h-full flex flex-col p-4 md:p-6 lg:p-8 gap-4 md:gap-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Phiếu nhập kho</h1>
          <p className="text-sm text-slate-500 mt-1">Theo dõi lịch sử nhập hàng từ nhà cung cấp</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleCreateReceipt} className="h-11 bg-slate-900 hover:bg-slate-800 text-white">
            <Plus className="h-4 w-4 mr-2" /> Tạo phiếu nhập
          </Button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-3 shrink-0">
        {/* Row 1: Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Mã phiếu, số hóa đơn…" value={search}
            onChange={(e) => setSearch(e.target.value)} className="pl-9 h-10" />
        </div>

        {/* Row 2: Quick-filter status tabs */}
        <div className="flex flex-wrap gap-1.5">
          {RECEIPT_STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setStatusFilter(f.value)}
              className={cn(
                "h-8 px-3 rounded-full text-sm font-medium transition-colors border",
                statusFilter === f.value
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-900",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Row 3: Date range + supplier + only-mine */}
        <div className="flex flex-wrap items-end gap-x-3 gap-y-2">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
            <span className="text-xs text-slate-500 whitespace-nowrap">Từ ngày:</span>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              className="h-9 px-2 border border-slate-200 rounded text-sm" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 whitespace-nowrap">Đến ngày:</span>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              className="h-9 px-2 border border-slate-200 rounded text-sm" />
          </div>
          <Input placeholder="NCC: nhập ID số hoặc lọc tên (đã tải)…" value={supplierFilter}
            onChange={(e) => setSupplierFilter(e.target.value)}
            className="h-9 min-w-[200px] w-[min(100%,280px)] shrink-0" />
          <button
            type="button"
            onClick={() => setOnlyMine((v) => !v)}
            aria-pressed={onlyMine}
            disabled={user == null || user.id <= 0}
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

      <div className={DATA_TABLE_SHELL_CLASS}>
        <div
          ref={scrollRootRef}
          data-testid="receipt-list-container"
          className={DATA_TABLE_SCROLL_CLASS}
        >
          {isPending && (
            <div className="flex justify-center py-20">
              <div className="animate-spin h-8 w-8 border-2 border-slate-300 border-t-slate-900 rounded-full" />
            </div>
          )}
          {showEmpty && (
            <div className="text-center py-16 bg-white">
              <Search className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-slate-900">Không tìm thấy phiếu nào</h3>
              <p className="text-slate-500">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm</p>
            </div>
          )}
          {listLoaded && (
            <>
              <ReceiptTable
                receipts={displayRows}
                visibleColumnKeys={visibleColumnKeys}
                onAction={(r) => {
                  setSelectedReceipt(r);
                  setIsPanelOpen(true);
                }}
                onEdit={handleEditReceipt}
                onDelete={handleDeleteReceipt}
                canDeleteReceipt={canDeleteReceipt}
              />

              {isFetchingNextPage && (
                <div className="flex justify-center p-4">
                  <div className="animate-spin h-6 w-6 border-2 border-slate-300 border-t-slate-900 rounded-full" />
                </div>
              )}

              {hasNextPage && !isFetchingNextPage && (
                <div ref={loadMoreSentinelRef} className="h-4" />
              )}
            </>
          )}
        </div>

        {data && serverTotal > 0 && !isError && (
          <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
            <span>
              Đang hiển thị {displayRows.length} / {serverTotal} bản ghi
            </span>
            {isFetchingNextPage && (
              <span className="text-slate-500">Đang tải thêm…</span>
            )}
            {hasNextPage && !isFetchingNextPage && (
              <span className="text-slate-400 text-xs hidden sm:inline">Cuộn xuống để tải thêm</span>
            )}
          </div>
        )}

        <ReceiptDetailDialog
          receipt={receiptForDialog}
          isOpen={isPanelOpen}
          onClose={() => {
            setIsPanelOpen(false)
            setSelectedReceipt(null)
          }}
          canApprove={userCanApprove}
          isLoadingDetail={isDetailPending}
          onAfterApprove={async (receiptId) => {
            await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "list"] })
            await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "detail", receiptId] })
          }}
        />

        <ReceiptForm
          open={isFormOpen}
          onOpenChange={setIsFormOpen}
          receipt={editingReceipt}
          onSubmit={handleFormSubmit}
          canApprove={userCanApprove}
          onAfterApproveOrReject={async (receiptId) => {
            await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "list"] })
            await queryClient.invalidateQueries({ queryKey: ["stock-receipts", "v1", "detail", receiptId] })
          }}
        />
      </div>
    </div>
  )
}
