import type { ComponentType } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { formatCurrency } from "../utils"
import type { InventoryItem } from "../types"
import type { InventoryDetailResponse } from "../api/inventoryApi"
import { getInventoryRowStatusDisplay } from "../lib/inventoryRowStatus"
import { DollarSign, MapPin, Box, ShieldCheck, Tag, Loader2 } from "lucide-react"

interface StockBatchDetailsDialogProps {
  isOpen: boolean
  onClose: () => void
  /** Dòng đang chọn trên bảng (hiển thị tạm khi đang fetch). */
  listItem: InventoryItem | null
  /** Dữ liệu `GET /api/v1/inventory/{id}?include=relatedLines` khi thành công. */
  detail: InventoryDetailResponse | null
  isDetailPending: boolean
  isDetailError: boolean
}

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000

function isExpiringSoon(expiryDate: string | undefined): boolean {
  if (!expiryDate) return false
  const expiryTime = new Date(expiryDate).getTime()
  const todayStart = new Date(new Date().toDateString()).getTime()
  return expiryTime < todayStart + THIRTY_DAYS_MS
}

type LotRow = {
  id: number
  batchNumber: string
  quantity: number
  expiryDate?: string
  warehouseCode: string
  shelfCode: string
}

function rowsFromDetail(d: InventoryDetailResponse): LotRow[] {
  const main: LotRow = {
    id: d.id,
    batchNumber: d.batchNumber ?? "—",
    quantity: d.quantity,
    expiryDate: d.expiryDate ?? undefined,
    warehouseCode: d.warehouseCode,
    shelfCode: d.shelfCode,
  }
  const rest: LotRow[] = d.relatedLines.map((r) => ({
    id: r.id,
    batchNumber: r.batchNumber ?? "—",
    quantity: r.quantity,
    expiryDate: r.expiryDate ?? undefined,
    warehouseCode: r.warehouseCode,
    shelfCode: r.shelfCode,
  }))
  return [main, ...rest]
}

function DetailItem({ label, value, icon: Icon }: { label: string; value: string | number; icon: ComponentType<{ size?: number }> }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-slate-50/50 rounded-lg border border-slate-100">
      <div className="p-2 bg-white rounded-md border border-slate-200 shadow-sm text-slate-600">
        <Icon size={16} />
      </div>
      <div>
        <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">{label}</p>
        <p className="text-sm font-semibold text-slate-900 mt-0.5">{value}</p>
      </div>
    </div>
  )
}

