import { useCallback, useMemo, useState } from "react"
import {
  CheckCircle2,
  Loader2,
  Plus,
  Save,
  Table2,
  Trash2,
  Upload,
  X,
} from "lucide-react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  CATEGORY_TABLE_COL,
  CUSTOMER_TABLE_COL,
  DATA_TABLE_SCROLL_CLASS,
  DATA_TABLE_SHELL_CLASS,
  PRODUCT_TABLE_COL,
  SUPPLIER_TABLE_COL,
  TABLE_HEAD_CLASS,
} from "@/lib/data-table-layout"
import { cn } from "@/lib/utils"
import type {
  CatalogDraftColumn,
  CatalogDraftRow,
  CatalogDraftTablePayload,
} from "../api/aiCatalogDraftApi"
import {
  commitCatalogDraft,
  deleteCatalogDraft,
  patchCatalogDraft,
} from "../api/aiCatalogDraftApi"
import { AiChatArtifactSummary } from "./AiChatArtifactSummary"

type Props = {
  initial: CatalogDraftTablePayload
  onDismiss?: () => void
}

const ENTITY_LABEL: Record<string, string> = {
  product: "Sản phẩm",
  category: "Danh mục",
  supplier: "Nhà cung cấp",
  customer: "Khách hàng",
}

const COL_WIDTH: Record<string, string> = {
  skuCode: PRODUCT_TABLE_COL.skuCode,
  name: PRODUCT_TABLE_COL.productName,
  categoryName: CATEGORY_TABLE_COL.categoryName,
  categoryCode: CATEGORY_TABLE_COL.categoryCode,
  parentName: "w-[160px] min-w-0",
  parentCategory: "w-[160px] min-w-0",
  description: CATEGORY_TABLE_COL.description,
  sortOrder: "w-[88px]",
  status: CATEGORY_TABLE_COL.status,
  supplierCode: SUPPLIER_TABLE_COL.code,
  customerCode: CUSTOMER_TABLE_COL.code,
  phone: CUSTOMER_TABLE_COL.phone,
  email: CUSTOMER_TABLE_COL.email,
  address: SUPPLIER_TABLE_COL.address,
  costPrice: PRODUCT_TABLE_COL.price,
  salePrice: PRODUCT_TABLE_COL.price,
  baseUnitName: "w-[88px]",
  contactPerson: "w-[120px] min-w-0",
  barcode: "w-[108px]",
  taxCode: "w-[100px]",
}

const INPUT_CLASS =
  "h-9 w-full min-w-0 border-slate-200 bg-white px-2 text-sm shadow-none focus-visible:border-slate-900 focus-visible:ring-0"

const SHEET_CONTENT_CLASS =
  "w-full sm:max-w-[min(96vw,1100px)] p-0 flex flex-col gap-0 overflow-hidden"

function cellValue(row: CatalogDraftRow, key: string): string {
  const v = row.values[key]
  if (v == null) return ""
  return String(v)
}

function visibleColumns(cols: CatalogDraftColumn[]): CatalogDraftColumn[] {
  const seen = new Set<string>()
  const out: CatalogDraftColumn[] = []
  for (const c of cols) {
    if (!c.key || seen.has(c.key)) continue
    seen.add(c.key)
    out.push(c)
  }
  return out
}

function previewFromRows(
  rows: CatalogDraftRow[],
  columns: CatalogDraftColumn[]
): string {
  if (rows.length === 0) return "Chưa có dòng dữ liệu."
  const first = rows[0]
  const parts = columns
    .slice(0, 3)
    .map((c) => {
      const v = cellValue(first, c.key)
      if (!v.trim()) return null
      return `${c.label ?? c.key}: ${v}`
    })
    .filter(Boolean)
  const more = rows.length > 1 ? ` (+${rows.length - 1} dòng khác)` : ""
  return (parts.length ? parts.join(" · ") : "Dòng 1") + more
}

type EditorProps = {
  entityType: string
  columns: CatalogDraftColumn[]
  rows: CatalogDraftRow[]
  pendingCount: number
  committedCount: number
  saving: boolean
  committing: boolean
  expanded?: boolean
  onAddRow: () => void
  onSaveDraft: () => void
  onCommit: () => void
  onCancel: () => void
  onRemoveRow: (rowId: string) => void
  onUpdateCell: (rowId: string, key: string, raw: string) => void
}

