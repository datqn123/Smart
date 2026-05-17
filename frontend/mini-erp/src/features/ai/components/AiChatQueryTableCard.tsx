import { useMemo } from "react"
import { Table2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
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
import type { QueryTablePayload } from "../api/aiQueryTableTypes"

type Props = {
  payload: QueryTablePayload
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—"
  if (typeof value === "object") return JSON.stringify(value)
  return String(value)
}

export function AiChatQueryTableCard({ payload }: Props) {
  const { columns, rows, rowCount, truncated, title } = payload

  const colKeys = useMemo(
    () => columns.map((c) => c.key),
    [columns],
  )

  return (
    <div
      className={`${DATA_TABLE_SHELL_CLASS} border border-slate-200 bg-white shadow-sm`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <Table2 className="h-4 w-4 text-slate-500" />
          <span className="text-sm font-semibold text-slate-800">
            {title ?? "Kết quả truy vấn"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="font-mono text-xs">
            {rowCount} dòng
          </Badge>
          {truncated ? (
            <Badge variant="outline" className="text-xs text-amber-700 border-amber-200">
              Hiển thị tối đa {payload.maxDisplayRows} dòng
            </Badge>
          ) : null}
        </div>
      </div>
      <div className={DATA_TABLE_SCROLL_CLASS}>
        <Table className="min-w-full text-sm">
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {columns.map((col) => (
                <TableHead key={col.key} className={TABLE_HEAD_CLASS}>
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
                  {colKeys.map((key) => (
                    <TableCell key={key} className="max-w-[240px] truncate align-top">
                      {formatCell(row[key])}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
