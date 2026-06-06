import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { useQuery } from "@tanstack/react-query"
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import { 
  Wallet, 
  Calendar, 
  Tag, 
  FileText, 
  CreditCard,
  PlusCircle,
  Save,
  ArrowUpCircle,
  ArrowDownCircle,
  Activity,
  Landmark,
} from "lucide-react"
import type { Transaction } from "../types"
import { cn } from "@/lib/utils"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import {
  CASH_TRANSACTION_DETAIL_QUERY_KEY,
  getCashTransactionById,
} from "../api/cashTransactionsApi"
import {
  FORM_LABEL_CLASS,
  FORM_INPUT_CLASS,
} from "@/lib/data-table-layout"
import type { CashFundItem } from "../api/cashFundsApi"

function mapTransactionToFormValues(t: Transaction) {
  const amt = typeof t.amount === "number" && !Number.isNaN(t.amount) ? t.amount : Number(t.amount)
  return {
    transactionCode: t.transactionCode,
    direction: t.direction,
    category: t.category,
    amount: Number.isFinite(amt) ? amt : 0,
    transactionDate: t.transactionDate,
    paymentMethod: t.paymentMethod ?? "Cash",
    status: t.status,
    description: t.description ?? "",
    fundId: t.fundId != null && t.fundId > 0 ? t.fundId : undefined,
  }
}

interface TransactionFormDialogProps {
  isOpen: boolean
  onClose: () => void
  /** Task065/067 — `ctx.source` = bản ghi server để build PATCH đúng BR. */
  onSubmit: (
    data: Record<string, unknown>,
    ctx?: { source?: Transaction | null },
  ) => void | Promise<void>
  initialData?: Transaction | null
  mode: "create" | "edit"
  /** Task066 — GET by id khi sửa (đủ read-model). */
  detailSourceId?: number | null
  fundOptions?: CashFundItem[]
  defaultFundId?: number | null
  fundsLoading?: boolean
}

