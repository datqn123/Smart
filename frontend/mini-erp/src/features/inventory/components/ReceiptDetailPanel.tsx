import React from "react"
import { 
  Sheet, 
  SheetContent, 
  SheetHeader, 
  SheetTitle,
  SheetDescription 
} from "@/components/ui/sheet"
import { formatCurrency, formatDate } from "../utils"
import type { StockReceipt } from "../types"
import { StatusBadge } from "./StatusBadge"
import { Package, Calendar, User, Building2, Hash, FileText, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

interface ReceiptDetailPanelProps {
  receipt: StockReceipt | null;
  isOpen: boolean;
  onClose: () => void;
  canApprove?: boolean;
}

export function ReceiptDetailPanel({ receipt, isOpen, onClose, canApprove = false }: ReceiptDetailPanelProps) {
  if (!receipt) return null;

  const handleApprove = () => alert(`Đã phê duyệt phiếu ${receipt.receiptCode} (Dữ liệu mock)`);
  const handleReject = () => alert(`Đã từ chối phiếu ${receipt.receiptCode} (Dữ liệu mock)`);

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="sm:max-w-[560px] overflow-y-auto p-6">
        <SheetHeader className="pb-4">
          <div className="flex items-center justify-between mb-2">
            <StatusBadge status={receipt.status} />
            <span className="text-xs text-slate-400">ID: {receipt.id}</span>
          </div>
          <SheetTitle className="text-xl font-mono">Phiếu nhập: {receipt.receiptCode}</SheetTitle>
          <SheetDescription>
            Tạo lúc {formatDate(receipt.createdAt)} bởi {receipt.staffName}
          </SheetDescription>
        </SheetHeader>

        <Separator className="my-4" />

        {receipt.status === "Rejected" ? (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50/70 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-red-100 text-red-700">
                <XCircle className="h-4 w-4" aria-hidden />
              </div>
              <div className="min-w-0 flex-1 text-sm">
                <p className="text-xs font-semibold uppercase tracking-wide text-red-800">Phiếu đã bị từ chối</p>
                <p className="mt-1 font-medium text-slate-900">Lý do từ chối</p>
                <p className="mt-1 whitespace-pre-wrap text-slate-800">
                  {receipt.rejectionReason?.trim() ? receipt.rejectionReason.trim() : "Không ghi nhận lý do cụ thể."}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="mb-6 flex items-center gap-2">
            {(["Draft", "Pending", "Approved"] as const).map((step, i, arr) => {
              const statusOrder = ["Draft", "Pending", "Approved", "Rejected"]
              const currentIdx = statusOrder.indexOf(receipt.status)
              const stepIdx = statusOrder.indexOf(step)
              const isCompleted = receipt.status === "Approved" && stepIdx <= 2
              const isCurrent = step === receipt.status
              const isPast = stepIdx < currentIdx && receipt.status !== "Approved"
              return (
                <div key={step} className="flex items-center">
                  <div className={`px-2.5 py-1 rounded text-[10px] sm:text-xs font-medium
                    ${isCompleted || isPast ? "bg-green-50 text-green-700" : ""}
                    ${isCurrent && receipt.status !== "Approved" && receipt.status !== "Rejected" ? "bg-slate-100 text-slate-800" : ""}
                    ${isCurrent && receipt.status === "Rejected" ? "bg-red-50 text-red-700" : ""}
                    ${!isCompleted && !isCurrent && !isPast ? "bg-slate-50 text-slate-400" : ""}
                  `}>
                    {isCompleted || isPast ? "✓" : isCurrent ? "●" : "○"}{" "}
                    {step === "Draft" ? "Nháp" : step === "Pending" ? "Chờ duyệt" : "Đã duyệt"}
                  </div>
                  {i < arr.length - 1 && (
                    <div className={`w-3 sm:w-5 h-0.5 mx-1 ${isCompleted ? "bg-green-300" : "bg-slate-200"}`} />
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm mb-8">
          <DetailItem icon={<Building2 />} label="Nhà cung cấp" value={receipt.supplierName} />
          <DetailItem icon={<Calendar />} label="Ngày nhập" value={formatDate(receipt.receiptDate)} />
          <DetailItem icon={<User />} label="Người tạo" value={receipt.staffName} />
          <DetailItem icon={<Hash />} label="Số hóa đơn" value={receipt.invoiceNumber || "—"} />
          <DetailItem icon={<FileText />} label="Ghi chú" value={receipt.notes || "Không có ghi chú"} className="col-span-2" />
          <div className="bg-slate-50 p-3 rounded-lg col-span-2 mt-2">
            <p className="text-xs text-slate-500 mb-1">Tổng tiền thanh toán</p>
            <p className="text-lg font-bold text-slate-900">{formatCurrency(receipt.totalAmount)}</p>
          </div>
        </div>

        {/* Products Table */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-tight flex items-center gap-2">
            <Package className="h-4 w-4" /> Danh sách hàng hóa ({receipt.details.length})
          </h3>
          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="text-left py-2 px-3 font-medium">Sản phẩm</th>
                  <th className="text-right py-2 px-3 font-medium">SL</th>
                  <th className="text-right py-2 px-3 font-medium">Thành tiền</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {receipt.details.map((detail) => (
                  <tr key={detail.id} className="hover:bg-slate-50/30">
                    <td className="py-2.5 px-3">
                      <p className="font-medium text-slate-900">{detail.productName}</p>
                      <p className="text-xs text-slate-500">{detail.skuCode} · {detail.unitName}</p>
                    </td>
                    <td className="text-right py-2.5 px-3 text-slate-600">
                      {detail.quantity} <span className="text-[10px]">{detail.unitName}</span>
                    </td>
                    <td className="text-right py-2.5 px-3 font-medium text-slate-900">
                      {formatCurrency(detail.lineTotal)}
                    </td>
                  </tr>
                ))}
                {receipt.details.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-8 text-center text-slate-400 italic">Không có dữ liệu mặt hàng</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Approval Info */}
        {receipt.approvedByName && (
          <div className="mt-8 bg-green-50 border border-green-100 rounded-lg p-3 text-xs flex gap-3">
            <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 shrink-0">
              <User className="h-4 w-4" />
            </div>
            <div>
              <p className="font-medium text-green-800">Người duyệt: {receipt.approvedByName}</p>
              {receipt.approvedAt && <p className="text-green-600 mt-0.5">Duyệt lúc {formatDate(receipt.approvedAt)}</p>}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {canApprove && receipt.status === "Pending" && (
          <div className="mt-10 flex gap-3 sticky bottom-0 bg-white pt-4 border-t">
            <Button 
              className="flex-1 bg-green-600 hover:bg-green-700 h-12" 
              onClick={handleApprove}
              data-testid="approve-btn"
            >
              Phê duyệt
            </Button>
            <Button 
              variant="outline" 
              className="flex-1 border-red-200 text-red-600 hover:bg-red-50 h-12" 
              onClick={handleReject}
              data-testid="reject-btn"
            >
              Từ chối
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function DetailItem({ icon, label, value, className }: { icon: React.ReactNode, label: string, value: string, className?: string }) {
  return (
    <div className={className}>
      <p className="text-[10px] text-slate-500 mb-1 flex items-center gap-1 uppercase tracking-wider font-semibold">
        {React.isValidElement(icon) && React.cloneElement(icon as React.ReactElement, { className: "h-3 w-3" })} {label}
      </p>
      <p className="font-medium text-slate-900 leading-tight">{value}</p>
    </div>
  );
}
