import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useState, useEffect, useMemo, useCallback, type UIEvent } from "react"
import { useInfiniteQuery } from "@tanstack/react-query"
import type { InventoryItem } from "../types"
import { ArrowDownToLine, ArrowUpFromLine, AlertCircle } from "lucide-react"
import { getSupplierList } from "@/features/product-management/api/suppliersApi"
import type { StockReceiptCreateBody, StockReceiptCreateSaveMode } from "../api/stockReceiptsApi"
import type { StockDispatchCreateBody } from "../api/dispatchApi"
import { cn } from "@/lib/utils"
import { DATA_TABLE_ROOT_CLASS, FORM_INPUT_CLASS, FORM_LABEL_CLASS } from "@/lib/data-table-layout"

const SUPPLIER_PAGE_SIZE = 50

/** Same visual height (44px) for every control; `Input` defaults to `h-9`, `SelectTrigger` to `data-[size=default]:h-9`. */
const STOCK_ACTION_FORM_FIELD_CLASS = cn(FORM_INPUT_CLASS, "rounded-lg py-0")

const STOCK_ACTION_SELECT_TRIGGER_CLASS = cn(
  STOCK_ACTION_FORM_FIELD_CLASS,
  "w-full shrink-0 h-11 min-h-11 data-[size=default]:h-11",
)

interface StockActionDialogProps {
  isOpen: boolean
  onClose: () => void
  items: InventoryItem[]
  type: "import" | "export"
  onImportSubmit: (body: StockReceiptCreateBody) => Promise<void>
  onExportSubmit: (body: StockDispatchCreateBody) => Promise<void>
}

function todayIsoDate(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
}

