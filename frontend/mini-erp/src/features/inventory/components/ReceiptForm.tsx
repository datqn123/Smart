import { useState, useMemo, useEffect } from "react"
import { useForm, useFieldArray, FormProvider } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, X, Save, Send, ShoppingCart, Info, Trash2, CheckCircle2, XCircle, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { formatCurrency, formatDate } from "../utils"
import type { StockReceipt } from "../types"
import { calculateReceiptTotal } from "../inboundLogic"
import { type ReceiptFormProductOption, catalogUnitForProduct } from "../receiptFormCatalog"
import {
  approveStockReceipt,
  rejectStockReceipt,
  STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS,
  STOCK_RECEIPT_REJECT_REASON_MIN_LEN,
} from "../api/stockReceiptsApi"
import { ApiRequestError } from "@/lib/api/http"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import {
  FORM_LABEL_CLASS,
  FORM_INPUT_CLASS,
  TABLE_HEAD_CLASS,
  TABLE_CELL_PRIMARY_CLASS,
  TABLE_CELL_SECONDARY_CLASS,
  TABLE_CELL_MONO_CLASS,
  TABLE_CELL_NUMBER_CLASS,
} from "@/lib/data-table-layout"
import {
  getProductById,
  getProductListAllPages,
  type ProductListItemDto,
} from "@/features/product-management/api/productsApi"
import { receiptSchema, type ReceiptFormData } from "../receiptFormSchema"
import { catalogCostForReceiptUnit } from "../receiptFormProductCost"
import { ReceiptLineBatchExpiryFields } from "./ReceiptLineBatchExpiryFields"

/** Ghi đè `disabled:opacity-50` từ Input/Select: phiếu chờ duyệt vẫn full opacity, chỉ không tương tác. */
const FORM_FIELD_DISABLED_OPAQUE = "disabled:opacity-100"

export type { ReceiptFormData }

interface ReceiptFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  receipt?: StockReceipt
  onSubmit: (data: ReceiptFormData, saveMode: "draft" | "pending") => void | Promise<void>
  /** Admin hoặc Owner + `can_approve` (JWT); hiển thị Duyệt / Từ chối khi phiếu `Pending`. */
  canApprove?: boolean
  /** Sau approve/reject thành công — vd. invalidate list + detail. */
  onAfterApproveOrReject?: (receiptId: number) => void | Promise<void>
}

const mockSuppliers = [
  { id: 1, name: "Công ty TNHH Vinamilk" },
  { id: 2, name: "Nhà phân phối PepsiCo" },
  { id: 3, name: "Công ty Hàng Tiêu Dùng" },
  { id: 4, name: "Công ty Masan" },
  { id: 5, name: "Đại lý Unilever" },
]

function buildReceiptFormDefaultValues(receipt: StockReceipt | undefined): ReceiptFormData {
  if (receipt) {
    return {
      supplierId: receipt.supplierId,
      receiptDate: receipt.receiptDate,
      invoiceNumber: receipt.invoiceNumber || "",
      notes: receipt.notes || "",
      details: receipt.details.map((d) => ({
        productId: d.productId,
        unitId: d.unitId > 0 ? d.unitId : (catalogUnitForProduct(d.productId) ?? 0),
        quantity: d.quantity,
        costPrice: d.costPrice,
        batchNumber: d.batchNumber || "",
        expiryDate: d.expiryDate ? new Date(d.expiryDate).toISOString().split("T")[0] : "",
      })),
    }
  }
  return {
    supplierId: 0 as unknown as number,
    receiptDate: new Date().toISOString().split("T")[0],
    invoiceNumber: "",
    notes: "",
    details: [
      { productId: 0 as unknown as number, unitId: 0 as unknown as number, quantity: 1, costPrice: 0, batchNumber: "", expiryDate: "" },
    ],
  }
}

function mapProductListItemToOption(item: ProductListItemDto): ReceiptFormProductOption {
  return {
    productId: item.id,
    unitId: 0,
    name: item.name,
    sku: item.skuCode,
    unitName: "—",
  }
}

