import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Download, Calendar, RotateCcw, Layers } from "lucide-react"
import {
  LEDGER_REFERENCE_TYPE_FILTER_OPTIONS,
  LEDGER_TRANSACTION_TYPE_FILTER_OPTIONS,
} from "../lib/ledgerDisplayLabels"

interface LedgerToolbarProps {
  searchStr: string
  onSearch: (val: string) => void
  dateFrom: string
  dateTo: string
  onDateFromChange: (val: string) => void
  onDateToChange: (val: string) => void
  transactionTypeFilter: string
  onTransactionTypeFilterChange: (val: string) => void
  referenceTypeFilter: string
  onReferenceTypeFilterChange: (val: string) => void
  onResetFilters: () => void
  onAction: (action: string) => void
}

export function LedgerToolbar({
  searchStr,
  onSearch,
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  transactionTypeFilter,
  onTransactionTypeFilterChange,
  referenceTypeFilter,
  onReferenceTypeFilterChange,
  onResetFilters,
  onAction,
}: LedgerToolbarProps) {
  return (
    <div className="flex flex-col gap-4 bg-white p-4 border border-slate-200 rounded-lg shrink-0 shadow-sm mb-4">
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        <div className="relative flex-1 w-full max-w-md group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
          <Input
            placeholder="Tìm theo diễn giải hoặc mã hiển thị (FL-…, mã đơn, mã phiếu trong mô tả)…"
            className="pl-10 h-11 bg-slate-50/50 border-slate-200 focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-50 transition-all rounded-lg"
            value={searchStr}
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => onDateFromChange(e.target.value)}
              className="h-11 bg-slate-50/50 border-slate-200 focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-50 transition-all rounded-lg w-40"
            />
            <span className="text-xs font-bold text-slate-400">—</span>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => onDateToChange(e.target.value)}
              className="h-11 bg-slate-50/50 border-slate-200 focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-50 transition-all rounded-lg w-40"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            className="h-11 bg-white border-slate-200 rounded-lg text-slate-600"
            onClick={onResetFilters}
            title="Làm mới bộ lọc"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            className="h-11 px-4 text-slate-600 border-slate-200 hover:bg-slate-50 rounded-lg ml-auto lg:ml-0"
            onClick={() => onAction("export")}
          >
            <Download className="h-4 w-4 mr-2" />
            Xuất sổ cái
          </Button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2 border-t border-slate-100 pt-4">
        <Layers className="h-4 w-4 text-slate-400 shrink-0 hidden sm:block" aria-hidden />
        <Select value={transactionTypeFilter} onValueChange={onTransactionTypeFilterChange}>
          <SelectTrigger className="h-11 w-full sm:w-[200px] border-slate-200 rounded-lg bg-slate-50/50">
            <SelectValue placeholder="Loại nghiệp vụ" />
          </SelectTrigger>
          <SelectContent position="popper" className="bg-white border-slate-200 rounded-xl shadow-xl max-h-72">
            {LEDGER_TRANSACTION_TYPE_FILTER_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={referenceTypeFilter} onValueChange={onReferenceTypeFilterChange}>
          <SelectTrigger className="h-11 w-full sm:w-[200px] border-slate-200 rounded-lg bg-slate-50/50">
            <SelectValue placeholder="Nguồn ghi sổ" />
          </SelectTrigger>
          <SelectContent position="popper" className="bg-white border-slate-200 rounded-xl shadow-xl max-h-72">
            {LEDGER_REFERENCE_TYPE_FILTER_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
