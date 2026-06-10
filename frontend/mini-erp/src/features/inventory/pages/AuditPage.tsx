import { useEffect, useMemo, useRef, useState } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import { ClipboardCheck, Plus, Search, Calendar, Download, Upload } from "lucide-react"
import type { AuditSession } from "../types"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { AuditSessionsTable } from "../components/AuditSessionsTable"
import { AuditSessionCreateForm } from "../components/AuditSessionCreateForm"
import { AuditSessionCancelDialog } from "../components/AuditSessionCancelDialog"
import { AuditSessionDetailDialog } from "../components/AuditSessionDetailDialog"
import { AuditSessionPatchDialog } from "../components/AuditSessionPatchDialog"
import { toast } from "sonner"
import {
  getAuditSessionById,
  getAuditSessionList,
  mapAuditSessionDetailToUi,
  mapAuditSessionListItemToUi,
  patchAuditSession,
  patchAuditSessionLines,
  postAuditSession,
  postAuditSessionApprove,
  postAuditSessionCancel,
  postAuditSessionComplete,
  postAuditSessionReject,
  deleteAuditSessionSoft,
  type AuditLinesPatchBody,
  type AuditSessionCancelBody,
  type AuditSessionCompleteBody,
  type AuditSessionOwnerNotesBody,
  type AuditSessionPatchBody,
  type GetAuditSessionListParams,
} from "../api/auditSessionsApi"
import { ApiRequestError } from "@/lib/api/http"
import { useAuthStore } from "@/features/auth/store/useAuthStore"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

const statusOptions = [
  { value: "all", label: "Tất cả trạng thái" },
  { value: "Pending", label: "Chờ kiểm" },
  { value: "In Progress", label: "Đang kiểm" },
  { value: "Pending Owner Approval", label: "Chờ duyệt Owner" },
  { value: "Completed", label: "Hoàn thành" },
  { value: "Cancelled", label: "Đã hủy" },
  { value: "Re-check", label: "Kiểm lại" },
]

