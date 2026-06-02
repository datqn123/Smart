import { useEffect } from "react"
import { useParams } from "react-router-dom"
import { AlertTriangle, CheckCircle2, FileText, ShieldAlert } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore } from "@/features/auth/store/useAuthStore"
import {
  canSeeRuntimeFolder,
  canSeeRuntimePage,
  findRuntimeCustomPage,
} from "@/features/custom-builder/runtime/customMenuRuntime"

export function CustomRuntimePage() {
  const { pageKey } = useParams()
  const { setTitle } = usePageTitle()
  const menuPermissions = useAuthStore((state) => state.menuPermissions)
  const role = useAuthStore((state) => state.user?.role ?? null)
  const result = pageKey ? findRuntimeCustomPage(pageKey) : null

  useEffect(() => {
    setTitle(result?.page.label ?? "Giao diện tùy chỉnh")
  }, [result?.page.label, setTitle])

  if (!result) {
    return (
      <div className="flex min-h-full items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
          <AlertTriangle className="mx-auto h-10 w-10 text-slate-400" />
          <h1 className="mt-4 text-lg font-semibold text-slate-950">Không tìm thấy giao diện tùy chỉnh</h1>
          <p className="mt-2 text-sm text-slate-500">Route này chưa được publish hoặc đã bị ngừng hiển thị.</p>
        </div>
      </div>
    )
  }

  const { folder, page } = result
  const folderVisible = canSeeRuntimeFolder(folder, menuPermissions, role)
  const pageVisible = canSeeRuntimePage(page, menuPermissions, role)

  if (!folderVisible || !pageVisible) {
    return (
      <div className="flex min-h-full items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md rounded-lg border border-slate-200 bg-white p-6 text-center shadow-sm">
          <ShieldAlert className="mx-auto h-10 w-10 text-slate-400" />
          <h1 className="mt-4 text-lg font-semibold text-slate-950">Bạn không có quyền mở giao diện này</h1>
          <p className="mt-2 text-sm text-slate-500">
            Hệ thống đã ẩn metadata chi tiết cho tới khi quyền menu, entity và dữ liệu được xác nhận.
          </p>
        </div>
      </div>
    )
  }

  const warnings = page.validationSummary.warnings

  return (
    <div className="h-full overflow-y-auto bg-slate-50/40 p-4 md:p-6 lg:p-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold text-slate-950">{page.label}</h1>
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">
                Published v{page.publishedVersion}
              </Badge>
              {page.hasDraft && <Badge variant="secondary">Có bản nháp v{page.draftVersion}</Badge>}
            </div>
            <p className="mt-1 max-w-3xl text-sm text-slate-500">{page.description}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
            <div>Danh mục: <span className="font-semibold text-slate-900">{folder.label}</span></div>
            <div>ETag: <span className="font-mono text-xs">{page.etag}</span></div>
          </div>
        </div>

        {warnings.length > 0 && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
              <div>
                <p className="text-sm font-semibold text-amber-800">Cảnh báo runtime preview</p>
                <ul className="mt-1 space-y-1 text-sm text-amber-700">
                  {warnings.map((warning) => (
                    <li key={`${warning.section}-${warning.message}`}>{warning.message}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-slate-500" />
              <h2 className="text-sm font-semibold text-slate-900">Runtime page resolver</h2>
            </div>
            <Badge variant="outline">{page.pageType}</Badge>
          </div>
          <div className="grid gap-4 p-4 md:grid-cols-3">
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase text-slate-500">Entity</p>
              <p className="mt-2 font-mono text-sm text-slate-900">{page.entityKey}</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase text-slate-500">Route</p>
              <p className="mt-2 font-mono text-sm text-slate-900">{page.routePath}</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase text-slate-500">Permission</p>
              <p className="mt-2 text-sm text-slate-900">Menu + entity + data đã pass ở frontend preview.</p>
            </div>
          </div>
          <div className="border-t border-slate-200 p-4">
            <div className="flex min-h-[260px] flex-col items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-center">
              <CheckCircle2 className="h-10 w-10 text-slate-400" />
              <h3 className="mt-3 text-base font-semibold text-slate-900">Trang runtime đang ở chế độ preview</h3>
              <p className="mt-1 max-w-lg text-sm text-slate-500">
                Backend sẽ thay phần này bằng table/form record theo entity, view và workflow published version.
              </p>
              <Button type="button" variant="outline" className="mt-4">
                Tạo record mẫu
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
