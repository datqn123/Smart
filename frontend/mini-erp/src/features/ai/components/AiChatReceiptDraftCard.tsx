import { memo, useCallback, useMemo, useState } from "react"
import { CheckCircle2, Loader2, Package, Plus, Save, Trash2, Upload, X } from "lucide-react"
import { toast } from "sonner"
import { Link } from "react-router-dom"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DATA_TABLE_SCROLL_CLASS,
  DATA_TABLE_SHELL_CLASS,
  TABLE_HEAD_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type {
  InventoryDraftColumn,
  InventoryDraftLine,
  InventoryReceiptDraftPayload,
  ReceiptDraftHeader,
} from "../api/aiInventoryDraftApi"
import {
  commitInventoryDraft,
  deleteInventoryDraft,
  patchInventoryDraft,
} from "../api/aiInventoryDraftApi"
import { AiChatArtifactSummary } from "./AiChatArtifactSummary"

type Props = {
  initial: InventoryReceiptDraftPayload
  onDismiss?: () => void
}

const INPUT_CLASS =
  "h-9 w-full min-w-0 border-slate-200 bg-white px-2 text-sm shadow-none focus-visible:border-slate-900 focus-visible:ring-0"

const SHEET_CONTENT_CLASS =
  "w-full sm:max-w-[min(96vw,900px)] p-0 flex flex-col gap-0 overflow-hidden"

function lineCell(line: InventoryDraftLine, key: string): string {
  const v = line.values[key]
  if (v == null) return ""
  return String(v)
}

type EditorProps = {
  lineColumns: InventoryDraftColumn[]
  header: ReceiptDraftHeader
  lines: InventoryDraftLine[]
  totalQty: number
  saving: boolean
  committing: boolean
  committed: boolean
  receiptCode: string | null
  expanded?: boolean
  onAddLine: () => void
  onSaveDraft: () => void
  onCommit: () => void
  onCancel: () => void
  onRemoveLine: (lineId: string) => void
  onUpdateHeader: (key: keyof ReceiptDraftHeader, value: string) => void
  onUpdateLineCell: (lineId: string, key: string, raw: string) => void
}