export function StockBatchDetailsDialog({
  isOpen,
  onClose,
  listItem,
  detail,
  isDetailPending,
  isDetailError,
}: StockBatchDetailsDialogProps) {
  if (!listItem) return null

  const d = detail
  const title = d?.productName ?? listItem.productName
  const sku = d?.skuCode ?? listItem.skuCode
  const unit = d?.unitName ?? listItem.unitName
  const barcode = d?.barcode ?? listItem.barcode ?? sku
  const warehouseCode = d?.warehouseCode ?? listItem.warehouseCode
  const shelfCode = d?.shelfCode ?? listItem.shelfCode
  const costPrice = d?.costPrice ?? listItem.costPrice
  const minQuantity = d?.minQuantity ?? listItem.minQuantity
  const quantity = d?.quantity ?? listItem.quantity
  const totalValue = d?.totalValue ?? listItem.totalValue
  const updatedAt = d?.updatedAt ?? listItem.updatedAt

  const lotRows: LotRow[] = d ? rowsFromDetail(d) : []
  const totalQuantity = d ? lotRows.reduce((sum, b) => sum + b.quantity, 0) : quantity

  /** Luôn khớp cột Trạng thái của bảng (theo dòng đang chọn). */
  const rowStatus = getInventoryRowStatusDisplay(listItem)

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-full sm:max-w-2xl lg:max-w-4xl max-h-[90vh] overflow-y-auto p-0 gap-0 border-slate-200 shadow-2xl">
        <DialogHeader className="p-6 pb-0">
          <div className="text-left">
            <DialogTitle className="text-2xl font-semibold tracking-tight text-slate-900">
              {title}
            </DialogTitle>
            <div className="mt-1.5 flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
              <DialogDescription asChild>
                <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-700 text-xs leading-none">
                  SKU: {sku}
                </span>
              </DialogDescription>
              <Badge variant="secondary" className={`h-7 shrink-0 px-3 text-xs font-normal border-none ${rowStatus.badgeClass}`}>
                {rowStatus.label}
              </Badge>
            </div>
          </div>
        </DialogHeader>

        <div className="px-6 py-4">
          {isDetailError && (
            <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              Không tải được chi tiết từ server. Đang hiển thị thông tin từ danh sách (có thể thiếu các lô liên quan).
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <DetailItem label="Mã Barcode" value={barcode} icon={Tag} />
            <DetailItem label="Vị trí mặc định" value={`${warehouseCode} - ${shelfCode}`} icon={MapPin} />
            <DetailItem label="Tài chính (VND)" value={`${formatCurrency(costPrice)} /đv`} icon={DollarSign} />
            <DetailItem label="Cảnh báo định mức" value={`Định mức: ${minQuantity}`} icon={ShieldCheck} />
          </div>

          <div className="mt-4 p-4 bg-slate-900 rounded-xl flex flex-col md:flex-row md:items-center justify-between text-white shadow-lg gap-4 md:gap-0">
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-slate-800 rounded-lg">
                <Box size={24} className="text-slate-300" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium whitespace-nowrap">
                  {d ? "Tổng số lượng (dòng đang chọn + lô liên quan còn hàng)" : "Tồn dòng đang chọn"}
                </p>
                <div className="text-2xl font-bold tracking-tight flex items-baseline gap-1.5">
                  {isDetailPending && !d ? (
                    <Loader2 className="h-7 w-7 animate-spin text-slate-400" aria-label="Đang tải" />
                  ) : (
                    <>
                      {totalQuantity} <span className="text-sm font-normal text-slate-500">{unit}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <Separator orientation="vertical" className="h-10 bg-slate-800 hidden md:block" />
            <div className="md:text-right">
              <p className="text-xs text-slate-400 font-medium whitespace-nowrap">Giá trị tồn kho (dòng đang chọn)</p>
              <p className="text-xl font-semibold text-green-400">{formatCurrency(totalValue)}</p>
            </div>
          </div>

          <div className="mt-8">
            <div className="flex items-center justify-between mb-4 px-1 gap-2">
              <h3 className="text-base font-semibold text-slate-900">Phân bổ chi tiết lô hàng</h3>
              {isDetailPending && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                  Đang tải lô liên quan…
                </span>
              )}
            </div>

            <div className="border border-slate-200 rounded-xl overflow-x-auto shadow-sm bg-white relative">
              <Table>
                <TableHeader className="bg-slate-50/80">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="min-w-[120px]">Số lô</TableHead>
                    <TableHead className="min-w-[120px] text-center px-4">Vị trí</TableHead>
                    <TableHead className="min-w-[120px] text-center px-4">Hạn SD</TableHead>
                    <TableHead className="min-w-[80px] text-right font-semibold">Số lượng</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!d && isDetailPending ? (
                    <TableRow>
                      <TableCell colSpan={4} className="py-8 text-center text-slate-500 text-sm">
                        <Loader2 className="inline h-5 w-5 animate-spin mr-2 align-middle" aria-hidden />
                        Đang tải chi tiết…
                      </TableCell>
                    </TableRow>
                  ) : (
                    lotRows.map((batch) => (
                      <TableRow key={batch.id} className="hover:bg-slate-50/50 transition-colors">
                        <TableCell className="font-medium text-slate-700 py-3">{batch.batchNumber}</TableCell>
                        <TableCell className="text-center px-4">
                          <Badge variant="outline" className="font-mono text-slate-600 bg-white shadow-xs border-slate-200">
                            {batch.warehouseCode}-{batch.shelfCode}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center px-4">
                          <span className={isExpiringSoon(batch.expiryDate) ? "text-amber-600 font-semibold" : "text-slate-600"}>
                            {batch.expiryDate ? new Date(batch.expiryDate).toLocaleDateString("vi-VN") : "-"}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-bold text-slate-900 py-3">{batch.quantity}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
        <div className="p-4 bg-slate-50 border-t border-slate-200 text-[11px] text-slate-400 text-center italic">
          Các chỉ số dựa trên dữ liệu cập nhật lần cuối: {new Date(updatedAt).toLocaleString("vi-VN")}
        </div>
      </DialogContent>
    </Dialog>
  )
}