export function AuditPage() {
  const queryClient = useQueryClient()
  const isOwner = useAuthStore((s) => s.user?.role === "Owner")
  const { setTitle } = usePageTitle()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const scrollRootRef = useRef<HTMLDivElement>(null)
  const loadMoreSentinelRef = useRef<HTMLDivElement>(null)

  const [search, setSearch] = useState("")
  const debouncedSearch = useDebouncedValue(search, SEARCH_DEBOUNCE_MS)
  const [statusFilter, setStatusFilter] = useState("all")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [createOpen, setCreateOpen] = useState(false)
  const [viewSessionId, setViewSessionId] = useState<number | null>(null)
  const [viewListHint, setViewListHint] = useState<AuditSession | null>(null)
  const [editSessionId, setEditSessionId] = useState<number | null>(null)
  const [editListHint, setEditListHint] = useState<AuditSession | null>(null)
  const [cancelDialogSession, setCancelDialogSession] = useState<AuditSession | null>(null)

  useEffect(() => {
    setTitle("Kiểm kê kho")
  }, [setTitle])

  const listQueryKey = useMemo(
    () =>
      ["inventory", "audit-sessions", "v1", "list", debouncedSearch, statusFilter, dateFrom, dateTo, PAGE_SIZE] as const,
    [debouncedSearch, statusFilter, dateFrom, dateTo],
  )

  const { data, isPending, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: listQueryKey,
    initialPageParam: 1,
    queryFn: ({ pageParam }) => {
      const base: GetAuditSessionListParams = {
        search: debouncedSearch.trim() || undefined,
        status: statusFilter as GetAuditSessionListParams["status"],
        dateFrom: dateFrom || undefined,
        dateTo: dateTo || undefined,
        page: pageParam,
        limit: PAGE_SIZE,
      }
      return getAuditSessionList(base)
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

  const mergedRows: AuditSession[] = useMemo(
    () => (data?.pages ? data.pages.flatMap((p) => p.items.map(mapAuditSessionListItemToUi)) : []),
    [data],
  )

  const firstPage = data?.pages[0]
  const serverTotal = firstPage?.total ?? 0

  const detailOpen = viewSessionId != null
  const editOpen = editSessionId != null
  const activeDetailId = viewSessionId ?? editSessionId

  const {
    data: detailRaw,
    isPending: isDetailPending,
    isError: isDetailError,
    error: detailError,
  } = useQuery({
    queryKey: ["inventory", "audit-sessions", "v1", "detail", activeDetailId],
    queryFn: () => getAuditSessionById(activeDetailId!),
    enabled: activeDetailId != null,
  })

  const viewSessionDetail = useMemo(() => {
    if (!detailRaw || viewSessionId == null || detailRaw.id !== viewSessionId) return null
    return mapAuditSessionDetailToUi(detailRaw)
  }, [detailRaw, viewSessionId])

  const editSessionDetail = useMemo(() => {
    if (!detailRaw || editSessionId == null || detailRaw.id !== editSessionId) return null
    return mapAuditSessionDetailToUi(detailRaw)
  }, [detailRaw, editSessionId])

  const patchMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: AuditSessionPatchBody }) => patchAuditSession(id, body),
    onSuccess: () => {
      toast.success("Đã cập nhật đợt kiểm kê")
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
      setEditSessionId(null)
      setEditListHint(null)
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        const det = e.body.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body.message ?? "Không cập nhật được đợt kiểm kê", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không cập nhật được đợt kiểm kê")
        }
      } else {
        toast.error("Không cập nhật được đợt kiểm kê")
      }
    },
  })

  const linesPatchMutation = useMutation({
    mutationFn: ({ sessionId, body }: { sessionId: number; body: AuditLinesPatchBody }) =>
      patchAuditSessionLines(sessionId, body),
    onSuccess: () => {
      toast.success("Đã cập nhật số đếm")
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        const det = e.body.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body.message ?? "Không cập nhật được số đếm", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không cập nhật được số đếm")
        }
      } else {
        toast.error("Không cập nhật được số đếm")
      }
    },
  })

  const handlePatchLines = async (sessionId: number, body: AuditLinesPatchBody) => {
    await linesPatchMutation.mutateAsync({ sessionId, body })
  }

  const completeMutation = useMutation({
    mutationFn: ({ sessionId, body }: { sessionId: number; body: AuditSessionCompleteBody }) =>
      postAuditSessionComplete(sessionId, body),
    onSuccess: (detail) => {
      const s = mapAuditSessionDetailToUi(detail)
      if (s.status === "Pending Owner Approval") {
        toast.success("Đã gửi đợt kiểm kê chờ Owner duyệt")
      } else if (s.status === "Completed") {
        toast.success("Đợt kiểm kê đã hoàn thành")
      } else {
        toast.success(`Đã cập nhật trạng thái: ${s.status}`)
      }
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        const det = e.body.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body.message ?? "Không hoàn tất được đợt kiểm kê", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không hoàn tất được đợt kiểm kê")
        }
      } else {
        toast.error("Không hoàn tất được đợt kiểm kê")
      }
    },
  })

  const handleCompleteSession = async (sessionId: number, body: AuditSessionCompleteBody) => {
    await completeMutation.mutateAsync({ sessionId, body })
  }

  const cancelMutation = useMutation({
    mutationFn: ({ sessionId, body }: { sessionId: number; body: AuditSessionCancelBody }) =>
      postAuditSessionCancel(sessionId, body),
    onSuccess: () => {
      toast.success("Đã hủy đợt kiểm kê")
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
      setCancelDialogSession(null)
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        const det = e.body.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body.message ?? "Không hủy được đợt kiểm kê", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không hủy được đợt kiểm kê")
        }
      } else {
        toast.error("Không hủy được đợt kiểm kê")
      }
    },
  })

  const handleRequestCancel = (session: AuditSession) => {
    setCancelDialogSession(session)
  }

  const handleConfirmCancel = async (cancelReason: string) => {
    if (cancelDialogSession == null) return
    await cancelMutation.mutateAsync({ sessionId: cancelDialogSession.id, body: { cancelReason } })
  }

  const approveOwnerMutation = useMutation({
    mutationFn: ({ sessionId, body }: { sessionId: number; body: AuditSessionOwnerNotesBody }) =>
      postAuditSessionApprove(sessionId, body),
    onSuccess: () => {
      toast.success("Owner đã duyệt — đợt chuyển Hoàn thành")
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không duyệt được đợt kiểm kê")
      } else {
        toast.error("Không duyệt được đợt kiểm kê")
      }
    },
  })

  const rejectOwnerMutation = useMutation({
    mutationFn: ({ sessionId, body }: { sessionId: number; body: AuditSessionOwnerNotesBody }) =>
      postAuditSessionReject(sessionId, body),
    onSuccess: () => {
      toast.success("Owner đã từ chối — đợt trở lại Đang kiểm")
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không từ chối được đợt kiểm kê")
      } else {
        toast.error("Không từ chối được đợt kiểm kê")
      }
    },
  })

  const softDeleteOwnerMutation = useMutation({
    mutationFn: (sessionId: number) => deleteAuditSessionSoft(sessionId),
    onSuccess: () => {
      toast.success("Đã xóa mềm đợt kiểm kê (Owner)")
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "detail"] })
      closeDetail()
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không xóa mềm được đợt kiểm kê")
      } else {
        toast.error("Không xóa mềm được đợt kiểm kê")
      }
    },
  })

  const handleOwnerApprove = async (sessionId: number, body: AuditSessionOwnerNotesBody) => {
    await approveOwnerMutation.mutateAsync({ sessionId, body })
  }

  const handleOwnerReject = async (sessionId: number, body: AuditSessionOwnerNotesBody) => {
    await rejectOwnerMutation.mutateAsync({ sessionId, body })
  }

  const handleOwnerSoftDelete = async (sessionId: number) => {
    await softDeleteOwnerMutation.mutateAsync(sessionId)
  }

  const createMutation = useMutation({
    mutationFn: postAuditSession,
    onSuccess: (detail) => {
      toast.success(`Đã tạo đợt kiểm kê ${detail.auditCode}`)
      void queryClient.invalidateQueries({ queryKey: ["inventory", "audit-sessions", "v1", "list"] })
      setCreateOpen(false)
    },
    onError: (e) => {
      if (e instanceof ApiRequestError) {
        const det = e.body.details
        if (det && typeof det === "object") {
          const desc = Object.entries(det)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n")
          toast.error(e.body.message ?? "Không tạo được đợt kiểm kê", { description: desc })
        } else {
          toast.error(e.body?.message ?? "Không tạo được đợt kiểm kê")
        }
      } else {
        toast.error("Không tạo được đợt kiểm kê")
      }
    },
  })

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
        toast.error(error.body?.message ?? "Bạn chưa đủ quyền xem kiểm kê kho (can_manage_inventory).")
      } else {
        toast.error(error.body?.message ?? "Không tải được danh sách đợt kiểm kê")
      }
    }
  }, [isError, error])

  const handleExportExcel = () => {
    toast.info("Đang xuất dữ liệu Excel...")
  }
  const handleImportExcel = () => {
    fileInputRef.current?.click()
  }
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) toast.success(`Đã chọn file: ${file.name}. Đang xử lý import...`)
  }
  const handleCreateAudit = () => {
    setCreateOpen(true)
  }

  const handleView = (session: AuditSession) => {
    setEditSessionId(null)
    setEditListHint(null)
    setViewSessionId(session.id)
    setViewListHint(session)
  }

  const closeDetail = () => {
    setViewSessionId(null)
    setViewListHint(null)
  }

  const closeEdit = () => {
    setEditSessionId(null)
    setEditListHint(null)
  }

  const handleEdit = (session: AuditSession) => {
    setViewSessionId(null)
    setViewListHint(null)
    setEditSessionId(session.id)
    setEditListHint(session)
  }

  const handlePatchSubmit = async (body: AuditSessionPatchBody) => {
    if (editSessionId == null) return
    await patchMutation.mutateAsync({ id: editSessionId, body })
  }

  const showEmpty = !isPending && !isError && serverTotal === 0
  const listLoaded = mergedRows.length > 0
  const noFilters =
    debouncedSearch.trim() === "" && statusFilter === "all" && !dateFrom && !dateTo

  return (
    <div className="h-full flex flex-col min-h-0 overflow-hidden p-4 md:p-6 lg:p-8 gap-4 md:gap-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shrink-0">
        <div>
          <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">
            Kiểm kê kho
          </h1>
          <p className="text-sm text-slate-500 mt-1">Đối chiếu tồn kho hệ thống với thực tế</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={handleCreateAudit} className="h-11 bg-slate-900 hover:bg-slate-800 text-white">
            <Plus className="h-4 w-4 mr-2" /> Tạo đợt kiểm kê
          </Button>
          <Button onClick={handleExportExcel} variant="outline" className="h-11">
            <Download className="h-4 w-4 mr-2" /> Export
          </Button>
          <Button onClick={handleImportExcel} variant="outline" className="h-11">
            <Upload className="h-4 w-4 mr-2" /> Import
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls,.csv"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 shrink-0 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Tìm theo mã, tên đợt kiểm kê, người tạo..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-11"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-11 px-3 border border-slate-200 bg-white text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400 w-full sm:w-[200px] rounded-md"
          >
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 text-xs">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
            <span className="text-slate-500 whitespace-nowrap">Từ ngày:</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-9 px-2 border border-slate-200 rounded outline-none focus:ring-1 focus:ring-slate-400"
            />
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 whitespace-nowrap">Đến ngày:</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-9 px-2 border border-slate-200 rounded outline-none focus:ring-1 focus:ring-slate-400"
            />
          </div>
        </div>
        <p className="text-xs text-slate-500">
          Đã tải <span className="font-medium text-slate-700">{mergedRows.length}</span>
          {" · "}
          Tổng server: <span className="font-medium text-slate-700">{serverTotal}</span> đợt kiểm kê
        </p>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-transparent">
        <div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
          <div
            ref={scrollRootRef}
            data-testid="audit-session-list-container"
            className="flex-1 overflow-y-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0"
          >
            {isPending && (
              <div className="flex justify-center py-20">
                <div className="animate-spin h-8 w-8 border-2 border-slate-300 border-t-slate-900 rounded-full" />
              </div>
            )}
            {isError && (
              <div className="text-center py-16 px-4 text-slate-600 text-sm">
                Không tải được danh sách. Kiểm tra đăng nhập và quyền <code className="text-xs">can_manage_inventory</code>.
              </div>
            )}
            {showEmpty && (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-12 px-4">
                <ClipboardCheck className="h-12 w-12 text-slate-300 mb-3" />
                <p className="text-slate-600 text-sm mb-1 font-medium">
                  {noFilters ? "Chưa có đợt kiểm kê nào" : "Không có đợt kiểm kê khớp bộ lọc"}
                </p>
                {!noFilters && (
                  <p className="text-slate-500 text-xs mb-4">Thử đổi từ khóa hoặc khoảng ngày.</p>
                )}
                {noFilters && (
                  <Button onClick={handleCreateAudit} className="h-11 mt-4 bg-slate-900 hover:bg-slate-800 text-white">
                    <Plus className="h-4 w-4 mr-2" /> Tạo đợt kiểm kê
                  </Button>
                )}
              </div>
            )}
            {listLoaded && (
              <>
                <AuditSessionsTable
                  sessions={mergedRows}
                  onView={handleView}
                  onEdit={handleEdit}
                  onRequestCancel={handleRequestCancel}
                />
                {isFetchingNextPage && (
                  <div className="flex justify-center p-4">
                    <div className="animate-spin h-6 w-6 border-2 border-slate-300 border-t-slate-900 rounded-full" />
                  </div>
                )}
                {hasNextPage && !isFetchingNextPage && (
                  <div ref={loadMoreSentinelRef} className="h-4" />
                )}
                {!hasNextPage && mergedRows.length > 0 && (
                  <p className="text-center text-xs text-slate-400 py-6">
                    — Đã tải {mergedRows.length} / {serverTotal} đợt —
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <AuditSessionDetailDialog
        open={detailOpen}
        onClose={closeDetail}
        session={viewSessionDetail}
        listHint={viewListHint}
        isLoading={isDetailPending && detailOpen}
        isError={isDetailError && detailOpen}
        errorMessage={detailError instanceof ApiRequestError ? detailError.body.message : undefined}
        onPatchLines={handlePatchLines}
        linesPatchPending={linesPatchMutation.isPending}
        onCompleteSession={handleCompleteSession}
        completePending={completeMutation.isPending}
        isOwner={isOwner}
        onOwnerApprove={isOwner ? handleOwnerApprove : undefined}
        onOwnerReject={isOwner ? handleOwnerReject : undefined}
        onOwnerSoftDelete={isOwner ? handleOwnerSoftDelete : undefined}
        approveOwnerPending={approveOwnerMutation.isPending}
        rejectOwnerPending={rejectOwnerMutation.isPending}
        softDeleteOwnerPending={softDeleteOwnerMutation.isPending}
      />

      <AuditSessionPatchDialog
        open={editOpen}
        onClose={closeEdit}
        session={editSessionDetail}
        listHint={editListHint}
        isLoading={isDetailPending && editOpen}
        isError={isDetailError && editOpen}
        errorMessage={detailError instanceof ApiRequestError ? detailError.body.message : undefined}
        isSubmitting={patchMutation.isPending}
        onSubmit={handlePatchSubmit}
      />

      <AuditSessionCreateForm
        open={createOpen}
        onOpenChange={setCreateOpen}
        isSubmitting={createMutation.isPending}
        onSubmit={(body) => createMutation.mutateAsync(body)}
      />

      <AuditSessionCancelDialog
        open={cancelDialogSession != null}
        onOpenChange={(o) => {
          if (!o) setCancelDialogSession(null)
        }}
        session={cancelDialogSession}
        isSubmitting={cancelMutation.isPending}
        onConfirm={handleConfirmCancel}
      />
    </div>
  )
}