export function StockActionDialog({
  isOpen,
  onClose,
  items,
  type,
  onImportSubmit,
  onExportSubmit,
}: StockActionDialogProps) {
  const [quantities, setQuantities] = useState<Record<number, number>>({})
  const [costPrices, setCostPrices] = useState<Record<number, number>>({})
  const [batchNumbers, setBatchNumbers] = useState<Record<number, string>>({})
  const [expiryDates, setExpiryDates] = useState<Record<number, string>>({})
  const [supplierId, setSupplierId] = useState<string>("")
  const [receiptDate, setReceiptDate] = useState(todayIsoDate())
  const [invoiceNumber, setInvoiceNumber] = useState("")
  const [notes, setNotes] = useState("")
  const [saveMode, setSaveMode] = useState<StockReceiptCreateSaveMode>("draft")
  const [dispatchDate, setDispatchDate] = useState(todayIsoDate())
  const [referenceLabel, setReferenceLabel] = useState("")
  const [exportNotes, setExportNotes] = useState("")
  const [busy, setBusy] = useState(false)

  const suppliersInfinite = useInfiniteQuery({
    queryKey: ["suppliers", "v1", "infinite", "stock-action", "Active", SUPPLIER_PAGE_SIZE],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      getSupplierList({ page: pageParam, limit: SUPPLIER_PAGE_SIZE, status: "Active" }),
    getNextPageParam: (lastPage) => {
      if (lastPage.items.length < lastPage.limit) {
        return undefined
      }
      if (lastPage.page * lastPage.limit >= lastPage.total) {
        return undefined
      }
      return lastPage.page + 1
    },
    enabled: isOpen && type === "import",
  })

  const supplierItems = useMemo(
    () => suppliersInfinite.data?.pages.flatMap((p) => p.items) ?? [],
    [suppliersInfinite.data?.pages],
  )

  const { fetchNextPage, hasNextPage, isFetchingNextPage } = suppliersInfinite

  /** Radix Select scrolls the viewport, not the content root — wired via `SelectContent.onViewportScroll`. */
  const handleSupplierViewportScroll = useCallback(
    (e: UIEvent<HTMLDivElement>) => {
      const el = e.currentTarget
      if (el.scrollHeight - el.scrollTop - el.clientHeight > 48) {
        return
      }
      if (hasNextPage && !isFetchingNextPage) {
        void fetchNextPage()
      }
    },
    [fetchNextPage, hasNextPage, isFetchingNextPage],
  )

  useEffect(() => {
    if (!isOpen) {
      return
    }
    const q0: Record<number, number> = {}
    const c0: Record<number, number> = {}
    const b0: Record<number, string> = {}
    const e0: Record<number, string> = {}
    items.forEach((item) => {
      q0[item.id] = 0
      c0[item.id] = item.costPrice
      b0[item.id] = item.batchNumber ?? ""
      e0[item.id] = item.expiryDate ? item.expiryDate.split("T")[0] : ""
    })
    setQuantities(q0)
    setCostPrices(c0)
    setBatchNumbers(b0)
    setExpiryDates(e0)
    setReceiptDate(todayIsoDate())
    setDispatchDate(todayIsoDate())
    setInvoiceNumber("")
    setNotes("")
    setExportNotes("")
    setReferenceLabel("")
    setSaveMode("draft")
    setSupplierId("")
    setBusy(false)
  }, [isOpen, items])

  const handleQtyChange = (id: number, val: string) => {
    const num = parseInt(val, 10) || 0
    setQuantities((prev) => ({ ...prev, [id]: num }))
  }

  const isInvalid = items.length === 0 || Object.values(quantities).every((q) => q <= 0)
  const hasExportError = type === "export" && items.some((item) => (quantities[item.id] || 0) > item.quantity)

  const missingUnit = useMemo(
    () => items.some((i) => i.unitId == null || i.unitId <= 0),
    [items],
  )

  const importHeaderInvalid = type === "import" && (!supplierId || supplierId === "0")

  const handleSubmit = async () => {
    if (type === "import") {
      const sid = parseInt(supplierId, 10)
      if (!sid || Number.isNaN(sid)) {
        return
      }
      const details = items
        .map((item) => {
          const qty = quantities[item.id] || 0
          if (qty <= 0) {
            return null
          }
          const uid = item.unitId
          if (uid == null || uid <= 0) {
            return null
          }
          const cost = costPrices[item.id] ?? item.costPrice
          const batch = batchNumbers[item.id]?.trim() || null
          // BE dùng `LocalDate.parse` → chỉ chấp nhận `YYYY-MM-DD` (API_Task014 / StockReceiptLifecycleService).
          const expDay = expiryDates[item.id]?.trim()
          const exp = expDay ? expDay.slice(0, 10) : null
          return {
            productId: item.productId,
            unitId: uid,
            quantity: qty,
            costPrice: Math.max(0, cost),
            batchNumber: batch,
            expiryDate: exp,
          }
        })
        .filter((d): d is NonNullable<typeof d> => d != null)
      if (details.length === 0) {
        return
      }
      const body: StockReceiptCreateBody = {
        supplierId: sid,
        receiptDate: receiptDate,
        invoiceNumber: invoiceNumber.trim() || undefined,
        notes: notes.trim() || undefined,
        saveMode,
        details,
      }
      setBusy(true)
      try {
        await onImportSubmit(body)
        onClose()
      }
      finally {
        setBusy(false)
      }
    }
    else {
      const lines = items
        .map((item) => {
          const qty = quantities[item.id] || 0
          if (qty <= 0) {
            return null
          }
          return { inventoryId: item.id, quantity: qty }
        })
        .filter((l): l is { inventoryId: number; quantity: number } => l != null)
      if (lines.length === 0) {
        return
      }
      const body: StockDispatchCreateBody = {
        dispatchDate,
        referenceLabel: referenceLabel.trim() || undefined,
        notes: exportNotes.trim() || undefined,
        lines,
      }
      setBusy(true)
      try {
        await onExportSubmit(body)
        onClose()
      }
      finally {
        setBusy(false)
      }
    }
  }

  const submitDisabled =
    busy
    || isInvalid
    || hasExportError
    || (type === "import" && (importHeaderInvalid || missingUnit))
    || (type === "import" && suppliersInfinite.isError)

  const supplierPlaceholder =
    suppliersInfinite.isPending && supplierItems.length === 0 ? "Đang tải…" : "Chọn NCC"

  const tableInputClass = (extra?: string) => cn(STOCK_ACTION_FORM_FIELD_CLASS, extra)

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && !busy && onClose()}>
      <DialogContent className="w-[95vw] max-w-[95vw] sm:max-w-[1700px] max-h-[90vh] flex flex-col p-0 gap-0 overflow-hidden border-slate-200 shadow-2xl rounded-2xl">
        <DialogHeader className="p-6 border-b shrink-0">
          <DialogTitle className="text-xl flex h-11 shrink-0 items-center gap-2 leading-none">
            {type === "import" ? (
              <>
                <ArrowDownToLine className="h-5 w-5 shrink-0 text-slate-700" aria-hidden /> Nhập kho hàng loạt
              </>
            ) : (
              <>
                <ArrowUpFromLine className="h-5 w-5 shrink-0 text-slate-700" aria-hidden /> Xuất kho hàng loạt
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {type === "import"
              ? `Tạo phiếu nhập kho từ ${items.length} dòng đã chọn (lưu nháp hoặc gửi chờ duyệt).`
              : `Tạo phiếu xuất kho từ ${items.length} dòng tồn đã chọn.`}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-y-auto p-6 custom-scrollbar space-y-6">
          {type === "import" && (
            <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Thông tin phiếu nhập</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:items-end">
                <div className="space-y-1.5 min-w-0">
                  <Label className={FORM_LABEL_CLASS}>Nhà cung cấp *</Label>
                  <Select value={supplierId} onValueChange={setSupplierId}>
                    <SelectTrigger className={STOCK_ACTION_SELECT_TRIGGER_CLASS}>
                      <SelectValue placeholder={supplierPlaceholder} />
                    </SelectTrigger>
                    <SelectContent
                      className="max-h-[min(320px,50vh)] min-w-[var(--radix-select-trigger-width)]"
                      onViewportScroll={handleSupplierViewportScroll}
                    >
                      {supplierItems.map((s) => (
                        <SelectItem key={s.id} value={String(s.id)}>
                          {s.name}
                        </SelectItem>
                      ))}
                      {suppliersInfinite.isFetchingNextPage && (
                        <div className="px-2 py-2 text-xs text-muted-foreground">Đang tải…</div>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className={FORM_LABEL_CLASS}>Ngày nhập *</Label>
                  <Input
                    type="date"
                    value={receiptDate}
                    onChange={(e) => setReceiptDate(e.target.value)}
                    className={STOCK_ACTION_FORM_FIELD_CLASS}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className={FORM_LABEL_CLASS}>Cách lưu</Label>
                  <Select value={saveMode} onValueChange={(v) => setSaveMode(v as StockReceiptCreateSaveMode)}>
                    <SelectTrigger className={STOCK_ACTION_SELECT_TRIGGER_CLASS}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft">Nháp</SelectItem>
                      <SelectItem value="pending">Gửi chờ duyệt</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className={FORM_LABEL_CLASS}>Số hóa đơn</Label>
                  <Input
                    value={invoiceNumber}
                    onChange={(e) => setInvoiceNumber(e.target.value)}
                    placeholder="INV-…"
                    className={STOCK_ACTION_FORM_FIELD_CLASS}
                  />
                </div>
                <div className="space-y-1.5 sm:col-span-2 lg:col-span-4">
                  <Label className={FORM_LABEL_CLASS}>Ghi chú phiếu</Label>
                  <Input value={notes} onChange={(e) => setNotes(e.target.value)} className={FORM_INPUT_CLASS} />
                </div>
              </div>
            </div>
          )}

          {type === "export" && (
            <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-4 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Thông tin phiếu xuất</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:items-end">
                <div className="space-y-1.5">
                  <Label className={FORM_LABEL_CLASS}>Ngày xuất *</Label>
                  <Input
                    type="date"
                    value={dispatchDate}
                    onChange={(e) => setDispatchDate(e.target.value)}
                    className={STOCK_ACTION_FORM_FIELD_CLASS}
                  />
                </div>
                <div className="space-y-1.5 min-w-0">
                  <Label className={FORM_LABEL_CLASS}>Tham chiếu / Đối tượng</Label>
                  <Input
                    value={referenceLabel}
                    onChange={(e) => setReferenceLabel(e.target.value)}
                    placeholder="VD: Khách lẻ, cửa hàng…"
                    className={STOCK_ACTION_FORM_FIELD_CLASS}
                  />
                </div>
                <div className="space-y-1.5 md:col-span-3">
                  <Label className={FORM_LABEL_CLASS}>Ghi chú</Label>
                  <Input value={exportNotes} onChange={(e) => setExportNotes(e.target.value)} className={STOCK_ACTION_FORM_FIELD_CLASS} />
                </div>
              </div>
            </div>
          )}

          {type === "import" && missingUnit && (
            <div className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Một số dòng thiếu mã đơn vị tính — hãy cập nhật tồn kho (Sửa) trước khi nhập.
            </div>
          )}

          <div className="w-full min-w-0 rounded-lg border border-slate-200/80 overflow-hidden">
            <Table
              containerClassName="overflow-x-visible min-w-0"
              className={cn(DATA_TABLE_ROOT_CLASS, "text-sm")}
            >
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[28%] max-w-0 whitespace-normal px-3">Sản phẩm</TableHead>
                  <TableHead className="w-[14%] px-2">Hiện tại</TableHead>
                  <TableHead className="w-[11%] px-2">{type === "import" ? "SL nhập" : "SL xuất"}</TableHead>
                  {type === "import" && (
                    <>
                      <TableHead className="w-[11%] px-2">Giá vốn</TableHead>
                      <TableHead className="w-[12%] px-2">Số lô</TableHead>
                      <TableHead className="w-[12%] px-2">Hạn SD</TableHead>
                    </>
                  )}
                  <TableHead className={cn("text-right px-3", type === "import" ? "w-[12%]" : "w-[47%]")}>
                    Dự kiến
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => {
                  const adj = quantities[item.id] || 0
                  const expected = type === "import" ? item.quantity + adj : item.quantity - adj
                  const error = type === "export" && adj > item.quantity

                  return (
                    <TableRow key={item.id}>
                      <TableCell className="max-w-0 min-w-0 p-2 align-middle whitespace-normal">
                        <div className="truncate font-bold text-slate-900" title={item.productName}>
                          {item.productName}
                        </div>
                        <div className="truncate text-xs text-slate-500" title={item.skuCode}>
                          {item.skuCode}
                        </div>
                      </TableCell>
                      <TableCell className="p-2 text-slate-600 font-medium whitespace-normal align-middle">
                        {item.quantity} {item.unitName}
                      </TableCell>
                      <TableCell className="p-2 align-middle">
                        <Input
                          type="number"
                          min={0}
                          value={adj || ""}
                          onChange={(e) => handleQtyChange(item.id, e.target.value)}
                          className={tableInputClass(
                            error ? "border-red-500 focus-visible:ring-red-500" : "border-slate-200 focus:border-slate-900",
                          )}
                        />
                        {error && (
                          <div className="text-[10px] text-red-600 font-bold flex items-center gap-1 mt-1">
                            <AlertCircle className="h-3 w-3" /> Vượt quá tồn kho
                          </div>
                        )}
                      </TableCell>
                      {type === "import" && (
                        <>
                          <TableCell className="p-2 align-middle">
                            <Input
                              type="number"
                              min={0}
                              value={costPrices[item.id] ?? ""}
                              onChange={(e) =>
                                setCostPrices((prev) => ({
                                  ...prev,
                                  [item.id]: parseInt(e.target.value, 10) || 0,
                                }))
                              }
                              className={tableInputClass("border-slate-200")}
                            />
                          </TableCell>
                          <TableCell className="p-2 align-middle">
                            <Input
                              value={batchNumbers[item.id] ?? ""}
                              onChange={(e) =>
                                setBatchNumbers((prev) => ({ ...prev, [item.id]: e.target.value }))
                              }
                              className={tableInputClass("border-slate-200 text-xs")}
                              placeholder="Lô"
                            />
                          </TableCell>
                          <TableCell className="p-2 align-middle">
                            <Input
                              type="date"
                              value={expiryDates[item.id] ?? ""}
                              onChange={(e) =>
                                setExpiryDates((prev) => ({ ...prev, [item.id]: e.target.value }))
                              }
                              className={tableInputClass("border-slate-200 text-xs")}
                            />
                          </TableCell>
                        </>
                      )}
                      <TableCell
                        className={cn(
                          "p-2 text-right font-bold align-middle tabular-nums",
                          expected < 0 ? "text-red-600" : "text-slate-900",
                        )}
                      >
                        {expected}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        </div>

        <DialogFooter className="p-6 border-t bg-slate-50/50 shrink-0">
          <Button variant="ghost" onClick={() => !busy && onClose()} className="rounded-lg" disabled={busy}>
            Hủy
          </Button>
          <Button
            disabled={submitDisabled}
            onClick={() => void handleSubmit()}
            className="rounded-lg px-8 bg-slate-900 text-white hover:bg-slate-800"
          >
            {busy ? "Đang xử lý…" : type === "import" ? "Tạo phiếu nhập" : "Tạo phiếu xuất"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
