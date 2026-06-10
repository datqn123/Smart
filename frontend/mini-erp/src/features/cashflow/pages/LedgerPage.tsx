import { useEffect, useMemo, useState } from "react"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { usePageTitle } from "@/context/PageTitleContext"
import { ApiRequestError } from "@/lib/api/http"
import { Button } from "@/components/ui/button"
import { ShieldAlert } from "lucide-react"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import type { LedgerEntry } from "../types"
import { LedgerToolbar } from "../components/LedgerToolbar"
import { LedgerTable } from "../components/LedgerTable"
import { toast } from "sonner"
import { FINANCE_LEDGER_LIST_QUERY_KEY, getFinanceLedgerList } from "../api/financeLedgerApi"

const PAGE_SIZE = 20
const SEARCH_DEBOUNCE_MS = 400

export function LedgerPage() {
  const { setTitle } = usePageTitle()
  const navigate = useNavigate()
  const role = useAuthStore((s) => s.user?.role)
  const isLedgerAdmin = role === "Admin"

  const [search, setSearch] = useState("")
  const debouncedSearch = useDebouncedValue(search.trim(), SEARCH_DEBOUNCE_MS)
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [transactionTypeFilter, setTransactionTypeFilter] = useState("all")
  const [referenceTypeFilter, setReferenceTypeFilter] = useState("all")
  const [page, setPage] = useState(1)

  useEffect(() => {
    setTitle("Sổ cái tài chính")
  }, [setTitle])

  useEffect(() => {
    const id = window.setTimeout(() => setPage(1), 0)
    return () => window.clearTimeout(id)
  }, [debouncedSearch, dateFrom, dateTo, transactionTypeFilter, referenceTypeFilter])

  const filters = useMemo(
    () => ({
      search: debouncedSearch || undefined,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
      transactionType:
        transactionTypeFilter !== "all"
          ? (transactionTypeFilter as "SalesRevenue" | "PurchaseCost" | "OperatingExpense" | "Refund")
          : undefined,
      referenceType: referenceTypeFilter !== "all" ? referenceTypeFilter : undefined,
      page,
      limit: PAGE_SIZE,
    }),
    [debouncedSearch, dateFrom, dateTo, transactionTypeFilter, referenceTypeFilter, page],
  )

  const ledgerQuery = useQuery({
    queryKey: [...FINANCE_LEDGER_LIST_QUERY_KEY, filters],
    queryFn: () => getFinanceLedgerList(filters),
    enabled: isLedgerAdmin,
  })

  useEffect(() => {
    if (!ledgerQuery.isError) return
    const e = ledgerQuery.error
    if (e instanceof ApiRequestError) {
      toast.error(e.body?.message ?? e.message)
    } else {
      toast.error(e instanceof Error ? e.message : "Đã xảy ra lỗi")
    }
  }, [ledgerQuery.isError, ledgerQuery.error])

  const items: LedgerEntry[] = ledgerQuery.data?.items ?? []
  const total = ledgerQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const handleToolbarAction = (action: string) => {
    if (action === "export") {
      toast.info("Đang xuất sổ cái tài chính Excel…")
    }
  }

  const resetFilters = () => {
    setSearch("")
    setDateFrom("")
    setDateTo("")
    setTransactionTypeFilter("all")
    setReferenceTypeFilter("all")
    setPage(1)
  }

  if (!isLedgerAdmin) {
    return (
      <div className="p-4 md:p-6 lg:p-8 flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center">
        <div className="rounded-full bg-amber-50 p-4 border border-amber-100">
          <ShieldAlert className="h-10 w-10 text-amber-700" aria-hidden />
        </div>
        <div className="max-w-md space-y-2">
          <h1 className="text-xl font-semibold text-slate-900">Sổ cái tài chính</h1>
          <p className="text-sm text-slate-600">
            Chỉ tài khoản <span className="font-semibold text-slate-800">Admin</span> được xem sổ cái. Vui lòng dùng
            mục Thu chi hoặc Sổ nợ nếu bạn có quyền xem tài chính.
          </p>
        </div>
        <Button type="button" className="h-11" onClick={() => navigate("/cashflow/transactions")}>
          Đi tới Giao dịch thu chi
        </Button>
      </div>
    )
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      <div className="shrink-0">
        <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Sổ cái tài chính</h1>
        <p className="text-sm text-slate-500 mt-1">
          Dòng tiền ghi sổ: loại nghiệp vụ, nguồn tham chiếu, số tiền có dấu và số dư lũy kế (chỉ Admin).
        </p>
      </div>

      <div className="flex-1 flex flex-col min-h-0 gap-4 md:gap-5">
        <LedgerToolbar
          searchStr={search}
          onSearch={setSearch}
          dateFrom={dateFrom}
          dateTo={dateTo}
          onDateFromChange={setDateFrom}
          onDateToChange={setDateTo}
          transactionTypeFilter={transactionTypeFilter}
          onTransactionTypeFilterChange={setTransactionTypeFilter}
          referenceTypeFilter={referenceTypeFilter}
          onReferenceTypeFilterChange={setReferenceTypeFilter}
          onResetFilters={resetFilters}
          onAction={handleToolbarAction}
        />

        <div className="flex-1 flex flex-col min-h-0 bg-white border border-slate-200/60 rounded-xl overflow-hidden shadow-md">
          <div className="flex-1 overflow-auto relative scroll-smooth [scrollbar-gutter:stable] min-h-0">
            <LedgerTable data={items} />
          </div>
          {total > PAGE_SIZE ? (
            <div className="flex items-center justify-between gap-2 border-t border-slate-100 px-4 py-2 text-xs font-bold text-slate-600">
              <span>
                Trang {page} / {totalPages} — {ledgerQuery.isFetching ? "…" : total} bản ghi
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-8 px-3"
                  disabled={page <= 1 || ledgerQuery.isFetching}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Trước
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-8 px-3"
                  disabled={page >= totalPages || ledgerQuery.isFetching}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Sau
                </Button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