export function TransactionFormDialog({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  mode,
  detailSourceId = null,
  fundOptions = [],
  defaultFundId = null,
  fundsLoading = false,
}: TransactionFormDialogProps) {
  const { register, handleSubmit, reset, setValue, watch } = useForm<Record<string, unknown>>({
    defaultValues: initialData || {
      direction: 'Income',
      category: '',
      amount: 0,
      transactionDate: new Date().toISOString().split('T')[0],
      paymentMethod: 'Cash',
      status: "Pending",
      description: '',
      fundId: defaultFundId ?? undefined,
    }
  })

  const detailQuery = useQuery({
    queryKey: [...CASH_TRANSACTION_DETAIL_QUERY_KEY, detailSourceId],
    queryFn: () => getCashTransactionById(detailSourceId!),
    enabled: isOpen && mode === "edit" && detailSourceId != null && detailSourceId > 0,
  })

  useEffect(() => {
    if (!detailQuery.isError) return
    if (mode !== "edit") return
    const e = detailQuery.error
    if (e instanceof ApiRequestError) {
      toast.error(e.body?.message ?? e.message)
    } else {
      toast.error(e instanceof Error ? e.message : "Không tải được chi tiết phiếu")
    }
  }, [detailQuery.isError, detailQuery.error, mode])

  useEffect(() => {
    if (!isOpen) return
    if (mode === "create") {
      reset({
        direction: "Income",
        category: "",
        amount: 0,
        transactionDate: new Date().toISOString().split("T")[0],
        paymentMethod: "Cash",
        status: "Pending",
        description: "",
        fundId: defaultFundId ?? undefined,
      })
      return
    }
    if (detailQuery.data) {
      reset(mapTransactionToFormValues(detailQuery.data))
      return
    }
    if (initialData) {
      reset(mapTransactionToFormValues(initialData))
    }
  }, [isOpen, mode, initialData, detailQuery.data, reset, defaultFundId])

  const directionValue = watch("direction")
  const fundIdWatch = watch("fundId") as number | string | undefined
  const fundSelectValue =
    fundIdWatch != null && fundIdWatch !== ""
      ? String(fundIdWatch)
      : defaultFundId != null
        ? String(defaultFundId)
        : fundOptions[0]?.id != null
          ? String(fundOptions[0].id)
          : ""
  const editLoadingFresh = mode === "edit" && detailSourceId != null && detailQuery.isFetching && !detailQuery.data

  const serverRow = mode === "edit" ? (detailQuery.data ?? initialData ?? null) : null
  const rowStatus = serverRow?.status
  const lockDirection = mode === "edit"
  const lockMoneyFields = mode === "edit" && (rowStatus === "Completed" || rowStatus === "Cancelled")
  const lockStatusSelect = mode === "edit" && (rowStatus === "Completed" || rowStatus === "Cancelled")
  const lockDescription = mode === "edit" && rowStatus === "Completed"

  const onFormSubmit = async (data: Record<string, unknown>) => {
    await onSubmit(data, { source: serverRow })
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl p-0 gap-0 border-slate-200 shadow-xl rounded-2xl overflow-hidden text-slate-900 relative">
        {editLoadingFresh ? (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/70 text-sm font-medium text-slate-600">
            Đang tải chi tiết phiếu…
          </div>
        ) : null}
        <DialogHeader className="p-8 pb-6 bg-slate-50/50 border-b border-slate-100">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-xl flex items-center justify-center bg-slate-800 text-white">
              {directionValue === 'Income' ? <ArrowUpCircle size={24} /> : <ArrowDownCircle size={24} />}
            </div>
            <div>
              <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-0.5">Tài chính & Thu chi</p>
              <DialogTitle className="text-2xl font-black text-slate-900 tracking-tight">
                {mode === 'create' ? "LẬP PHIẾU THU CHI" : "CẬP NHẬT GIAO DỊCH"}
              </DialogTitle>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit(onFormSubmit)} className="p-8 pt-6 space-y-8">
          <div className="grid grid-cols-2 gap-x-10 gap-y-7">
            {/* Row 1 */}
            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>
                <Tag size={12} className="inline mr-1" /> Loại giao dịch
              </Label>
              <Select
                value={watch("direction") ?? "Income"}
                onValueChange={(val) => setValue("direction", val as "Income" | "Expense")}
                disabled={lockDirection}
              >
                <SelectTrigger
                  disabled={lockDirection}
                  className={cn(FORM_INPUT_CLASS, "h-14 font-bold")}
                >
                  <SelectValue placeholder="Chọn loại..." />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-slate-200 shadow-xl">
                  <SelectItem value="Income" className="text-slate-800 font-medium">Thu tiền (+)</SelectItem>
                  <SelectItem value="Expense" className="text-slate-800 font-medium">Chi tiền (-)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>
                <FileText size={12} className="inline mr-1" /> Nhóm phân loại
              </Label>
              <Input
                {...register("category")}
                placeholder="VD: Bán hàng, Nhập hàng, Lương..."
                disabled={lockMoneyFields}
                className={cn(FORM_INPUT_CLASS, "h-14 font-bold")}
              />
            </div>

            {/* Row 2 */}
            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>
                <Wallet size={12} className="inline mr-1" /> Số tiền (VNĐ)
              </Label>
              <Input
                type="number"
                {...register("amount", { valueAsNumber: true })}
                disabled={lockMoneyFields}
                className={cn(FORM_INPUT_CLASS, "h-14 font-black text-lg")}
              />
            </div>

            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>
                <Calendar size={12} className="inline mr-1" /> Ngày giao dịch
              </Label>
              <Input
                type="date"
                {...register("transactionDate")}
                disabled={lockMoneyFields}
                className={cn(FORM_INPUT_CLASS, "h-14 font-bold")}
              />
            </div>

            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>
                <Landmark size={12} className="inline mr-1" /> Quỹ tiền
              </Label>
              {mode === "edit" && lockMoneyFields ? (
                <p className={cn(FORM_INPUT_CLASS, "h-14 flex items-center text-sm font-bold text-slate-800")}>
                  {serverRow?.fundCode ?? serverRow?.fundId ?? "—"}
                </p>
              ) : (
                <Select
                  value={fundSelectValue}
                  onValueChange={(val) => setValue("fundId", Number(val), { shouldValidate: true })}
                  disabled={lockMoneyFields || fundsLoading || fundOptions.length === 0}
                >
                  <SelectTrigger
                    disabled={lockMoneyFields || fundsLoading || fundOptions.length === 0}
                    className={cn(FORM_INPUT_CLASS, "h-14 font-bold")}
                  >
                    <SelectValue placeholder={fundsLoading ? "Đang tải quỹ…" : "Chọn quỹ…"} />
                  </SelectTrigger>
                  <SelectContent className="rounded-xl border-slate-200 shadow-xl">
                    {fundOptions.map((f) => (
                      <SelectItem key={f.id} value={String(f.id)}>
                        {f.name} ({f.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Row 3 */}
            <div className="space-y-2">
              <Label className={FORM_LABEL_CLASS}>
                <CreditCard size={12} className="inline mr-1" /> Phương thức
              </Label>
              <Select
                value={watch("paymentMethod") ?? "Cash"}
                onValueChange={(val) => setValue("paymentMethod", val)}
                disabled={lockMoneyFields}
              >
                <SelectTrigger
                  disabled={lockMoneyFields}
                  className={cn(FORM_INPUT_CLASS, "h-14 font-bold")}
                >
                  <SelectValue placeholder="Chọn phương thức..." />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-slate-200 shadow-xl">
                  <SelectItem value="Cash">Tiền mặt</SelectItem>
                  <SelectItem value="BankTransfer">Chuyển khoản</SelectItem>
                  <SelectItem value="Credit">Thẻ tín dụng</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {mode === "create" ? (
              <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>
                  <Activity size={12} className="inline mr-1" /> Trạng thái
                </Label>
                <p className={cn(FORM_INPUT_CLASS, "h-14 flex items-center text-sm text-slate-600 font-medium")}>
                  Phiếu mới: <span className="ml-1 font-semibold text-slate-800">Chờ xử lý</span>
                  <span className="text-slate-400 font-normal ml-1">(server — hoàn tất sau khi lưu)</span>
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Label className={FORM_LABEL_CLASS}>
                  <Activity size={12} className="inline mr-1" /> Trạng thái
                </Label>
                <Select
                  value={watch("status") ?? "Pending"}
                  onValueChange={(val) => setValue("status", val as "Completed" | "Pending" | "Cancelled")}
                  disabled={lockStatusSelect}
                >
                  <SelectTrigger
                    disabled={lockStatusSelect}
                    className={cn(FORM_INPUT_CLASS, "h-14 font-bold")}
                  >
                    <SelectValue placeholder="Chọn trạng thái..." />
                  </SelectTrigger>
                  <SelectContent className="rounded-xl border-slate-200 shadow-xl">
                    <SelectItem value="Completed">Hoàn thành</SelectItem>
                    <SelectItem value="Pending">Chờ xử lý</SelectItem>
                    <SelectItem value="Cancelled">Đã hủy</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Row 4: Full width description */}
            <div className="col-span-2 space-y-2">
                <Label className={FORM_LABEL_CLASS}>
                    <FileText size={12} className="inline mr-1" /> Nội dung diễn giải
                </Label>
                <Input
                  {...register("description")}
                  placeholder="VD: Thu tiền bán hàng cho khách A..."
                  disabled={lockDescription}
                  className={cn(FORM_INPUT_CLASS, "h-14 font-medium")}
                />
            </div>
          </div>
        </form>

        <DialogFooter className="p-8 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
           <div className="hidden md:block">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Xác thực tài chính</p>
              <p className="text-xs text-slate-500 font-medium italic">Ghi nhật ký hệ thống: {new Date().toLocaleDateString()}</p>
           </div>
           <div className="flex gap-3">
              <Button variant="ghost" onClick={onClose} className="px-6 font-bold text-slate-400 hover:text-slate-900 rounded-xl">Hủy bỏ</Button>
              <Button 
                onClick={handleSubmit(onFormSubmit)}
                disabled={mode === "create" && (fundsLoading || fundOptions.length === 0)}
                className="px-8 font-semibold bg-slate-900 hover:bg-slate-800 rounded-lg text-white"
              >
                {mode === 'edit' ? <Save className="mr-2" size={18} /> : <PlusCircle className="mr-2" size={18} />}
                {mode === 'edit' ? "Lưu thay đổi" : "Lập phiếu"}
              </Button>
           </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