/**
 * Radix Select chỉ hiện label khi có `SelectItem` cùng `value`.
 * Danh sách sản phẩm từ API; phiếu cũ có thể tham chiếu SP đã xóa/không còn trong list — bổ sung từ `receipt.details`.
 */
function mergeProductSelectOptions(
  fromApi: ReceiptFormProductOption[],
  receipt: StockReceipt | undefined,
): ReceiptFormProductOption[] {
  const base = fromApi
  if (!receipt?.details?.length) {
    return base
  }
  const have = new Set(base.map((p) => p.productId))
  const extra: ReceiptFormProductOption[] = []
  for (const d of receipt.details) {
    if (!have.has(d.productId)) {
      have.add(d.productId)
      extra.push({
        productId: d.productId,
        unitId: d.unitId,
        name: d.productName,
        sku: d.skuCode,
        unitName: d.unitName,
      })
    }
  }
  return extra.length > 0 ? [...base, ...extra] : base
}

export function ReceiptForm({
  open,
  onOpenChange,
  receipt,
  onSubmit,
  canApprove = false,
  onAfterApproveOrReject,
}: ReceiptFormProps) {
  const queryClient = useQueryClient()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [inboundLocationId, setInboundLocationId] = useState(1)
  const [approveBusy, setApproveBusy] = useState(false)
  const [rejectBusy, setRejectBusy] = useState(false)
  const [rejectInlineOpen, setRejectInlineOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  // Wizard: step 1 = Header, 2 = Lines, 3 = Review (only for new/Draft)
  const [wizardStep, setWizardStep] = useState(1)

  const form = useForm<ReceiptFormData>({
    resolver: zodResolver(receiptSchema),
    defaultValues: buildReceiptFormDefaultValues(receipt),
  })

  // Đồng bộ form khi mở dialog hoặc đổi phiếu; defaultValues của useForm chỉ áp dụng lúc mount lần đầu.
  useEffect(() => {
    if (!open) {
      return
    }
    form.reset(buildReceiptFormDefaultValues(receipt))
    setWizardStep(1)
  }, [open, form, receipt?.id, receipt?.updatedAt])

  useEffect(() => {
    if (!open) {
      setRejectInlineOpen(false)
      return
    }
    if (receipt) {
      setInboundLocationId(1)
      setApproveBusy(false)
      setRejectBusy(false)
      setRejectInlineOpen(false)
      setRejectReason("")
    }
  }, [open, receipt?.id])

  const productsCatalogQ = useQuery({
    queryKey: ["products", "receipt-form", "all-pages"],
    queryFn: () => getProductListAllPages({ sort: "name:asc" }),
    enabled: open,
    staleTime: 60_000,
  })

  useEffect(() => {
    if (!open || !productsCatalogQ.isError) {
      return
    }
    toast.error("Không tải được danh sách sản phẩm")
  }, [open, productsCatalogQ.isError])

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "details"
  })

  const formValues = form.watch()
  const apiProductOptions = useMemo(
    () => (productsCatalogQ.data ?? []).map(mapProductListItemToOption),
    [productsCatalogQ.data],
  )
  const productSelectOptions = useMemo(
    () => mergeProductSelectOptions(apiProductOptions, receipt),
    [apiProductOptions, receipt],
  )
  const totalAmount = useMemo(() => calculateReceiptTotal(formValues.details || []), [formValues.details])

  const submitWithMode = (saveMode: "draft" | "pending") =>
    form.handleSubmit(async (data) => {
      setIsSubmitting(true)
      try {
        await onSubmit(data, saveMode)
        onOpenChange(false)
      } finally {
        setIsSubmitting(false)
      }
    })

  const isEditable = !receipt || receipt.status === "Draft"
  const showPendingApprovalActions = Boolean(receipt && receipt.status === "Pending" && canApprove)
  // Wizard only active when creating new or editing Draft
  const useWizard = isEditable && !receipt?.id
  const WIZARD_STEPS = ["Thông tin chung", "Chi tiết hàng hóa", "Xem lại & Gửi"]

  const goNextStep = async () => {
    if (wizardStep === 1) {
      const ok = await form.trigger(["supplierId", "receiptDate"])
      if (!ok) return
    }
    if (wizardStep === 2) {
      const ok = await form.trigger(["details"])
      if (!ok) return
    }
    setWizardStep((s) => Math.min(s + 1, 3))
  }
  const goPrevStep = () => setWizardStep((s) => Math.max(s - 1, 1))

  const handleApprove = async () => {
    if (!receipt) {
      return
    }
    setApproveBusy(true)
    try {
      await approveStockReceipt(receipt.id, { inboundLocationId })
      toast.success("Đã phê duyệt phiếu nhập kho")
      await onAfterApproveOrReject?.(receipt.id)
      onOpenChange(false)
    } catch (e) {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không phê duyệt được phiếu nhập")
      } else {
        toast.error("Không phê duyệt được phiếu nhập")
      }
    } finally {
      setApproveBusy(false)
    }
  }

  const handleConfirmReject = async () => {
    if (!receipt) {
      return
    }
    const reason = rejectReason.trim()
    if (!reason) {
      toast.error("Vui lòng nhập lý do từ chối")
      return
    }
    if (reason.length < STOCK_RECEIPT_REJECT_REASON_MIN_LEN) {
      toast.error(`Lý do từ chối phải ghi rõ (tối thiểu ${STOCK_RECEIPT_REJECT_REASON_MIN_LEN} ký tự)`)
      return
    }
    setRejectBusy(true)
    try {
      await rejectStockReceipt(receipt.id, { reason })
      toast.success("Đã từ chối phiếu nhập kho")
      await onAfterApproveOrReject?.(receipt.id)
      setRejectInlineOpen(false)
      onOpenChange(false)
    } catch (e) {
      if (e instanceof ApiRequestError) {
        toast.error(e.body?.message ?? "Không từ chối được phiếu nhập")
      } else {
        toast.error("Không từ chối được phiếu nhập")
      }
    } finally {
      setRejectBusy(false)
    }
  }

  return (
    <FormProvider {...form}>
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] sm:max-w-[90vw] lg:max-w-7xl max-h-[92vh] flex flex-col p-0 overflow-hidden border-slate-200 shadow-3xl">
        <DialogHeader className="p-6 pb-4 bg-slate-50/50 border-b border-slate-100 flex-none text-left">
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-xl font-bold text-slate-900">
                {receipt ? (isEditable ? `Sửa phiếu: ${receipt.receiptCode}` : `Chi tiết phiếu: ${receipt.receiptCode}`) : "Tạo mới phiếu nhập kho"}
              </DialogTitle>
              <DialogDescription className="text-slate-500 mt-1">
                {receipt?.status === "Pending"
                  ? "Phiếu đang chờ duyệt — chỉ xem nội dung; dùng Duyệt hoặc Từ chối phiếu nhập nếu bạn có quyền phê duyệt."
                  : receipt?.status === "Rejected"
                    ? "Phiếu đã bị từ chối — chỉ xem nội dung; xem lý do từ chối bên dưới."
                    : "Điền đầy đủ các thông tin hóa đơn và chi tiết mặt hàng nhập kho."}
              </DialogDescription>
            </div>
            <div className="text-right">
                <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Ước tính giá trị (VNĐ)</p>
                <p className="text-2xl font-black text-slate-900">{formatCurrency(totalAmount)}</p>
            </div>
          </div>
        </DialogHeader>

        {/* Wizard step indicator — only for new receipts */}
        {useWizard && (
          <div className="px-6 py-3 border-b border-slate-100 bg-white shrink-0">
            <div className="flex items-center gap-0">
              {WIZARD_STEPS.map((label, i) => {
                const step = i + 1
                const isActive = wizardStep === step
                const isDone = wizardStep > step
                return (
                  <div key={step} className="flex items-center">
                    <div className="flex items-center gap-2">
                      <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold border-2 transition-colors ${
                        isActive ? "border-slate-900 bg-slate-900 text-white"
                        : isDone ? "border-green-600 bg-green-600 text-white"
                        : "border-slate-200 bg-white text-slate-400"
                      }`}>
                        {isDone ? "✓" : step}
                      </span>
                      <span className={`text-sm font-medium hidden sm:inline ${isActive ? "text-slate-900" : isDone ? "text-green-700" : "text-slate-400"}`}>
                        {label}
                      </span>
                    </div>
                    {i < WIZARD_STEPS.length - 1 && (
                      <ChevronRight className="h-4 w-4 text-slate-300 mx-2 shrink-0" />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          <form
            id="receipt-form"
            onSubmit={(e) => {
              e.preventDefault()
              void submitWithMode("draft")()
            }}
            className="space-y-8"
          >
            {/* Header Info Section — Step 1 (or always show when not wizard) */}
            <div className={`bg-white rounded-xl border border-slate-200 p-6 shadow-sm ${useWizard && wizardStep !== 1 ? "hidden" : ""}`}>
                <div className="flex items-center gap-2 mb-4">
                    <Info size={16} className="text-slate-400" />
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-700">Thông tin chung</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="space-y-1.5">
                    <label className={FORM_LABEL_CLASS}>Nhà cung cấp *</label>
                    <Select 
                        value={form.watch("supplierId")?.toString() || ""} 
                        onValueChange={(val) => form.setValue("supplierId", parseInt(val))}
                        disabled={!isEditable}
                    >
                        <SelectTrigger className={cn(FORM_INPUT_CLASS, "w-full", FORM_FIELD_DISABLED_OPAQUE)}>
                        <SelectValue placeholder="Chọn đối tác..." />
                        </SelectTrigger>
                        <SelectContent>
                        {mockSuppliers.map(s => (
                            <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                        ))}
                        </SelectContent>
                    </Select>
                    {form.formState.errors.supplierId && (
                        <p className="text-[10px] text-red-500 font-bold px-1">{form.formState.errors.supplierId.message}</p>
                    )}
                    </div>

                    <div className="space-y-1.5">
                    <label className={FORM_LABEL_CLASS}>Ngày nhập thực tế *</label>
                    <Input
                        type="date"
                        {...form.register("receiptDate")}
                        disabled={!isEditable}
                        className={cn(FORM_INPUT_CLASS, FORM_FIELD_DISABLED_OPAQUE)}
                    />
                    {form.formState.errors.receiptDate && (
                        <p className="text-[10px] text-red-500 font-bold px-1">{form.formState.errors.receiptDate.message}</p>
                    )}
                    </div>

                    <div className="space-y-1.5">
                    <label className={FORM_LABEL_CLASS}>Số hóa đơn / Chứng từ</label>
                    <Input
                        placeholder="VD: INV-001..."
                        {...form.register("invoiceNumber")}
                        disabled={!isEditable}
                        className={cn(FORM_INPUT_CLASS, "font-mono", FORM_FIELD_DISABLED_OPAQUE)}
                    />
                    </div>

                    <div className="space-y-1.5">
                        <label className={FORM_LABEL_CLASS}>Ghi chú phiếu</label>
                        <Input
                            placeholder="Mô tả ngắn..."
                            {...form.register("notes")}
                            disabled={!isEditable}
                            className={cn(FORM_INPUT_CLASS, FORM_FIELD_DISABLED_OPAQUE)}
                        />
                    </div>
                </div>
            </div>

            {receipt?.status === "Rejected" && (!useWizard || wizardStep === 1) && (
              <div className="rounded-xl border border-red-200 bg-red-50/70 p-5">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-100 text-red-700">
                    <XCircle className="h-5 w-5" aria-hidden />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-black uppercase tracking-widest text-red-800">Phiếu đã bị từ chối</p>
                    <p className="mt-2 text-sm font-semibold text-slate-900">Lý do từ chối</p>
                    <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-red-950/90">
                      {receipt.rejectionReason?.trim() ? receipt.rejectionReason.trim() : "Không ghi nhận lý do cụ thể trên hệ thống."}
                    </p>
                    {(receipt.reviewedByName || receipt.reviewedAt) && (
                      <p className="mt-3 text-xs text-slate-600">
                        {receipt.reviewedByName ? (
                          <span>
                            Người xử lý: <span className="font-medium text-slate-800">{receipt.reviewedByName}</span>
                          </span>
                        ) : null}
                        {receipt.reviewedAt ? (
                          <span className={receipt.reviewedByName ? " ml-2" : ""}>· {formatDate(receipt.reviewedAt)}</span>
                        ) : null}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Product Items Table Section — Step 2 */}
            <div className={`bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm ${useWizard && wizardStep !== 2 ? "hidden" : ""}`}>
              <div className="flex flex-col gap-4 border-b border-slate-200 bg-slate-50/80 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-2">
                    <ShoppingCart size={18} className="text-slate-400" />
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-700">Chi tiết hàng hóa ({fields.length})</h3>
                </div>
                <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-end sm:gap-4 sm:shrink-0">
                  {showPendingApprovalActions && (
                    <div className="flex w-full flex-col gap-1.5 sm:max-w-[260px] sm:text-right">
                      <label
                        className="text-[10px] font-bold uppercase tracking-widest text-slate-500 sm:text-right"
                        htmlFor="receipt-form-inbound-location"
                      >
                        Vị trí nhập kho
                      </label>
                      <Select
                        value={String(inboundLocationId)}
                        onValueChange={(v) => setInboundLocationId(parseInt(v, 10))}
                        disabled={approveBusy || rejectBusy}
                      >
                        <SelectTrigger id="receipt-form-inbound-location" className="h-9 border-slate-200 bg-white sm:w-full">
                          <SelectValue placeholder="Chọn vị trí…" />
                        </SelectTrigger>
                        <SelectContent>
                          {STOCK_RECEIPT_APPROVE_LOCATION_OPTIONS.map((o) => (
                            <SelectItem key={o.id} value={String(o.id)}>
                              {o.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  {isEditable && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => append({ productId: 0 as unknown as number, unitId: 0 as unknown as number, quantity: 1, costPrice: 0, batchNumber: "", expiryDate: "" })}
                      className="h-9 shrink-0 border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                    >
                      <Plus className="mr-2 h-4 w-4" /> Thêm mặt hàng
                    </Button>
                  )}
                </div>
              </div>

              <div className="overflow-x-auto min-h-[300px]">
                <Table className="border-collapse">
                  <TableHeader className="bg-slate-50/50">
                    <TableRow className="hover:bg-transparent">
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[50px] text-left")}>#</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "min-w-[280px] text-left")}>Sản phẩm *</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[100px] text-left")}>ĐVT</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[120px] text-left")}>Số lượng *</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[150px] text-left")}>Đơn giá *</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[150px] text-left")}>Số lô</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[160px] text-left")}>Hạn sử dụng</TableHead>
                      <TableHead className={cn(TABLE_HEAD_CLASS, "w-[150px] text-left")}>Thành tiền</TableHead>
                      {isEditable && <TableHead className="w-[60px] text-left" />}
                    </TableRow>
                  </TableHeader>
                  <TableBody className="divide-y divide-slate-100">
                    {fields.map((field, index) => {
                      const detail = formValues.details[index]
                      const product = productSelectOptions.find((p) => p.productId === detail?.productId)
                      const lineTotal = (detail?.quantity || 0) * (detail?.costPrice || 0)

                      return (
                        <TableRow key={field.id} className="hover:bg-slate-50/30 transition-colors group h-14">
                          <TableCell className={cn("text-left", TABLE_CELL_MONO_CLASS)}>
                            {index + 1}
                          </TableCell>
                          <TableCell className="px-2 py-1.5 focus-within:z-10">
                            <Select
                              value={detail?.productId?.toString() || ""}
                              onValueChange={(val) => {
                                const pid = parseInt(val, 10)
                                form.setValue(`details.${index}.productId`, pid)
                                form.setValue(`details.${index}.batchNumber`, "")
                                form.setValue(`details.${index}.expiryDate`, "")
                                const opt = productSelectOptions.find((p) => p.productId === pid)
                                if (opt != null) {
                                  form.setValue(`details.${index}.unitId`, opt.unitId)
                                } else {
                                  const uid = catalogUnitForProduct(pid)
                                  if (uid != null) {
                                    form.setValue(`details.${index}.unitId`, uid)
                                  }
                                }
                                void (async () => {
                                  try {
                                    const productDetail = await queryClient.fetchQuery({
                                      queryKey: ["product-detail", pid],
                                      queryFn: () => getProductById(pid),
                                      staleTime: 60_000,
                                    })
                                    let unitId = opt?.unitId ?? catalogUnitForProduct(pid) ?? 0
                                    if (unitId <= 0) {
                                      unitId =
                                        productDetail.units?.find((u) => u.isBaseUnit)?.id ??
                                        productDetail.units?.[0]?.id ??
                                        0
                                    }
                                    if (unitId > 0) {
                                      form.setValue(`details.${index}.unitId`, unitId)
                                      form.setValue(
                                        `details.${index}.costPrice`,
                                        catalogCostForReceiptUnit(productDetail, unitId),
                                      )
                                    }
                                  } catch {
                                    /* giữ đơn giá hiện tại / nhập tay */
                                  }
                                })()
                              }}
                              disabled={!isEditable || productsCatalogQ.isLoading}
                            >
                              <SelectTrigger
                                className={cn(
                                  FORM_INPUT_CLASS,
                                  "h-10 w-full min-w-0 text-left group-hover:bg-white focus:bg-white transition-all shadow-none",
                                  FORM_FIELD_DISABLED_OPAQUE,
                                )}
                              >
                                <SelectValue
                                  placeholder={
                                    productsCatalogQ.isLoading ? "Đang tải danh sách sản phẩm…" : "Chọn sản phẩm…"
                                  }
                                />
                              </SelectTrigger>
                              <SelectContent>
                                {productSelectOptions.map((p) => (
                                  <SelectItem key={p.productId} value={p.productId.toString()}>
                                    <div className="flex flex-col text-left">
                                        <span className={TABLE_CELL_PRIMARY_CLASS}>{p.name}</span>
                                        <span className={cn(TABLE_CELL_MONO_CLASS, "text-[10px] text-slate-400")}>SKU: {p.sku}</span>
                                    </div>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell className="text-left">
                             <span className={cn(TABLE_CELL_SECONDARY_CLASS, "inline-block w-full bg-slate-50 px-2 py-1 text-left")}>
                                {product?.unitName || "—"}
                             </span>
                          </TableCell>
                          <TableCell className="px-1 text-left">
                            <Input
                              type="number"
                              {...form.register(`details.${index}.quantity`, { valueAsNumber: true })}
                              disabled={!isEditable}
                              className={cn(
                                FORM_INPUT_CLASS,
                                "h-10 text-left group-hover:bg-white focus:bg-white",
                                FORM_FIELD_DISABLED_OPAQUE,
                              )}
                            />
                          </TableCell>
                          <TableCell className="px-1 text-left">
                            <Input
                              type="number"
                              {...form.register(`details.${index}.costPrice`, { valueAsNumber: true })}
                              disabled={!isEditable}
                              className={cn(
                                FORM_INPUT_CLASS,
                                "h-10 text-left group-hover:bg-white focus:bg-white",
                                FORM_FIELD_DISABLED_OPAQUE,
                              )}
                            />
                          </TableCell>
                          <ReceiptLineBatchExpiryFields
                            rowIndex={index}
                            productId={detail?.productId > 0 ? detail.productId : 0}
                            isEditable={isEditable}
                            dialogOpen={open}
                          />
                          <TableCell className="pr-2 text-left">
                             <span className={cn(TABLE_CELL_NUMBER_CLASS, "text-left")}>{formatCurrency(lineTotal)}</span>
                          </TableCell>
                          
                          {isEditable && (
                            <TableCell className="w-[60px] text-left">
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => remove(index)}
                                className="h-8 w-8 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-full opacity-0 group-hover:opacity-100 transition-all"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          )}
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
              
              {fields.length === 0 && (
                  <div className="py-12 text-center text-slate-400 italic bg-white">
                      Nhấn "Thêm mặt hàng" để bắt đầu nhập liệu
                  </div>
              )}
            </div>
            
            {(form.formState.errors.details || form.formState.errors.root) && (!useWizard || wizardStep === 2) && (
              <div className="p-4 bg-red-50 border border-red-100 rounded-lg flex items-center gap-3">
                  <X className="text-red-500" size={18} />
                  <p className="text-sm text-red-600 font-bold">
                    {form.formState.errors.details?.message || form.formState.errors.details?.root?.message || "Dữ liệu không hợp lệ, vui lòng kiểm tra lại các trường đánh dấu *"}
                  </p>
              </div>
            )}

            {/* Step 3: Review & Submit */}
            {useWizard && wizardStep === 3 && (
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle2 className="h-5 w-5 text-slate-400" />
                  <h3 className="text-sm font-black uppercase tracking-widest text-slate-700">Xem lại trước khi gửi</h3>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="space-y-0.5">
                    <p className="text-xs text-slate-500 uppercase font-semibold tracking-wide">Nhà cung cấp</p>
                    <p className="font-medium text-slate-900">
                      {mockSuppliers.find((s) => s.id === formValues.supplierId)?.name ?? `ID: ${formValues.supplierId}`}
                    </p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-xs text-slate-500 uppercase font-semibold tracking-wide">Ngày nhập</p>
                    <p className="font-medium text-slate-900">{formValues.receiptDate}</p>
                  </div>
                  {formValues.invoiceNumber && (
                    <div className="space-y-0.5">
                      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wide">Số hóa đơn</p>
                      <p className="font-mono text-slate-900">{formValues.invoiceNumber}</p>
                    </div>
                  )}
                  {formValues.notes && (
                    <div className="space-y-0.5 col-span-2">
                      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wide">Ghi chú</p>
                      <p className="text-slate-700">{formValues.notes}</p>
                    </div>
                  )}
                </div>
                <div className="border-t border-slate-100 pt-4">
                  <p className="text-xs text-slate-500 uppercase font-semibold tracking-wide mb-2">
                    Hàng hóa ({fields.length} dòng)
                  </p>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {formValues.details.map((d, i) => {
                      const prod = productSelectOptions.find((p) => p.productId === d.productId)
                      const lineTotal = (d.quantity || 0) * (d.costPrice || 0)
                      return (
                        <div key={i} className="flex items-center justify-between gap-3 text-sm bg-slate-50 rounded-lg px-3 py-2">
                          <span className="truncate font-medium text-slate-800">{prod?.name ?? `SP #${d.productId}`}</span>
                          <span className="shrink-0 text-slate-600 tabular-nums">
                            {d.quantity} × {formatCurrency(d.costPrice)} = <span className="font-semibold text-slate-900">{formatCurrency(lineTotal)}</span>
                          </span>
                        </div>
                      )
                    })}
                  </div>
                  <div className="mt-3 flex justify-end">
                    <p className="text-base font-bold text-slate-900">
                      Tổng: <span className="text-xl">{formatCurrency(totalAmount)}</span>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>

        <DialogFooter className="w-full flex-none flex-col gap-0 border-t border-slate-200 bg-slate-50 p-6 sm:flex-row sm:justify-start">
          <div className="flex w-full flex-col gap-4">
            <div className="flex w-full min-h-[44px] flex-row flex-wrap items-center justify-between gap-3">
              {/* Left: Reject (for pending approval) or Back (wizard) */}
              <div className="flex shrink-0 items-center gap-2">
                {showPendingApprovalActions && (
                  <Button
                    type="button"
                    variant="outline"
                    className={cn(
                      "h-11 shrink-0 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700",
                      rejectInlineOpen && "bg-red-50/80 ring-2 ring-red-300",
                    )}
                    onClick={() => {
                      setRejectReason("")
                      setRejectInlineOpen((v) => !v)
                    }}
                    disabled={approveBusy || rejectBusy}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    {rejectInlineOpen ? "Đóng nhập lý do" : "Từ chối phiếu nhập"}
                  </Button>
                )}
                {useWizard && wizardStep > 1 && (
                  <Button type="button" variant="outline" className="h-11" onClick={goPrevStep} disabled={isSubmitting}>
                    ← Quay lại
                  </Button>
                )}
              </div>

              {/* Right: Wizard Next / Save / Submit / Approve */}
              <div className="flex flex-wrap items-center justify-end gap-3">
                {useWizard && wizardStep < 3 && (
                  <Button
                    type="button"
                    className="h-11 min-w-[120px] bg-slate-900 text-white hover:bg-slate-800"
                    onClick={() => void goNextStep()}
                  >
                    Tiếp theo <ChevronRight className="ml-1 h-4 w-4" />
                  </Button>
                )}

                {(!useWizard || wizardStep === 3) && isEditable && (
                  <>
                    <Button
                      type="button"
                      variant="outline"
                      disabled={isSubmitting}
                      className="h-11 border-slate-300 bg-white"
                      onClick={() => void submitWithMode("draft")()}
                    >
                      <Save className="mr-2 h-4 w-4" />
                      Lưu bản nháp
                    </Button>
                    <Button
                      type="button"
                      disabled={isSubmitting}
                      className="h-11 min-w-[140px] bg-slate-900 text-white hover:bg-slate-800"
                      onClick={() => void submitWithMode("pending")()}
                    >
                      <Send className="mr-2 h-4 w-4" />
                      Gửi yêu cầu duyệt
                    </Button>
                  </>
                )}
                {showPendingApprovalActions && (
                  <Button
                    type="button"
                    className="h-11 min-w-[120px] shrink-0 bg-slate-900 text-white hover:bg-slate-800"
                    onClick={() => void handleApprove()}
                    disabled={approveBusy || rejectBusy}
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Duyệt
                  </Button>
                )}
              </div>
            </div>

            {showPendingApprovalActions && rejectInlineOpen && (
              <div className="w-full max-w-2xl space-y-3 rounded-xl border border-red-200 bg-red-50/60 p-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900">Từ chối phiếu nhập</p>
                  <p className="mt-0.5 text-xs text-slate-600">
                    Nhập lý do rõ ràng (tối thiểu {STOCK_RECEIPT_REJECT_REASON_MIN_LEN} ký tự). « Xác nhận từ chối » gửi lên server.
                  </p>
                </div>
                <Textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Ví dụ: Số lượng không khớp hóa đơn gốc — cần đính kèm bằng chứng…"
                  disabled={rejectBusy}
                  className="min-h-[120px] bg-white text-sm"
                  minLength={STOCK_RECEIPT_REJECT_REASON_MIN_LEN}
                  maxLength={2000}
                  aria-label="Lý do từ chối"
                />
                <div className="flex flex-row flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="h-11 min-h-[44px] min-w-[88px]"
                    onClick={() => {
                      setRejectInlineOpen(false)
                      setRejectReason("")
                    }}
                    disabled={rejectBusy}
                  >
                    Hủy
                  </Button>
                  <Button
                    type="button"
                    className="h-11 min-h-[44px] min-w-[168px] bg-red-600 font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-60"
                    onClick={() => void handleConfirmReject()}
                    disabled={rejectBusy}
                  >
                    Xác nhận từ chối
                  </Button>
                </div>
              </div>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
    </FormProvider>
  )
}