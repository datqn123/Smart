import { useEffect, useMemo, useState } from "react"
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, RotateCcw, Save } from "lucide-react"
import { usePageTitle } from "@/context/PageTitleContext"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import {
  getDefaultTableColumnSettings,
  getTableColumnSettings,
  saveTableColumnSettings,
  type TableColumnConfig,
  type TableColumnSetting,
  type TableKey,
} from "@/lib/table-column-settings"

function cloneSettings(items: TableColumnSetting[]) {
  return items.map((table) => ({
    ...table,
    columns: table.columns.map((column) => ({ ...column })),
  }))
}

function serializeSettings(items: TableColumnSetting[]) {
  return JSON.stringify(
    items.map((table) => ({
      tableKey: table.tableKey,
      columns: [...table.columns]
        .sort((a, b) => a.order - b.order)
        .map((column) => ({
          key: column.key,
          visible: column.visible || column.required,
          order: column.order,
        })),
    })),
  )
}

function orderedColumns(columns: TableColumnConfig[]) {
  return [...columns].sort((a, b) => a.order - b.order)
}

function reindex(columns: TableColumnConfig[]) {
  return columns.map((column, index) => ({ ...column, order: index }))
}

function updateTable(
  items: TableColumnSetting[],
  tableKey: TableKey,
  updater: (table: TableColumnSetting) => TableColumnSetting,
) {
  return items.map((table) => (table.tableKey === tableKey ? updater(table) : table))
}

function ColumnListItem({
  column,
  selected,
  onSelect,
}: {
  column: TableColumnConfig
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex min-h-11 w-full items-center justify-between gap-3 rounded-md border px-3 py-2 text-left text-sm transition-colors",
        selected
          ? "border-slate-500 bg-slate-100 text-slate-950"
          : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
      )}
    >
      <span className="min-w-0 truncate font-medium">{column.label}</span>
      {column.required && <Badge variant="secondary" className="shrink-0">Bắt buộc</Badge>}
    </button>
  )
}

