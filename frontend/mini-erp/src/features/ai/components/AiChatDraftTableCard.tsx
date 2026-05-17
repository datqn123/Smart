import { useCallback, useState } from "react"
import { Loader2, Save, Table2, Trash2, Upload } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
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

type Props = {
  initial: CatalogDraftTablePayload
  onDismiss?: () => void
}

function cellValue(row: CatalogDraftRow, key: string): string {
  const v = row.values[key]
  if (v == null) return ""
  return String(v)
}

const ENTITY_LABEL: Record<string, string> = {
  product: "sản phẩm",
  category: "danh mục",
  supplier: "nhà cung cấp",
  customer: "khách hàng",
}

export function AiChatDraftTableCard({ initial, onDismiss }: Props) {
  const [draftId] = useState(initial.draftId)
  const [entityType] = useState(initial.entityType)
  const [columns] = useState<CatalogDraftColumn[]>(initial.columns ?? [])
  const [rows, setRows] = useState<CatalogDraftRow[]>(
    () => initial.rows?.map((r) => ({ ...r, values: { ...r.values } })) ?? []
  )
  const [saving, setSaving] = useState(false)
  const [committing, setCommitting] = useState(false)

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
      const err = e as Error
      toast.error(err?.message ?? "Không lưu được nháp")
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
          `Ghi thành công ${data.committedCount}, lỗi ${data.failedCount} dòng — xem lỗi dưới bảng`
        )
      }
    } catch (e: unknown) {
      const err = e as Error
      toast.error(err?.message ?? "Commit thất bại")
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
    onDismiss?.()
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden w-full max-w-[min(100%,920px)]">
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50/80">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <Table2 className="h-4 w-4 text-blue-600" />
          Bảng nháp — {ENTITY_LABEL[entityType] ?? entityType}
          {initial.previewMessage ? (
            <span className="text-slate-500 font-normal">({initial.previewMessage})</span>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={addRow}>
            Thêm dòng
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={saving || committing}
            onClick={() => void handleSaveDraft()}
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            <span className="ml-1">Lưu nháp</span>
          </Button>
          <Button
            type="button"
            size="sm"
            disabled={saving || committing}
            onClick={() => void handleCommit()}
          >
            {committing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            <span className="ml-1">Xác nhận ghi DB</span>
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={() => void handleCancel()}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div className="overflow-x-auto max-h-[min(420px,50vh)]">
        <Table className="table-fixed min-w-[640px]">
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col.key} className="text-xs font-bold text-slate-600">
                  {col.label ?? col.key}
                  {col.required ? " *" : ""}
                </TableHead>
              ))}
              <TableHead className="w-10" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow
                key={row.rowId}
                className={
                  row.committedAt ? "bg-emerald-50/50" : row.lastError ? "bg-red-50/40" : undefined
                }
              >
                {columns.map((col) => (
                  <TableCell key={col.key} className="py-2 px-2 align-middle">
                    {col.type === "enum" && col.options?.length ? (
                      <select
                        className="w-full h-9 rounded-md border border-slate-200 bg-white px-2 text-sm"
                        value={cellValue(row, col.key) || col.options[0]}
                        disabled={Boolean(row.committedAt)}
                        onChange={(e) => updateCell(row.rowId, col.key, e.target.value)}
                      >
                        {col.options.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <Input
                        className="h-9 border-slate-200 focus-visible:border-black focus-visible:ring-0"
                        value={cellValue(row, col.key)}
                        disabled={Boolean(row.committedAt)}
                        onChange={(e) => updateCell(row.rowId, col.key, e.target.value)}
                      />
                    )}
                  </TableCell>
                ))}
                <TableCell className="py-2">
                  {!row.committedAt ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => removeRow(row.rowId)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-slate-400" />
                    </Button>
                  ) : null}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {rows.some((r) => r.lastError) ? (
        <div className="px-4 py-2 text-xs text-red-600 border-t border-red-100 bg-red-50/50 space-y-0.5">
          {rows
            .filter((r) => r.lastError)
            .map((r) => (
              <div key={r.rowId}>
                {r.rowId}: {r.lastError}
              </div>
            ))}
        </div>
      ) : null}
    </div>
  )
}