function InventoryReceiptDraftEditor({
  lineColumns,
  header,
  lines,
  totalQty,
  saving,
  committing,
  committed,
  receiptCode,
  expanded = false,
  onAddLine,
  onSaveDraft,
  onCommit,
  onCancel,
  onRemoveLine,
  onUpdateHeader,
  onUpdateLineCell,
}: EditorProps) {
  return (
    <div className={cn(DATA_TABLE_SHELL_CLASS, "w-full max-w-none shadow-sm h-full flex flex-col")}>
      <div className="flex flex-col gap-3 border-b border-slate-200/80 bg-slate-50/90 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Package className="h-4 w-4 shrink-0 text-blue-600" aria-hidden />
            <h3 className="text-sm font-semibold text-slate-900">Phiếu nhập kho — nháp</h3>
            <Badge variant="secondary" className="font-normal text-slate-600">
              {lines.length} dòng · SL ~{totalQty}
            </Badge>
            {committed && receiptCode ? (
              <Badge className="bg-emerald-100 font-normal text-emerald-800 hover:bg-emerald-100">
                {receiptCode}
              </Badge>
            ) : null}
          </div>
          <p className="text-xs text-slate-500">
            Chỉnh header và dòng hàng → Lưu nháp → Tạo phiếu (Draft/Pending). Duyệt tại màn Nhập kho.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {!committed ? (
            <>
              <Button type="button" variant="outline" size="sm" className="bg-white" onClick={onAddLine}>
                <Plus className="h-4 w-4" />
                Thêm dòng
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="bg-white"
                disabled={saving || committing}
                onClick={onSaveDraft}
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Lưu nháp
              </Button>
              <Button
                type="button"
                size="sm"
                disabled={saving || committing || lines.length === 0}
                className="bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
                onClick={onCommit}
              >
                {committing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4" />
                )}
                Xác nhận tạo phiếu
              </Button>
            </>
          ) : (
            <Button type="button" variant="outline" size="sm" className="bg-white" asChild>
              <Link to="/inventory/inbound">Mở màn Nhập kho</Link>
            </Button>
          )}
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="text-slate-500"
            title="Hủy nháp"
            onClick={onCancel}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-3 border-b border-slate-100 px-4 py-3 sm:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-1">
          <Label className="text-xs text-slate-500">Nhà cung cấp *</Label>
          <Input
            className={INPUT_CLASS}
            value={header.supplierName ?? ""}
            disabled={committed}
            onChange={(e) => onUpdateHeader("supplierName", e.target.value)}
            placeholder="Tên NCC"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-slate-500">Mã NCC</Label>
          <Input
            className={INPUT_CLASS}
            value={header.supplierCode ?? ""}
            disabled={committed}
            onChange={(e) => onUpdateHeader("supplierCode", e.target.value)}
            placeholder="Mã (tuỳ chọn)"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-slate-500">Ngày nhập *</Label>
          <Input
            type="date"
            className={INPUT_CLASS}
            value={header.receiptDate ?? ""}
            disabled={committed}
            onChange={(e) => onUpdateHeader("receiptDate", e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-slate-500">Số HĐ</Label>
          <Input
            className={INPUT_CLASS}
            value={header.invoiceNumber ?? ""}
            disabled={committed}
            onChange={(e) => onUpdateHeader("invoiceNumber", e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-slate-500">Trạng thái lưu</Label>
          <Select
            value={header.saveMode ?? "draft"}
            disabled={committed}
            onValueChange={(v) => onUpdateHeader("saveMode", v)}
          >
            <SelectTrigger className={INPUT_CLASS}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="draft">Nháp (Draft)</SelectItem>
              <SelectItem value="pending">Gửi duyệt (Pending)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1 sm:col-span-2 lg:col-span-1">
          <Label className="text-xs text-slate-500">Ghi chú</Label>
          <Input
            className={INPUT_CLASS}
            value={header.notes ?? ""}
            disabled={committed}
            onChange={(e) => onUpdateHeader("notes", e.target.value)}
          />
        </div>
      </div>

      <div
        className={cn(
          DATA_TABLE_SCROLL_CLASS,
          "overflow-x-auto",
          expanded ? "max-h-[calc(100dvh-18rem)] flex-1" : "max-h-[min(320px,50vh)]"
        )}
      >
        <Table className="w-full min-w-[640px] table-auto border-separate border-spacing-0">
          <TableHeader className="sticky top-0 z-10 bg-white">
            <TableRow className="hover:bg-transparent">
              <TableHead className={cn(TABLE_HEAD_CLASS, "w-10 whitespace-nowrap")}>#</TableHead>
              {lineColumns.map((col) => (
                <TableHead key={col.key} className={cn(TABLE_HEAD_CLASS, "whitespace-nowrap")}>
                  {col.label ?? col.key}
                  {col.required ? " *" : ""}
                </TableHead>
              ))}
              {!committed ? <TableHead className="w-10" /> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {lines.map((ln, idx) => (
              <TableRow key={ln.lineId}>
                <TableCell className="text-center text-xs text-slate-400">{idx + 1}</TableCell>
                {lineColumns.map((col) => (
                  <TableCell key={col.key} className="py-2 px-2">
                    {committed ? (
                      <span className="text-sm">{lineCell(ln, col.key)}</span>
                    ) : (
                      <Input
                        className={INPUT_CLASS}
                        value={lineCell(ln, col.key)}
                        type={col.type === "number" ? "number" : "text"}
                        onChange={(e) => onUpdateLineCell(ln.lineId, col.key, e.target.value)}
                      />
                    )}
                  </TableCell>
                ))}
                {!committed ? (
                  <TableCell>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => onRemoveLine(ln.lineId)}
                    >
                      <Trash2 className="h-4 w-4 text-slate-400" />
                    </Button>
                  </TableCell>
                ) : null}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {committed ? (
        <div className="flex items-center gap-2 border-t border-slate-100 px-4 py-2 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4" />
          Phiếu đã tạo{receiptCode ? `: ${receiptCode}` : ""}. Vào Nhập kho để duyệt và chọn vị trí nhập.
        </div>
      ) : null}
    </div>
  )
}

export const AiChatReceiptDraftCard = memo(function AiChatReceiptDraftCard({ initial, onDismiss }: Props) {
  const [sheetOpen, setSheetOpen] = useState(false)
  const [draftId] = useState(initial.draftId)
  const [lineColumns] = useState<InventoryDraftColumn[]>(() => initial.lineColumns ?? [])
  const [header, setHeader] = useState<ReceiptDraftHeader>(() => ({
    saveMode: "draft",
    receiptDate: new Date().toISOString().slice(0, 10),
    ...initial.header,
  }))
  const [lines, setLines] = useState<InventoryDraftLine[]>(
    () => initial.lines?.map((l) => ({ ...l, values: { ...l.values } })) ?? []
  )
  const [saving, setSaving] = useState(false)
  const [committing, setCommitting] = useState(false)
  const [committed, setCommitted] = useState(false)
  const [receiptCode, setReceiptCode] = useState<string | null>(null)

  const totalQty = useMemo(() => {
    return lines.reduce((sum, ln) => {
      const q = Number(ln.values.quantity)
      return sum + (Number.isFinite(q) ? q : 0)
    }, 0)
  }, [lines])

  const updateHeader = (key: keyof ReceiptDraftHeader, value: string) => {
    setHeader((h) => ({ ...h, [key]: value }))
  }

  const updateLineCell = useCallback(
    (lineId: string, key: string, raw: string) => {
      setLines((prev) =>
        prev.map((ln) => {
          if (ln.lineId !== lineId) return ln
          const col = lineColumns.find((c) => c.key === key)
          let next: unknown = raw
          if (col?.type === "number" && raw.trim() !== "") {
            const n = Number(raw.replace(/,/g, ""))
            next = Number.isFinite(n) ? n : raw
          }
          return { ...ln, values: { ...ln.values, [key]: next } }
        })
      )
    },
    [lineColumns]
  )

  const addLine = () => {
    const n = lines.length + 1
    setLines((prev) => [
      ...prev,
      {
        lineId: `l${n}`,
        values: { skuCode: "", productName: "", quantity: 1, costPrice: 0 },
      },
    ])
  }

  const removeLine = (lineId: string) => {
    setLines((prev) => prev.filter((l) => l.lineId !== lineId))
  }

  const handleSaveDraft = async () => {
    setSaving(true)
    try {
      await patchInventoryDraft(draftId, lines, header, lineColumns)
      toast.success("Đã lưu nháp phiếu nhập")
    } catch (e: unknown) {
      toast.error((e as Error)?.message ?? "Không lưu được nháp")
    } finally {
      setSaving(false)
    }
  }

  const handleCommit = async () => {
    setCommitting(true)
    try {
      await patchInventoryDraft(draftId, lines, header, lineColumns)
      const data = await commitInventoryDraft(draftId)
      if (data?.draft?.lines) {
        setLines(data.draft.lines.map((l) => ({ ...l, values: { ...l.values } })))
      }
      if (data?.success) {
        setCommitted(true)
        setReceiptCode(data.receiptCode ?? null)
        toast.success(data.message ?? "Đã tạo phiếu nhập kho")
      } else {
        toast.error(data?.message ?? "Không tạo được phiếu nhập")
      }
    } catch (e: unknown) {
      toast.error((e as Error)?.message ?? "Commit thất bại")
    } finally {
      setCommitting(false)
    }
  }

  const handleCancel = async () => {
    try {
      await deleteInventoryDraft(draftId)
      toast.info("Đã hủy nháp")
    } catch {
      /* ignore */
    }
    setSheetOpen(false)
    onDismiss?.()
  }

  const preview = [
    header.supplierName ? `NCC: ${header.supplierName}` : null,
    header.receiptDate ? `Ngày: ${header.receiptDate}` : null,
    lines.length > 0
      ? `Dòng 1: ${lineColumns
          .slice(0, 2)
          .map((c) => lineCell(lines[0], c.key))
          .filter(Boolean)
          .join(" · ") || "—"}`
      : null,
  ]
    .filter(Boolean)
    .join(" · ")

  const editorProps: EditorProps = {
    lineColumns,
    header,
    lines,
    totalQty,
    saving,
    committing,
    committed,
    receiptCode,
    onAddLine: addLine,
    onSaveDraft: () => void handleSaveDraft(),
    onCommit: () => void handleCommit(),
    onCancel: () => void handleCancel(),
    onRemoveLine: removeLine,
    onUpdateHeader: updateHeader,
    onUpdateLineCell: updateLineCell,
  }

  return (
    <>
      <AiChatArtifactSummary
        icon={<Package className="h-4 w-4" />}
        title="Phiếu nhập kho — nháp"
        description="Chỉnh header và dòng hàng trong panel rộng."
        openLabel="Mở phiếu nháp"
        onOpen={() => setSheetOpen(true)}
        badges={
          <>
            <Badge variant="secondary" className="font-normal text-slate-600">
              {lines.length} dòng · SL ~{totalQty}
            </Badge>
            {committed && receiptCode ? (
              <Badge className="bg-emerald-100 font-normal text-emerald-800 hover:bg-emerald-100">
                {receiptCode}
              </Badge>
            ) : null}
          </>
        }
        preview={preview || "Chưa có thông tin phiếu."}
      />

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className={SHEET_CONTENT_CLASS} showCloseButton>
          <SheetHeader className="sr-only">
            <SheetTitle>Phiếu nhập kho nháp</SheetTitle>
            <SheetDescription>Chỉnh sửa và tạo phiếu nhập</SheetDescription>
          </SheetHeader>
          <InventoryReceiptDraftEditor {...editorProps} expanded />
        </SheetContent>
      </Sheet>
    </>
  )
})