export function InterfaceSettingsPage() {
  const { setTitle } = usePageTitle()
  const [sourceSettings, setSourceSettings] = useState<TableColumnSetting[]>([])
  const [draftSettings, setDraftSettings] = useState<TableColumnSetting[]>([])
  const [selectedTableKey, setSelectedTableKey] = useState<TableKey>("inventory_stock")
  const [selectedVisibleKey, setSelectedVisibleKey] = useState<string | null>(null)
  const [selectedHiddenKey, setSelectedHiddenKey] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const defaultSettings = useMemo(() => getDefaultTableColumnSettings(), [])

  useEffect(() => {
    setTitle("Cấu hình giao diện")
    const load = async () => {
      const settings = await getTableColumnSettings()
      setSourceSettings(cloneSettings(settings))
      setDraftSettings(cloneSettings(settings))
      setSelectedTableKey(settings[0]?.tableKey ?? "inventory_stock")
    }
    void load()
  }, [setTitle])

  const selectedTable = draftSettings.find((table) => table.tableKey === selectedTableKey)
  const visibleColumns = selectedTable ? orderedColumns(selectedTable.columns.filter((column) => column.visible || column.required)) : []
  const hiddenColumns = selectedTable ? orderedColumns(selectedTable.columns.filter((column) => !column.visible && !column.required)) : []
  const selectedVisibleColumn = visibleColumns.find((column) => column.key === selectedVisibleKey)
  const selectedVisibleIndex = visibleColumns.findIndex((column) => column.key === selectedVisibleKey)
  const hasUnsavedChanges = serializeSettings(sourceSettings) !== serializeSettings(draftSettings)

  const changeTable = (tableKey: TableKey) => {
    setSelectedTableKey(tableKey)
    setSelectedVisibleKey(null)
    setSelectedHiddenKey(null)
  }

  const hideSelectedColumn = () => {
    if (!selectedVisibleKey || selectedVisibleColumn?.required) {
      return
    }
    setDraftSettings((prev) =>
      updateTable(prev, selectedTableKey, (table) => {
        const next = orderedColumns(table.columns).map((column) =>
          column.key === selectedVisibleKey ? { ...column, visible: false } : column,
        )
        const visible = next.filter((column) => column.visible || column.required)
        const hidden = next.filter((column) => !column.visible && !column.required)
        return { ...table, columns: reindex([...visible, ...hidden]) }
      }),
    )
    setSelectedVisibleKey(null)
    setSelectedHiddenKey(selectedVisibleKey)
  }

  const showSelectedColumn = () => {
    if (!selectedHiddenKey) {
      return
    }
    setDraftSettings((prev) =>
      updateTable(prev, selectedTableKey, (table) => {
        const current = orderedColumns(table.columns)
        const target = current.find((column) => column.key === selectedHiddenKey)
        if (!target) {
          return table
        }
        const visible = current.filter((column) => column.visible || column.required)
        const hidden = current.filter((column) => !column.visible && !column.required && column.key !== selectedHiddenKey)
        return {
          ...table,
          columns: reindex([...visible, { ...target, visible: true }, ...hidden]),
        }
      }),
    )
    setSelectedVisibleKey(selectedHiddenKey)
    setSelectedHiddenKey(null)
  }

  const moveSelectedVisibleColumn = (direction: -1 | 1) => {
    if (selectedVisibleIndex < 0) {
      return
    }
    const targetIndex = selectedVisibleIndex + direction
    if (targetIndex < 0 || targetIndex >= visibleColumns.length) {
      return
    }
    setDraftSettings((prev) =>
      updateTable(prev, selectedTableKey, (table) => {
        const current = orderedColumns(table.columns)
        const visible = current.filter((column) => column.visible || column.required)
        const hidden = current.filter((column) => !column.visible && !column.required)
        const nextVisible = [...visible]
        const tmp = nextVisible[selectedVisibleIndex]
        nextVisible[selectedVisibleIndex] = nextVisible[targetIndex]
        nextVisible[targetIndex] = tmp
        return { ...table, columns: reindex([...nextVisible, ...hidden]) }
      }),
    )
  }

  const resetSelectedTable = () => {
    const defaultTable = defaultSettings.find((table) => table.tableKey === selectedTableKey)
    if (!defaultTable) {
      return
    }
    setDraftSettings((prev) =>
      updateTable(prev, selectedTableKey, () => ({
        ...defaultTable,
        columns: defaultTable.columns.map((column) => ({ ...column })),
      })),
    )
    setSelectedVisibleKey(null)
    setSelectedHiddenKey(null)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await saveTableColumnSettings({
        items: draftSettings.map((table) => {
          const columns = orderedColumns(table.columns)
          return {
            tableKey: table.tableKey,
            hiddenColumns: columns
              .filter((column) => !column.required && !column.visible)
              .map((column) => column.key),
            columnOrder: columns.map((column) => column.key),
          }
        }),
      })
      const reloaded = await getTableColumnSettings()
      setSourceSettings(cloneSettings(reloaded))
      setDraftSettings(cloneSettings(reloaded))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto bg-slate-50/30 p-4 md:p-6 lg:p-8">
      <div className="mx-auto flex min-h-full max-w-6xl flex-col gap-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Cấu hình giao diện</h1>
            <p className="mt-1 text-sm text-slate-500">
              Tùy chỉnh cột hiển thị và thứ tự cột trong bảng dữ liệu Kho hàng.
            </p>
          </div>
          <div className="w-full md:w-[320px]">
            <label className="mb-1.5 block text-sm font-semibold text-slate-700">Bảng dữ liệu</label>
            <Select value={selectedTableKey} onValueChange={(value) => changeTable(value as TableKey)}>
              <SelectTrigger className="h-11 w-full bg-white">
                <SelectValue placeholder="Chọn bảng dữ liệu" />
              </SelectTrigger>
              <SelectContent>
                {draftSettings.map((table) => (
                  <SelectItem key={table.tableKey} value={table.tableKey}>
                    {table.tableLabel}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid flex-1 gap-3 lg:grid-cols-[1fr_72px_1fr]">
          <section className="flex min-h-[360px] flex-col rounded-lg border border-slate-200 bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-900">Đang hiển thị</h2>
              <span className="text-sm text-slate-500">{visibleColumns.length} cột</span>
            </div>
            <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-2">
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9"
                onClick={() => moveSelectedVisibleColumn(-1)}
                disabled={selectedVisibleIndex <= 0}
                title="Di chuyển lên"
              >
                <ChevronUp className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9"
                onClick={() => moveSelectedVisibleColumn(1)}
                disabled={selectedVisibleIndex < 0 || selectedVisibleIndex >= visibleColumns.length - 1}
                title="Di chuyển xuống"
              >
                <ChevronDown className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto p-3">
              {visibleColumns.map((column) => (
                <ColumnListItem
                  key={column.key}
                  column={column}
                  selected={selectedVisibleKey === column.key}
                  onSelect={() => {
                    setSelectedVisibleKey(column.key)
                    setSelectedHiddenKey(null)
                  }}
                />
              ))}
            </div>
          </section>

          <div className="flex items-center justify-center gap-2 lg:flex-col">
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-11 w-11"
              onClick={hideSelectedColumn}
              disabled={!selectedVisibleColumn || selectedVisibleColumn.required}
              title="Ẩn cột"
            >
              <ChevronRight className="hidden h-4 w-4 lg:block" />
              <ChevronDown className="h-4 w-4 lg:hidden" />
            </Button>
            <Button
              type="button"
              variant="outline"
              size="icon"
              className="h-11 w-11"
              onClick={showSelectedColumn}
              disabled={!selectedHiddenKey}
              title="Hiện cột"
            >
              <ChevronLeft className="hidden h-4 w-4 lg:block" />
              <ChevronUp className="h-4 w-4 lg:hidden" />
            </Button>
          </div>

          <section className="flex min-h-[360px] flex-col rounded-lg border border-slate-200 bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-slate-900">Đang ẩn</h2>
              <span className="text-sm text-slate-500">{hiddenColumns.length} cột</span>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto p-3">
              {hiddenColumns.length === 0 ? (
                <div className="flex h-full min-h-40 items-center justify-center rounded-md border border-dashed border-slate-200 text-sm text-slate-500">
                  Chưa có cột nào bị ẩn
                </div>
              ) : hiddenColumns.map((column) => (
                <ColumnListItem
                  key={column.key}
                  column={column}
                  selected={selectedHiddenKey === column.key}
                  onSelect={() => {
                    setSelectedHiddenKey(column.key)
                    setSelectedVisibleKey(null)
                  }}
                />
              ))}
            </div>
          </section>
        </div>

        <div className="sticky bottom-0 flex flex-col gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <span className="text-sm text-slate-600">
            {hasUnsavedChanges ? "Có thay đổi chưa lưu" : "Không có thay đổi chưa lưu"}
          </span>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={resetSelectedTable}>
              <RotateCcw className="mr-2 h-4 w-4" /> Khôi phục mặc định
            </Button>
            <Button
              type="button"
              onClick={handleSave}
              disabled={!hasUnsavedChanges || saving}
              className="bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-900 disabled:text-white"
            >
              <Save className="mr-2 h-4 w-4" /> {saving ? "Đang lưu..." : "Lưu thay đổi"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