function CatalogDraftTableEditor({
  entityType,
  columns,
  rows,
  pendingCount,
  committedCount,
  saving,
  committing,
  expanded = false,
  onAddRow,
  onSaveDraft,
  onCommit,
  onCancel,
  onRemoveRow,
  onUpdateCell,
}: EditorProps) {
  const useWideTable = expanded || columns.length > 5
  const tableMinWidth = useWideTable ? "min-w-[880px]" : "min-w-[520px]"

  return (
    <div className={cn(DATA_TABLE_SHELL_CLASS, "w-full max-w-none shadow-sm h-full flex flex-col")}>
      <div className="flex flex-col gap-3 border-b border-slate-200/80 bg-slate-50/90 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Table2 className="h-4 w-4 shrink-0 text-blue-600" aria-hidden />
            <h3 className="text-sm font-semibold text-slate-900">
              Bảng nháp — {ENTITY_LABEL[entityType] ?? entityType}
            </h3>
            <Badge variant="secondary" className="font-normal text-slate-600">
              {rows.length} dòng
            </Badge>
            {committedCount > 0 ? (
              <Badge className="bg-emerald-100 font-normal text-emerald-800 hover:bg-emerald-100">
                {committedCount} đã ghi
              </Badge>
            ) : null}
          </div>
          <p className="text-xs text-slate-500">
            Chỉnh sửa trực tiếp trên bảng, sau đó lưu nháp hoặc xác nhận ghi vào cơ sở dữ liệu.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <Button type="button" variant="outline" size="sm" className="bg-white" onClick={onAddRow}>
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
            disabled={saving || committing || pendingCount === 0}
            className="bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
            onClick={onCommit}
          >
            {committing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Xác nhận ghi DB
            {pendingCount > 0 ? ` (${pendingCount})` : ""}
          </Button>
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

      <div
        className={cn(
          DATA_TABLE_SCROLL_CLASS,
          "overflow-x-auto",
          expanded ? "max-h-[calc(100dvh-11rem)] flex-1" : "max-h-[min(360px,55vh)]"
        )}
      >
        <Table
          className={cn(
            "w-full border-separate border-spacing-0",
            tableMinWidth,
            useWideTable ? "table-auto" : "table-fixed"
          )}
        >
          <TableHeader className="sticky top-0 z-10">
            <TableRow className="hover:bg-transparent">
              <TableHead className={cn(TABLE_HEAD_CLASS, "w-10 text-center")}>#</TableHead>
              {columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={cn(
                    TABLE_HEAD_CLASS,
                    "whitespace-nowrap",
                    COL_WIDTH[col.key] ?? "min-w-[120px]",
                    col.type === "number" ? "text-right" : "text-left"
                  )}
                >
                  {col.label ?? col.key}
                  {col.required ? (
                    <span className="text-red-500" aria-hidden>
                      {" "}
                      *
                    </span>
                  ) : null}
                </TableHead>
              ))}
              <TableHead className={cn(TABLE_HEAD_CLASS, "w-12 text-center")} />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length + 2}
                  className="py-10 text-center text-sm text-slate-500"
                >
                  Chưa có dòng — bấm &quot;Thêm dòng&quot; hoặc gửi lại yêu cầu cho AI.
                </TableCell>
              </TableRow>
            ) : (
              rows.map((row, index) => {
                const done = Boolean(row.committedAt)
                const err = Boolean(row.lastError)
                return (
                  <TableRow
                    key={row.rowId}
                    className={cn(
                      "group",
                      done && "bg-emerald-50/60",
                      err && !done && "bg-red-50/50",
                      !done && !err && "hover:bg-slate-50/80"
                    )}
                  >
                    <TableCell className="py-3 text-center text-xs font-medium text-slate-400">
                      {done ? (
                        <CheckCircle2
                          className="mx-auto h-4 w-4 text-emerald-600"
                          aria-label="Đã ghi"
                        />
                      ) : (
                        index + 1
                      )}
                    </TableCell>
                    {columns.map((col) => (
                      <TableCell
                        key={col.key}
                        className={cn(
                          "py-3 px-2 align-middle",
                          col.type === "number" && "text-right"
                        )}
                      >
                        {col.type === "enum" && col.options?.length ? (
                          <select
                            className={cn(INPUT_CLASS, "cursor-pointer")}
                            value={cellValue(row, col.key) || col.options[0]}
                            disabled={done}
                            onChange={(e) => onUpdateCell(row.rowId, col.key, e.target.value)}
                          >
                            {col.options.map((opt) => (
                              <option key={opt} value={opt}>
                                {opt}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <Input
                            className={INPUT_CLASS}
                            inputMode={col.type === "number" ? "decimal" : "text"}
                            value={cellValue(row, col.key)}
                            disabled={done}
                            onChange={(e) => onUpdateCell(row.rowId, col.key, e.target.value)}
                          />
                        )}
                      </TableCell>
                    ))}
                    <TableCell className="py-3 text-center">
                      {!done ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          className="text-slate-400 hover:text-red-600"
                          title="Xóa dòng"
                          onClick={() => onRemoveRow(row.rowId)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      ) : null}
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      {rows.some((r) => r.lastError) ? (
        <div className="border-t border-red-200 bg-red-50 px-4 py-3 text-xs text-red-800 space-y-1">
          <p className="font-semibold">Lỗi khi ghi một số dòng:</p>
          {rows
            .filter((r) => r.lastError)
            .map((r) => (
              <p key={r.rowId}>
                Dòng {r.rowId}: {r.lastError}
              </p>
            ))}
        </div>
      ) : null}
    </div>
  )
}

export function AiChatDraftTableCard({ initial, onDismiss }: Props) {
  const [sheetOpen, setSheetOpen] = useState(false)
  const [draftId] = useState(initial.draftId)
  const [entityType] = useState(initial.entityType)
  const [columns] = useState<CatalogDraftColumn[]>(() =>
    visibleColumns(initial.columns ?? [])
  )
  const [rows, setRows] = useState<CatalogDraftRow[]>(
    () => initial.rows?.map((r) => ({ ...r, values: { ...r.values } })) ?? []
  )
  const [saving, setSaving] = useState(false)
  const [committing, setCommitting] = useState(false)

  const pendingCount = useMemo(
    () => rows.filter((r) => !r.committedAt).length,
    [rows]
  )
  const committedCount = rows.length - pendingCount
  const entityLabel = ENTITY_LABEL[entityType] ?? entityType

  const updateCell = useCallback(
    (rowId: string, key: string, raw: string) => {
      setRows((prev) =>
        prev.map((r) => {
          if (r.rowId !== rowId) return r
          const col = columns.find((c) => c.key === key)
          let next: unknown = raw
          if (col?.type === "number" && raw.trim() !== "") {
            const n = Number(raw.replace(/,/g, ""))
            next = Number.isFinite(n) ? n : raw
          }
          return { ...r, values: { ...r.values, [key]: next } }
        })
      )
    },
    [columns]
  )

  const addRow = () => {
    const n = rows.length + 1
    const values: Record<string, unknown> = {}
    for (const c of columns) {
      if (c.type === "enum" && c.options?.length) values[c.key] = c.options[0]
      else values[c.key] = ""
    }
    setRows((prev) => [...prev, { rowId: `r${n}`, values }])
  }

  const removeRow = (rowId: string) => {
    setRows((prev) => prev.filter((r) => r.rowId !== rowId))
  }

  const handleSaveDraft = async () => {
    setSaving(true)
    try {
      await patchCatalogDraft(draftId, rows, columns)
      toast.success("Đã lưu nháp")
    } catch (e: unknown) {
      toast.error((e as Error)?.message ?? "Không lưu được nháp")
    } finally {
      setSaving(false)
    }
  }

  const handleCommit = async () => {
    setCommitting(true)
    try {
      await patchCatalogDraft(draftId, rows, columns)
      const data = await commitCatalogDraft(draftId)
      if (data?.draft?.rows) {
        setRows(data.draft.rows.map((r) => ({ ...r, values: { ...r.values } })))
      }
      if (data && data.failedCount === 0) {
        toast.success(`Đã ghi ${data.committedCount} dòng vào hệ thống`)
      } else if (data) {
        toast.warning(
          `Ghi thành công ${data.committedCount}, lỗi ${data.failedCount} dòng — xem lỗi trong bảng`
        )
      }
    } catch (e: unknown) {
      toast.error((e as Error)?.message ?? "Commit thất bại")
    } finally {
      setCommitting(false)
    }
  }

  const handleCancel = async () => {
    try {
      await deleteCatalogDraft(draftId)
      toast.info("Đã hủy nháp")
    } catch {
      /* ignore */
    }
    setSheetOpen(false)
    onDismiss?.()
  }

  const editorProps: EditorProps = {
    entityType,
    columns,
    rows,
    pendingCount,
    committedCount,
    saving,
    committing,
    onAddRow: addRow,
    onSaveDraft: () => void handleSaveDraft(),
    onCommit: () => void handleCommit(),
    onCancel: () => void handleCancel(),
    onRemoveRow: removeRow,
    onUpdateCell: updateCell,
  }

  return (
    <>
      <AiChatArtifactSummary
        icon={<Table2 className="h-4 w-4" />}
        title={`Bảng nháp — ${entityLabel}`}
        description="Chỉnh sửa trong panel rộng, sau đó lưu nháp hoặc ghi DB."
        openLabel="Mở bảng nháp"
        onOpen={() => setSheetOpen(true)}
        badges={
          <>
            <Badge variant="secondary" className="font-normal text-slate-600">
              {rows.length} dòng
            </Badge>
            {pendingCount > 0 ? (
              <Badge variant="outline" className="font-normal text-amber-800 border-amber-200">
                {pendingCount} chờ ghi
              </Badge>
            ) : null}
            {committedCount > 0 ? (
              <Badge className="bg-emerald-100 font-normal text-emerald-800 hover:bg-emerald-100">
                {committedCount} đã ghi
              </Badge>
            ) : null}
          </>
        }
        preview={previewFromRows(rows, columns)}
      />

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className={SHEET_CONTENT_CLASS} showCloseButton>
          <SheetHeader className="sr-only">
            <SheetTitle>Bảng nháp {entityLabel}</SheetTitle>
            <SheetDescription>Chỉnh sửa và xác nhận ghi dữ liệu</SheetDescription>
          </SheetHeader>
          <CatalogDraftTableEditor {...editorProps} expanded />
        </SheetContent>
      </Sheet>
    </>
  )
}
