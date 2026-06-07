import { useEffect, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { usePageTitle } from "@/context/PageTitleContext"
import type { Debt } from "../types"
import { DebtToolbar } from "../components/DebtToolbar"
import { DebtTable } from "../components/DebtTable"
import { DebtDetailDialog } from "../components/DebtDetailDialog"
import { DebtFormDialog } from "../components/DebtFormDialog"
import { toast } from "sonner"
import { Users, Truck, AlertCircle, type LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { DATA_TABLE_SCROLL_CLASS, DATA_TABLE_SHELL_CLASS } from "@/lib/data-table-layout"
import { toastApiError } from "@/lib/api/toastApiError"
import { DEBTS_LIST_QUERY_KEY, patchDebt, postDebt, type DebtCreateBody } from "../api/debtsApi"
import { useDebtsListQuery } from "../hooks/useDebtsListQuery"

function readPositiveNumber(value: unknown) {
  const n = typeof value === "number" ? value : Number(value)
  return Number.isFinite(n) && n > 0 ? n : null
}

function mapFormToCreateBody(data: Record<string, unknown>): DebtCreateBody {
  const partnerType = data.partnerType === "Supplier" ? "Supplier" : "Customer"
  const totalAmount = Number(data.totalAmount)
  const paidAmount = Number(data.paidAmount ?? 0)
  const dueDate = data.dueDate ? String(data.dueDate) : null
  const notesRaw = data.notes != null ? String(data.notes).trim() : ""
  const customerId = partnerType === "Customer" ? readPositiveNumber(data.customerId) : null
  const supplierId = partnerType === "Supplier" ? readPositiveNumber(data.supplierId) : null
  return {
    partnerType,
    customerId,
    supplierId,
    totalAmount,
    paidAmount,
    dueDate,
    notes: notesRaw.length > 0 ? notesRaw : null,
  }
}

function mapFormToPatchBody(data: Record<string, unknown>, source: Debt | null): Record<string, unknown> {
  const dueDate = data.dueDate ? String(data.dueDate) : null
  const notesRaw = data.notes != null ? String(data.notes).trim() : ""
  const body: Record<string, unknown> = {
    dueDate,
    notes: notesRaw.length > 0 ? notesRaw : null,
  }
  if (source?.status !== "Cleared") {
    body.totalAmount = Number(data.totalAmount)
    body.paidAmount = Number(data.paidAmount ?? 0)
  }
  return body
}

export function DebtPage() {
  const { setTitle } = usePageTitle()
  const queryClient = useQueryClient()
  
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const debtsQuery = useDebtsListQuery()
  
  // Modals state
  const [selectedItem, setSelectedItem] = useState<Debt | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')

  useEffect(() => { setTitle("Sổ nợ") }, [setTitle])

  useEffect(() => {
    if (!debtsQuery.isError) return
    toastApiError(debtsQuery.error, "Không tải được sổ nợ")
  }, [debtsQuery.isError, debtsQuery.error])

  useEffect(() => {
    const t = window.setTimeout(() => {
      const visibleIds = new Set(debtsQuery.debts.map((d) => d.id))
      setSelectedIds((prev) => prev.filter((id) => visibleIds.has(id)))
    }, 0)
    return () => window.clearTimeout(t)
  }, [debtsQuery.debts])

  // Summary stats
  const totalReceivable = debtsQuery.debts.filter(d => d.partnerType === 'Customer').reduce((sum, d) => sum + d.remainingAmount, 0)
  const totalPayable = debtsQuery.debts.filter(d => d.partnerType === 'Supplier').reduce((sum, d) => sum + d.remainingAmount, 0)
  const overdueCount = debtsQuery.debts.filter(d => {
    if (!d.dueDate || d.status === "Cleared") return false
    const today = new Date(); today.setHours(0, 0, 0, 0)
    const due = new Date(d.dueDate); due.setHours(0, 0, 0, 0)
    return due < today
  }).length

  // Handlers
  const handleSelect = (id: number) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id])
  }

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? debtsQuery.debts.map(d => d.id) : [])
  }

  const handleToolbarAction = (action: string) => {
    switch (action) {
      case "create":
        setSelectedItem(null)
        setFormMode('create')
        setIsFormOpen(true)
        break;
      case "repay":
        if (selectedIds.length === 1) {
            const item = debtsQuery.debts.find(d => d.id === selectedIds[0])
            if (item) {
                setSelectedItem(item)
                setFormMode('edit')
                setIsFormOpen(true)
            }
        } else {
            toast.error("Vui lòng chọn duy nhất 1 khoản nợ để cập nhật thanh toán")
        }
        break;
    }
  }

  const handleView = (item: Debt) => {
    setSelectedItem(item)
    setIsDetailOpen(true)
  }

  const handleEdit = (item: Debt) => {
    setSelectedItem(item)
    setFormMode('edit')
    setIsFormOpen(true)
  }

  const handleFormSubmit = async (data: Record<string, unknown>) => {
    const paid = Number(data.paidAmount)
    const total = Number(data.totalAmount)
    if (!Number.isFinite(total) || total < 0) {
      toast.error("Tổng nợ không hợp lệ")
      return
    }
    if (!Number.isFinite(paid) || paid < 0 || paid > total) {
      toast.error("Đã thanh toán phải từ 0 đến tổng nợ")
      return
    }
    if (formMode === 'create') {
      const body = mapFormToCreateBody(data)
      if (body.partnerType === "Customer" && !body.customerId) {
        toast.error("Vui lòng nhập ID khách hàng")
        return
      }
      if (body.partnerType === "Supplier" && !body.supplierId) {
        toast.error("Vui lòng nhập ID nhà cung cấp")
        return
      }
      try {
        await postDebt(body)
        toast.success("Đã tạo khoản nợ")
        await queryClient.invalidateQueries({ queryKey: [...DEBTS_LIST_QUERY_KEY] })
        setIsFormOpen(false)
      } catch (e) {
        toastApiError(e, "Không tạo được khoản nợ")
      }
      return
    }
    if (!selectedItem?.id) {
      toast.error("Thiếu thông tin khoản nợ")
      return
    }
    try {
      const updated = await patchDebt(selectedItem.id, mapFormToPatchBody(data, selectedItem))
      toast.success("Đã cập nhật khoản nợ")
      await queryClient.invalidateQueries({ queryKey: [...DEBTS_LIST_QUERY_KEY] })
      setSelectedItem(updated)
      setIsFormOpen(false)
    } catch (e) {
      toastApiError(e, "Không cập nhật được khoản nợ")
    }
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 flex flex-col h-full min-h-0 gap-4 md:gap-5 overflow-hidden">
      {/* Header & Stats Cards */}
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-6 shrink-0">
        <div>
          <h1 className="text-xl md:text-2xl font-semibold text-slate-900 tracking-tight">Sổ nợ đối tác</h1>
          <p className="text-sm text-slate-500 mt-1 font-medium">Theo dõi công nợ khách hàng và nhà cung cấp</p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
            <StatCard 
                label="Phải thu (trang này)" 
                amount={totalReceivable} 
                icon={Users} 
                color="blue" 
            />
            <StatCard 
                label="Phải trả (trang này)" 
                amount={totalPayable} 
                icon={Truck} 
                color="indigo" 
            />
            <StatCard 
                label="Quá hạn (trang này)" 
                amount={overdueCount} 
                icon={AlertCircle} 
                color="rose"
                isCount 
            />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-h-0 gap-4 md:gap-5">
        <DebtToolbar 
          searchStr={debtsQuery.search}
          onSearch={debtsQuery.setSearch}
          statusFilter={debtsQuery.statusFilter}
          onStatusChange={debtsQuery.setStatusFilter}
          typeFilter={debtsQuery.partnerTypeFilter}
          onTypeChange={debtsQuery.setPartnerTypeFilter}
          dueDateFrom={debtsQuery.dueDateFrom}
          dueDateTo={debtsQuery.dueDateTo}
          onDueDateFromChange={debtsQuery.setDueDateFrom}
          onDueDateToChange={debtsQuery.setDueDateTo}
          selectedIds={selectedIds}
          onAction={handleToolbarAction}
        />
        
        <div className={DATA_TABLE_SHELL_CLASS}>
          <div className={DATA_TABLE_SCROLL_CLASS}>
            {debtsQuery.isFetching ? (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60 text-sm font-medium text-slate-500">
                Đang tải…
              </div>
            ) : null}
            <DebtTable 
              data={debtsQuery.debts}
              selectedIds={selectedIds}
              onSelect={handleSelect}
              onSelectAll={handleSelectAll}
              onView={handleView}
              onEdit={handleEdit}
            />
          </div>
          <div className="flex items-center justify-between flex-wrap gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50/80 text-sm text-slate-600 min-h-11 shrink-0">
            <span>
              Đang hiển thị {debtsQuery.debts.length} / {debtsQuery.isFetching ? "…" : debtsQuery.total} khoản nợ
            </span>
            <div className="flex items-center gap-2">
              <span>Trang {debtsQuery.page} / {debtsQuery.totalPages}</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 px-3"
                disabled={debtsQuery.page <= 1 || debtsQuery.isFetching}
                onClick={() => debtsQuery.setPage((p) => Math.max(1, p - 1))}
              >
                Trước
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 px-3"
                disabled={debtsQuery.page >= debtsQuery.totalPages || debtsQuery.isFetching}
                onClick={() => debtsQuery.setPage((p) => p + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <DebtDetailDialog 
        debt={selectedItem}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />

      <DebtFormDialog 
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        initialData={selectedItem}
        mode={formMode}
      />
    </div>
  )
}

function StatCard({ label, amount, icon: Icon, color, isCount = false }: { label: string, amount: number, icon: LucideIcon, color: 'blue' | 'indigo' | 'rose', isCount?: boolean }) {
    const colorMap = {
        blue: "text-slate-700 bg-slate-50 border-slate-100",
        indigo: "text-slate-700 bg-slate-50 border-slate-100",
        rose: "text-rose-600 bg-slate-50 border-slate-100"
    }
    
    return (
        <div className="px-5 py-3 rounded-xl border border-slate-200 flex items-center gap-4 bg-white min-w-50">
            <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center", colorMap[color].split(' ')[1])}>
                <Icon size={18} className={colorMap[color].split(' ')[0]} />
            </div>
            <div>
                <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest">{label}</p>
                <p className={cn("text-base font-black tracking-tight", colorMap[color].split(' ')[0])}>
                    {amount.toLocaleString()} <span className="text-[10px] font-normal text-slate-400">{isCount ? 'khoản' : 'đ'}</span>
                </p>
            </div>
        </div>
    )
}
