import { useEffect, useMemo, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import type { Transaction } from "../types"
import { TransactionToolbar } from "../components/TransactionToolbar"
import { TransactionTable } from "../components/TransactionTable"
import { TransactionDetailDialog } from "../components/TransactionDetailDialog"
import { TransactionFormDialog } from "../components/TransactionFormDialog"
import { toast } from "sonner"
import { TrendingUp, TrendingDown, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DATA_TABLE_SCROLL_CLASS, DATA_TABLE_SHELL_CLASS } from "@/lib/data-table-layout"
import { toastApiError } from "@/lib/api/toastApiError"
import {
  CASH_TRANSACTIONS_LIST_QUERY_KEY,
  CASH_TRANSACTION_DETAIL_QUERY_KEY,
  getCashTransactionsList,
  postCashTransaction,
  patchCashTransaction,
  deleteCashTransaction,
  type CashTransactionCreateBody,
} from "../api/cashTransactionsApi"
import { FINANCE_LEDGER_LIST_QUERY_KEY } from "../api/financeLedgerApi"
import { CASH_FUNDS_LIST_QUERY_KEY, getCashFundsList } from "../api/cashFundsApi"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

function mapFormToCreateBody(data: Record<string, unknown>): CashTransactionCreateBody {
  const direction: "Income" | "Expense" = data.direction === "Expense" ? "Expense" : "Income"
  const amount =
    typeof data.amount === "number" && !Number.isNaN(data.amount) ? data.amount : Number(data.amount)
  const category = String(data.category ?? "").trim()
  const transactionDate = String(data.transactionDate ?? "").trim()
  const paymentMethod = (String(data.paymentMethod ?? "Cash").trim() || "Cash").slice(0, 30)
  const descRaw = data.description != null ? String(data.description).trim() : ""
  const description = descRaw.length > 0 ? descRaw : undefined
  const fundIdRaw = data.fundId
  const fundId =
    typeof fundIdRaw === "number" && !Number.isNaN(fundIdRaw) ? Math.trunc(fundIdRaw) : Math.trunc(Number(fundIdRaw))
  return { direction, amount, category, transactionDate, paymentMethod, description, fundId }
}

/** Task067 — body theo trạng thái server (Cancelled chỉ `description`; Completed chỉ idempotent `status`). */
function buildCashTransactionPatchBody(form: Record<string, unknown>, server: Transaction): Record<string, unknown> {
  const st = server.status
  if (st === "Cancelled") {
    const desc = form.description != null ? String(form.description).trim() : ""
    const prev = (server.description ?? "").trim()
    if (desc === prev) return {}
    return { description: desc.length > 0 ? desc : null }
  }
  if (st === "Completed") {
    return { status: "Completed" }
  }
  const amount =
    typeof form.amount === "number" && !Number.isNaN(form.amount) ? form.amount : Number(form.amount)
  const category = String(form.category ?? "").trim()
  const transactionDate = String(form.transactionDate ?? "").trim()
  const paymentMethod = (String(form.paymentMethod ?? "Cash").trim() || "Cash").slice(0, 30)
  const descRaw = form.description != null ? String(form.description).trim() : ""
  const description = descRaw.length > 0 ? descRaw : null
  const statusRaw = String(form.status ?? "Pending").trim()
  const status: "Pending" | "Completed" | "Cancelled" =
    statusRaw === "Completed" || statusRaw === "Cancelled" || statusRaw === "Pending" ? statusRaw : "Pending"
  return { amount, category, description, paymentMethod, transactionDate, status }
}

export function TransactionsPage() {
  const { setTitle } = usePageTitle()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [typeFilter, setTypeFilter] = useState("all")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [page, setPage] = useState(1)

  const [selectedItem, setSelectedItem] = useState<Transaction | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [formMode, setFormMode] = useState<"create" | "edit">("create")

  useEffect(() => {
    setTitle("Giao dịch thu chi")
  }, [setTitle])

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(search.trim()), SEARCH_DEBOUNCE_MS)
    return () => window.clearTimeout(t)
  }, [search])

  useEffect(() => {
    const t = window.setTimeout(() => setPage(1), 0)
    return () => window.clearTimeout(t)
  }, [debouncedSearch, statusFilter, typeFilter, dateFrom, dateTo])

  const filters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      type:
        typeFilter === "all" ? undefined : (typeFilter as "Income" | "Expense"),
      status:
        statusFilter === "all"
          ? undefined
          : (statusFilter as "Pending" | "Completed" | "Cancelled"),
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
      page,
      limit: PAGE_SIZE,
    }),
    [debouncedSearch, typeFilter, statusFilter, dateFrom, dateTo, page],
  )

  const txQuery = useQuery({
    queryKey: [...CASH_TRANSACTIONS_LIST_QUERY_KEY, filters],
    queryFn: () => getCashTransactionsList(filters),
  })

  const fundsQuery = useQuery({
    queryKey: CASH_FUNDS_LIST_QUERY_KEY,
    queryFn: () => getCashFundsList(),
  })

  const defaultFundId = useMemo(() => {
    const items = fundsQuery.data?.items ?? []
    const d = items.find((f) => f.isDefault)
    return d?.id ?? items[0]?.id ?? null
  }, [fundsQuery.data?.items])

  useEffect(() => {
    if (!txQuery.isError) return
    toastApiError(txQuery.error)
  }, [txQuery.isError, txQuery.error])

  const transactions: Transaction[] = txQuery.data?.items ?? []
  const total = txQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const totalIncome = transactions.filter((t) => t.direction === "Income").reduce((sum, t) => sum + t.amount, 0)
  const totalExpense = transactions.filter((t) => t.direction === "Expense").reduce((sum, t) => sum + t.amount, 0)
  const balance = totalIncome - totalExpense

  const handleSelect = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]))
  }

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? transactions.map((t) => t.id) : [])
  }

  const handleToolbarAction = (action: string) => {
    switch (action) {
      case "create":
        setSelectedItem(null)
        setFormMode("create")
        setIsFormOpen(true)
        break
      case "edit":
        if (selectedIds.length === 1) {
          const item = transactions.find((t) => t.id === selectedIds[0])
          if (item) {
            setSelectedItem(item)
            setFormMode("edit")
            setIsFormOpen(true)
          }
        } else {
          toast.error("Vui lòng chọn duy nhất 1 giao dịch để chỉnh sửa")
        }
        break
      case "delete":
        requestDeleteByIds(selectedIds)
        break
    }
  }

  const handleView = (item: Transaction) => {
    setSelectedItem(item)
    setIsDetailOpen(true)
  }

  const handleEdit = (item: Transaction) => {
    setSelectedItem(item)
    setFormMode("edit")
    setIsFormOpen(true)
  }

  const requestDeleteByIds = (ids: number[]) => {
    if (ids.length === 0) {
      toast.error("Chưa chọn giao dịch")
      return
    }
    toast.warning(
      ids.length === 1
        ? "Xóa giao dịch này? Chỉ phiếu chờ xử lý hoặc đã huỷ và chưa ghi sổ mới xóa được."
        : `Xóa ${ids.length} giao dịch đã chọn?`,
      {
        action: {
          label: "Xóa",
          onClick: () => void deleteByIds(ids),
        },
      },
    )
  }

  const deleteByIds = async (ids: number[]) => {
    const successfulIds: number[] = []
    let failedCount = 0
    for (const id of ids) {
      try {
        await deleteCashTransaction(id)
        successfulIds.push(id)
        queryClient.removeQueries({ queryKey: [...CASH_TRANSACTION_DETAIL_QUERY_KEY, id] })
      } catch (e) {
        failedCount += 1
        toastApiError(e, "Không xóa được giao dịch")
      }
    }

    if (successfulIds.length > 0) {
      await queryClient.invalidateQueries({ queryKey: [...CASH_TRANSACTIONS_LIST_QUERY_KEY] })
      const message =
        failedCount > 0
          ? `Đã xóa ${successfulIds.length} giao dịch, thất bại ${failedCount}`
          : successfulIds.length === 1
            ? "Đã xóa giao dịch"
            : `Đã xóa ${successfulIds.length} giao dịch`
      toast.success(message)
      const removed = new Set(successfulIds)
      setSelectedIds((prev) => prev.filter((id) => !removed.has(id)))
      if (selectedItem && removed.has(selectedItem.id)) {
        setSelectedItem(null)
        setIsDetailOpen(false)
        setIsFormOpen(false)
      }
    }
  }

  const handleFormSubmit = async (
    data: Record<string, unknown>,
    ctx?: { source?: Transaction | null },
  ) => {
    if (formMode === "create") {
      const category = String(data.category ?? "").trim()
      const amount =
        typeof data.amount === "number" && !Number.isNaN(data.amount) ? data.amount : Number(data.amount)
      if (!category) {
        toast.error("Vui lòng nhập nhóm phân loại")
        return
      }
      if (category.length > 500) {
        toast.error("Nhóm phân loại tối đa 500 ký tự")
        return
      }
      if (!Number.isFinite(amount) || amount <= 0) {
        toast.error("Số tiền phải lớn hơn 0")
        return
      }
      const body = mapFormToCreateBody(data)
      if (!Number.isFinite(body.fundId) || body.fundId <= 0) {
        toast.error("Vui lòng chọn quỹ cho giao dịch")
        return
      }
      const desc = data.description != null ? String(data.description).trim() : ""
      if (desc.length > 2000) {
        toast.error("Nội dung diễn giải tối đa 2000 ký tự")
        return
      }
      try {
        await postCashTransaction(body)
        toast.success("Đã tạo giao dịch")
        await queryClient.invalidateQueries({ queryKey: [...CASH_TRANSACTIONS_LIST_QUERY_KEY] })
        setIsFormOpen(false)
      } catch (e) {
        toastApiError(e, "Không tạo được giao dịch")
      }
      return
    }

    const source = ctx?.source ?? selectedItem
    if (!source?.id) {
      toast.error("Thiếu thông tin giao dịch")
      return
    }

    if (source.status === "Pending") {
      const category = String(data.category ?? "").trim()
      const amount =
        typeof data.amount === "number" && !Number.isNaN(data.amount) ? data.amount : Number(data.amount)
      if (!category) {
        toast.error("Vui lòng nhập nhóm phân loại")
        return
      }
      if (category.length > 500) {
        toast.error("Nhóm phân loại tối đa 500 ký tự")
        return
      }
      if (!Number.isFinite(amount) || amount <= 0) {
        toast.error("Số tiền phải lớn hơn 0")
        return
      }
      const desc = data.description != null ? String(data.description).trim() : ""
      if (desc.length > 2000) {
        toast.error("Nội dung diễn giải tối đa 2000 ký tự")
        return
      }
    }

    if (source.status === "Cancelled") {
      const desc = data.description != null ? String(data.description).trim() : ""
      if (desc.length > 2000) {
        toast.error("Nội dung diễn giải tối đa 2000 ký tự")
        return
      }
    }

    const patchBody = buildCashTransactionPatchBody(data, source)
    if (Object.keys(patchBody).length === 0) {
      toast.info("Không có thay đổi để lưu")
      return
    }

    try {
      const updated = await patchCashTransaction(source.id, patchBody)
      toast.success("Đã cập nhật giao dịch")
      await queryClient.invalidateQueries({ queryKey: [...CASH_TRANSACTIONS_LIST_QUERY_KEY] })
      await queryClient.invalidateQueries({ queryKey: [...CASH_TRANSACTION_DETAIL_QUERY_KEY, source.id] })
      if (updated.status === "Completed") {
        await queryClient.invalidateQueries({ queryKey: [...FINANCE_LEDGER_LIST_QUERY_KEY] })
      }
      setSelectedItem(updated)
      setIsFormOpen(false)
    } catch (e) {
      toastApiError(e, "Không cập nhật được giao dịch")
    }
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-6">
        <div>
          <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Giao dịch thu chi</h1>
          <p className="text-sm text-slate-500 mt-1 font-medium">Quản lý thu chi và luân chuyển tiền mặt</p>
        </div>

        <div className="flex flex-col gap-1">
        <div className="flex flex-wrap items-center gap-4">
            <StatCard label="Thu (trang này)" amount={totalIncome} icon={TrendingUp} />
            <StatCard label="Chi (trang này)" amount={totalExpense} icon={TrendingDown} />
            <StatCard label="Chênh lệch (trang này)" amount={balance} icon={DollarSign} />
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 gap-4 md:gap-5">
        <TransactionToolbar
          searchStr={search}
          onSearch={setSearch}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          typeFilter={typeFilter}
          onTypeChange={setTypeFilter}
          dateFrom={dateFrom}
          dateTo={dateTo}
          onDateFromChange={setDateFrom}
          onDateToChange={setDateTo}
          selectedIds={selectedIds}
          onAction={handleToolbarAction}
        />

        <div className={DATA_TABLE_SHELL_CLASS}>
          <div className={DATA_TABLE_SCROLL_CLASS}>
            {txQuery.isFetching ? (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60 text-sm font-medium text-slate-500">
                Đang tải…
              </div>
            ) : null}
            <TransactionTable
              data={transactions}
              selectedIds={selectedIds}
              onSelect={handleSelect}
              onSelectAll={handleSelectAll}
              onView={handleView}
              onEdit={handleEdit}
              onDelete={(item) => requestDeleteByIds([item.id])}
            />
          </div>
          {total > PAGE_SIZE ? (
            <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
              <span>
                Trang {page} / {totalPages} — {txQuery.isFetching ? "…" : total} bản ghi
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-8 px-3"
                  disabled={page <= 1 || txQuery.isFetching}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Trước
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-8 px-3"
                  disabled={page >= totalPages || txQuery.isFetching}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Sau
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <TransactionDetailDialog
        transactionId={isDetailOpen && selectedItem ? selectedItem.id : null}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />

      <TransactionFormDialog
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        initialData={selectedItem}
        mode={formMode}
        detailSourceId={formMode === "edit" && isFormOpen && selectedItem ? selectedItem.id : null}
        fundOptions={fundsQuery.data?.items ?? []}
        defaultFundId={defaultFundId}
        fundsLoading={fundsQuery.isLoading}
      />
    </div>
  )
}

function StatCard({
  label,
  amount,
  icon: Icon,
}: {
  label: string
  amount: number
  icon: typeof TrendingUp
}) {
  return (
    <div className="px-5 py-3 rounded-xl border border-slate-200 flex items-center gap-4 bg-white min-w-50">
      <div className="h-10 w-10 rounded-lg flex items-center justify-center bg-slate-100 text-slate-600">
        <Icon size={18} strokeWidth={2} />
      </div>
      <div>
        <p className="text-[10px] font-semibold uppercase text-slate-500 tracking-wide">{label}</p>
        <p className="text-base font-semibold tabular-nums tracking-tight text-slate-900">
          {amount.toLocaleString()} <span className="text-[10px] font-normal text-slate-500">đ</span>
        </p>
      </div>
    </div>
  )
}
