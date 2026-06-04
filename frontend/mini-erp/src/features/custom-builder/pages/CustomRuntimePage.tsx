import { useEffect, useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Edit,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import {
  getMockRuntimePageBundle,
  permissionCanOpenPage,
  type BuilderPageBundle,
  type RuntimeRecord,
} from "@/features/custom-builder/api/customBuilderMockAdapter"

function StateMessage({
  icon,
  title,
  message,
}: {
  icon: React.ReactNode
  title: string
  message: string
}) {
  return (
    <div className="flex min-h-full items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md rounded-md border border-slate-200 bg-white p-6 text-center shadow-sm">
        <div className="mx-auto flex h-10 w-10 items-center justify-center text-slate-400">{icon}</div>
        <h1 className="mt-4 text-lg font-semibold text-slate-950">{title}</h1>
        <p className="mt-2 text-sm text-slate-500">{message}</p>
      </div>
    </div>
  )
}

function formatValue(value: string | number | undefined) {
  if (value == null || value === "") return "-"
  return String(value)
}

const pageTypeLabels: Record<BuilderPageBundle["menuPage"]["pageType"], string> = {
  record_list: "Danh sách bản ghi",
  form: "Biểu mẫu",
  table_detail: "Bảng kèm chi tiết",
}

export function CustomRuntimePage() {
  const { pageKey, recordId } = useParams()
  const { setTitle } = usePageTitle()
  const menuPermissions = useAuthStore((state) => state.menuPermissions)
  const role = useAuthStore((state) => state.user?.role ?? null)
  const [bundle, setBundle] = useState<BuilderPageBundle | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState("")
  const [selectedId, setSelectedId] = useState<string | null>(recordId ?? null)
  const [mode, setMode] = useState<"detail" | "create" | "edit">("detail")
  const [draftValues, setDraftValues] = useState<Record<string, string | number>>({})

  const loadBundle = async () => {
    setLoading(true)
    setError(null)
    try {
      const next = pageKey ? await getMockRuntimePageBundle(pageKey) : null
      setBundle(next)
      if (!next) {
        setError("Route này chưa được publish hoặc không có trong fixture.")
      }
    } catch {
      setError("Không tải được metadata runtime.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadBundle()
  }, [pageKey])

  useEffect(() => {
    setTitle(bundle?.menuPage.label ?? "Giao diện tùy chỉnh")
  }, [bundle?.menuPage.label, setTitle])

  useEffect(() => {
    if (recordId) {
      setSelectedId(recordId)
      setMode("detail")
    }
  }, [recordId])

  const records = useMemo(() => {
    const clean = query.trim().toLowerCase()
    const source = bundle?.sampleRecords ?? []
    if (!clean) return source
    return source.filter((record) =>
      Object.values(record.values).some((value) => String(value).toLowerCase().includes(clean)),
    )
  }, [bundle?.sampleRecords, query])

  const selectedRecord = useMemo<RuntimeRecord | null>(() => {
    if (!bundle) return null
    return bundle.sampleRecords.find((record) => record.id === selectedId) ?? records[0] ?? null
  }, [bundle, records, selectedId])

  useEffect(() => {
    if (!selectedId && records[0]) {
      setSelectedId(records[0].id)
    }
  }, [records, selectedId])

  useEffect(() => {
    if (mode === "create") {
      setDraftValues({})
      return
    }
    setDraftValues(selectedRecord?.values ?? {})
  }, [mode, selectedRecord])

  if (loading) {
    return (
      <StateMessage
        icon={<Loader2 className="h-10 w-10 animate-spin" />}
        title="Đang tải cấu hình giao diện"
        message="Frontend đang đọc định nghĩa trang và bản ghi mẫu qua mock adapter."
      />
    )
  }

  if (!bundle || error) {
    return (
      <StateMessage
        icon={<AlertTriangle className="h-10 w-10" />}
        title="Không tìm thấy giao diện tùy chỉnh"
        message={error ?? "Route này chưa được publish hoặc đã bị ngừng hiển thị."}
      />
    )
  }

  if (!permissionCanOpenPage(bundle.menuPage, menuPermissions, role)) {
    return (
      <StateMessage
        icon={<ShieldAlert className="h-10 w-10" />}
        title="Bạn không có quyền mở giao diện này"
        message="Frontend ẩn metadata chi tiết; backend vẫn là lớp enforce quyền khi API thật được nối."
      />
    )
  }

  const listColumns = bundle.views.listColumns
  const warnings = [...bundle.menuPage.validationSummary.warnings, ...bundle.validationSummary.warnings]
  const canMutate = bundle.permissions.create.includes(role ?? "Owner") || role == null

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-4 md:p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <header className="flex flex-col gap-4 rounded-md border border-slate-200 bg-white p-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold text-slate-950">{bundle.menuPage.label}</h1>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">
                Đã publish v{bundle.menuPage.publishedVersion}
              </Badge>
              <Badge variant="secondary">{pageTypeLabels[bundle.menuPage.pageType]}</Badge>
              {bundle.menuPage.hasDraft && <Badge variant="outline">Có draft v{bundle.menuPage.draftVersion}</Badge>}
            </div>
            <p className="mt-1 max-w-3xl text-sm text-slate-500">{bundle.menuPage.description}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => void loadBundle()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Tải lại
            </Button>
            <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" disabled={!canMutate} onClick={() => setMode("create")}>
              <Plus className="mr-2 h-4 w-4" />
              Tạo bản ghi
            </Button>
          </div>
        </header>

        {warnings.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <div>
                <p className="text-sm font-semibold text-amber-800">Cảnh báo runtime</p>
                <ul className="mt-1 space-y-1 text-sm text-amber-700">
                  {warnings.map((warning) => (
                    <li key={`${warning.section}-${warning.message}`}>{warning.message}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="rounded-md border border-slate-200 bg-white">
            <div className="flex flex-col gap-3 border-b border-slate-200 p-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-500" />
                <h2 className="text-sm font-semibold text-slate-900">Danh sách bản ghi</h2>
                <Badge variant="outline">Trang 1 / 1</Badge>
              </div>
              <div className="relative w-full lg:w-80">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input className="pl-9" placeholder="Tìm bản ghi..." value={query} onChange={(event) => setQuery(event.target.value)} />
              </div>
            </div>
            {records.length === 0 ? (
              <div className="flex min-h-[360px] flex-col items-center justify-center p-8 text-center">
                <FileText className="h-10 w-10 text-slate-400" />
                <h3 className="mt-3 text-base font-semibold text-slate-900">Chưa có bản ghi</h3>
                <p className="mt-1 text-sm text-slate-500">Giao diện vẫn ổn định khi fixture trả mảng rỗng.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-[760px] w-full text-sm">
                  <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                    <tr>
                      {listColumns.map((column) => (
                        <th key={column.fieldKey} className="px-4 py-3" style={{ width: column.width }}>
                          {column.label}
                        </th>
                      ))}
                      <th className="px-4 py-3">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {records.map((record) => (
                      <tr
                        key={record.id}
                        className={selectedRecord?.id === record.id ? "bg-slate-50" : "hover:bg-slate-50"}
                      >
                        {listColumns.map((column) => (
                          <td key={column.fieldKey} className="px-4 py-3">
                            <button
                              type="button"
                              className="text-left text-slate-900"
                              onClick={() => {
                                setSelectedId(record.id)
                                setMode("detail")
                              }}
                            >
                              {formatValue(record.values[column.fieldKey])}
                            </button>
                          </td>
                        ))}
                        <td className="px-4 py-3">
                          <Badge variant="outline">{record.state}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <aside className="rounded-md border border-slate-200 bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 p-4">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  {mode === "create" ? "Tạo bản ghi" : mode === "edit" ? "Chỉnh sửa bản ghi" : "Chi tiết bản ghi"}
                </h2>
                <p className="mt-1 text-xs text-slate-500">Render theo metadata field/view từ fixture frontend.</p>
              </div>
              {mode === "detail" && selectedRecord && (
                <Button type="button" size="icon" variant="outline" onClick={() => setMode("edit")} disabled={!canMutate} title="Sửa">
                  <Edit className="h-4 w-4" />
                </Button>
              )}
            </div>
            <div className="space-y-4 p-4">
              {bundle.fields.filter((field) => field.status !== "Archived").map((field) => (
                <div key={field.id}>
                  <Label>
                    {field.label}
                    {field.required ? " *" : ""}
                  </Label>
                  <Input
                    className="mt-1.5"
                    readOnly={mode === "detail"}
                    value={mode === "detail" ? formatValue(selectedRecord?.values[field.fieldKey]) : draftValues[field.fieldKey] ?? ""}
                    placeholder={field.type === "reference" ? "{refType, refEntityKey, refId, labelSnapshot}" : field.fieldKey}
                    onChange={(event) => setDraftValues((current) => ({ ...current, [field.fieldKey]: event.target.value }))}
                  />
                  {field.type === "reference" && (
                    <p className="mt-1 text-xs text-slate-500">
                      {field.refType}:{field.refEntityKey}
                    </p>
                  )}
                </div>
              ))}
              <div className="flex gap-2 border-t border-slate-200 pt-4">
                <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" disabled={mode === "detail" || !canMutate}>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Lưu bản nháp
                </Button>
                {mode !== "detail" && (
                  <Button type="button" variant="outline" onClick={() => setMode("detail")}>
                    Hủy
                  </Button>
                )}
              </div>
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-slate-500" />
                  <h3 className="text-sm font-semibold text-slate-900">Timeline / audit</h3>
                </div>
                <div className="mt-3 space-y-2">
                  {(selectedRecord?.audit.length ? selectedRecord.audit : [{ at: "03/06/2026", actor: "Fixture", action: "Chưa có audit" }]).map((item) => (
                    <div key={`${item.at}-${item.action}`} className="rounded-md border border-slate-200 bg-white p-2 text-xs text-slate-600">
                      <span className="font-semibold text-slate-900">{item.at}</span> - {item.actor}: {item.action}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
