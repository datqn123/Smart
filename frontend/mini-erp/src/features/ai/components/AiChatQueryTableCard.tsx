import { useCallback, useMemo, useState } from "react"
import { Copy, RotateCcw, Table2 } from "lucide-react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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
import type { QueryTableColumn, QueryTablePayload } from "../api/aiQueryTableTypes"
import { AiChatArtifactSummary } from "./AiChatArtifactSummary"

type Props = {
  payload: QueryTablePayload
}

const PREVIEW_ROWS = 4

const INPUT_CLASS =
  "h-9 w-full min-w-[88px] border-slate-200 bg-white px-2 text-sm shadow-none focus-visible:border-slate-900 focus-visible:ring-0"

function cloneRows(rows: QueryTablePayload["rows"]): QueryTablePayload["rows"] {
  return rows.map((r) => ({ ...r }))
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return ""
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

function displayCell(value: unknown): string {
  const s = formatCell(value)
  return s === "" ? "—" : s
}

function isReadOnlyColumn(key: string): boolean {
  const k = key.toLowerCase()
  return k === "id" || k.endsWith("_id")
}

function rowsToCsv(columns: QueryTableColumn[], rows: QueryTablePayload["rows"]): string {
  const keys = columns.map((c) => c.key)
  const header = keys.map((k) => columns.find((c) => c.key === k)?.label ?? k)
  const escape = (v: string) => {
    if (/[",\n]/.test(v)) return `"${v.replace(/"/g, '""')}"`
    return v
  }
  const lines = [
    header.map(escape).join(","),
    ...rows.map((row) => keys.map((k) => escape(formatCell(row[k]))).join(",")),
  ]
  return lines.join("\n")
}

type TableProps = {
  columns: QueryTableColumn[]
  colKeys: string[]
  rows: QueryTablePayload["rows"]
  compact?: boolean
  editable?: boolean
  onCellChange?: (rowIndex: number, key: string, value: string) => void
}

function QueryResultTable({
  columns,
  colKeys,
  rows,
  compact,
  editable,
  onCellChange,
}: TableProps) {
  return (
    <div className={cn(DATA_TABLE_SCROLL_CLASS, "overflow-x-auto", compact && "max-h-[200px]")}>
      <Table
        className={cn(
          "w-full text-sm border-separate border-spacing-0",
          editable ? "min-w-[720px] table-auto" : compact ? "min-w-[480px]" : "min-w-[640px]"
        )}
      >
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {columns.map((col) => (
              <TableHead key={col.key} className={cn(TABLE_HEAD_CLASS, "whitespace-nowrap")}>
                {col.label ?? col.key}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={Math.max(colKeys.length, 1)}
                className="py-8 text-center text-slate-500"
              >
                Không có dữ liệu
              </TableCell>
            </TableRow>
          ) : (
            rows.map((row, idx) => (
              <TableRow key={idx} className="hover:bg-slate-50/80">
                {colKeys.map((key) => {
                  const col = columns.find((c) => c.key === key)
                  const readOnly = !editable || isReadOnlyColumn(key)
                  const raw = formatCell(row[key])
                  return (
                    <TableCell
                      key={key}
                      className={cn(
                        "align-top py-2 px-2",
                        !editable && (compact ? "max-w-[180px] truncate" : "max-w-[280px] truncate")
                      )}
                    >
                      {readOnly ? (
                        <span
                          className={cn(
                            "block text-sm",
                            isReadOnlyColumn(key) ? "text-slate-500 tabular-nums" : "text-slate-800"
                          )}
                          title={displayCell(row[key])}
                        >
                          {displayCell(row[key])}
                        </span>
                      ) : (
                        <Input
                          className={INPUT_CLASS}
                          value={raw}
                          inputMode={col?.type === "number" ? "decimal" : "text"}
                          onChange={(e) => onCellChange?.(idx, key, e.target.value)}
                        />
                      )}
                    </TableCell>
                  )
                })}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}

export function AiChatQueryTableCard({ payload }: Props) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editedRows, setEditedRows] = useState(() => cloneRows(payload.rows))
  const [dirty, setDirty] = useState(false)

  const { columns, rowCount, truncated, title } = payload
  const colKeys = useMemo(() => columns.map((c) => c.key), [columns])
  const previewRows = editedRows.slice(0, PREVIEW_ROWS)
  const previewHint =
    editedRows.length > PREVIEW_ROWS
      ? `Hiển thị ${PREVIEW_ROWS}/${editedRows.length} dòng trong xem trước — mở bảng để chỉnh sửa.`
      : "Mở bảng đầy đủ để chỉnh sửa các ô (trừ cột ID)."

  const updateCell = useCallback((rowIndex: number, key: string, value: string) => {
    setEditedRows((prev) =>
      prev.map((row, i) => (i === rowIndex ? { ...row, [key]: value } : row))
    )
    setDirty(true)
  }, [])

  const resetRows = useCallback(() => {
    setEditedRows(cloneRows(payload.rows))
    setDirty(false)
    toast.info("Đã khôi phục dữ liệu gốc từ truy vấn")
  }, [payload.rows])

  const copyCsv = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(rowsToCsv(columns, editedRows))
      toast.success("Đã sao chép bảng (CSV) vào clipboard")
    } catch {
      toast.error("Không sao chép được — thử lại hoặc dùng trình duyệt khác")
    }
  }, [columns, editedRows])

  const openDialog = () => {
    if (!dirty) {
      setEditedRows(cloneRows(payload.rows))
    }
    setDialogOpen(true)
  }

  return (
    <>
      <AiChatArtifactSummary
        icon={<Table2 className="h-4 w-4" />}
        title={title ?? "Kết quả truy vấn"}
        description={previewHint}
        openLabel="Chỉnh sửa bảng"
        onOpen={openDialog}
        badges={
          <>
            <Badge variant="secondary" className="font-mono text-xs">
              {rowCount} dòng
            </Badge>
            {dirty ? (
              <Badge variant="outline" className="text-xs text-blue-700 border-blue-200">
                Đã chỉnh sửa
              </Badge>
            ) : null}
            {truncated ? (
              <Badge variant="outline" className="text-xs text-amber-700 border-amber-200">
                Tối đa {payload.maxDisplayRows} dòng
              </Badge>
            ) : null}
          </>
        }
        preview={
          previewRows.length > 0 ? (
            <div className={cn(DATA_TABLE_SHELL_CLASS, "border border-slate-100 shadow-none")}>
              <QueryResultTable
                columns={columns}
                colKeys={colKeys}
                rows={previewRows}
                compact
              />
            </div>
          ) : (
            "Không có dữ liệu."
          )
        }
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent
          showCloseButton={false}
          className="flex max-h-[min(90dvh,900px)] w-full max-w-[min(96vw,1100px)] flex-col gap-0 overflow-hidden p-0 sm:max-w-[min(96vw,1100px)]"
        >
          <DialogHeader className="border-b border-slate-100 px-5 py-4 text-left space-y-2">
            <DialogTitle className="text-base">{title ?? "Kết quả truy vấn"}</DialogTitle>
            <p className="text-xs text-slate-500 leading-relaxed">
              Chỉnh sửa trực tiếp trên bảng. Thay đổi chỉ lưu trên phiên chat — không ghi vào cơ sở
              dữ liệu. Cột ID / mã tham chiếu (…_id) chỉ xem. Dùng sao chép CSV để mang sang Excel.
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="font-mono text-xs">
                {rowCount} dòng
              </Badge>
              {dirty ? (
                <Badge variant="outline" className="text-xs text-blue-700 border-blue-200">
                  Đã chỉnh sửa
                </Badge>
              ) : null}
              {truncated ? (
                <Badge variant="outline" className="text-xs text-amber-700 border-amber-200">
                  Hiển thị tối đa {payload.maxDisplayRows} dòng
                </Badge>
              ) : null}
            </div>
          </DialogHeader>
          <div
            className={cn(
              DATA_TABLE_SHELL_CLASS,
              "flex-1 min-h-0 border-0 shadow-none rounded-none max-h-[calc(90dvh-11rem)]"
            )}
          >
            <QueryResultTable
              columns={columns}
              colKeys={colKeys}
              rows={editedRows}
              editable
              onCellChange={updateCell}
            />
          </div>
          <DialogFooter className="shrink-0 flex-row flex-nowrap items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/90 px-5 py-3.5 sm:flex-row sm:justify-between">
            <Button type="button" variant="outline" size="sm" disabled={!dirty} onClick={resetRows}>
              <RotateCcw className="h-4 w-4" />
              Khôi phục gốc
            </Button>
            <div className="flex shrink-0 flex-row items-center gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => void copyCsv()}>
                <Copy className="h-4 w-4" />
                Sao chép CSV
              </Button>
              <Button
                type="button"
                size="sm"
                className="bg-slate-900 text-white hover:bg-slate-800"
                onClick={() => setDialogOpen(false)}
              >
                Đóng
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
