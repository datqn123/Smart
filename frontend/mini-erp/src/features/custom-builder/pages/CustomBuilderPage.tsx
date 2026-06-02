import { useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Eye,
  FilePlus,
  FileText,
  Folder,
  FolderPlus,
  Save,
} from "lucide-react"
import { toast } from "sonner"
import { usePageTitle } from "@/context/PageTitleContext"
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
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

type FolderStatus = "Draft" | "Published" | "Hidden"
type PageStatus = "Draft" | "Published" | "NeedsConfig" | "Hidden"
type PageType = "record_list" | "form" | "table_detail"

type CustomMenuPageNode = {
  nodeType: "page"
  id: string
  key: string
  label: string
  icon?: string
  parentKey: string
  routePath: string
  entityKey: string
  pageType: PageType
  status: PageStatus
  sortOrder: number
  description?: string
  permissions: string[]
  version: number
  draftVersion?: number
  publishedVersion?: number
  hasDraft: boolean
  publishedAt?: string
  publishedByName?: string
  etag: string
  updatedAt: string
  updatedByName?: string
}

type CustomMenuFolderNode = {
  nodeType: "folder"
  id: string
  key: string
  label: string
  icon?: string
  description?: string
  status: FolderStatus
  sortOrder: number
  permissions: string[]
  version: number
  draftVersion?: number
  publishedVersion?: number
  hasDraft: boolean
  publishedAt?: string
  publishedByName?: string
  etag: string
  children: CustomMenuPageNode[]
  updatedAt: string
  updatedByName?: string
}

type SelectedRef =
  | { type: "folder"; folderKey: string }
  | { type: "page"; folderKey: string; pageKey: string }

type ValidationErrors = Partial<Record<"label" | "key" | "routePath" | "entityKey", string>>

const STATUS_LABELS: Record<FolderStatus | PageStatus, string> = {
  Draft: "Bản nháp",
  Published: "Đã publish",
  NeedsConfig: "Cần cấu hình",
  Hidden: "Ngừng hiển thị",
}

const PAGE_TYPE_LABELS: Record<PageType, string> = {
  record_list: "Danh sách record",
  form: "Form nhập liệu",
  table_detail: "Bảng + chi tiết",
}

const DEFAULT_PERMISSIONS = ["Owner", "Admin"]

const initialFolders: CustomMenuFolderNode[] = [
  {
    nodeType: "folder",
    id: "folder-quality",
    key: "kiem_hang",
    label: "Kiểm hàng",
    icon: "folder",
    description: "Nhóm giao diện phục vụ kiểm hàng và xử lý sự cố kho.",
    status: "Draft",
    sortOrder: 0,
    permissions: DEFAULT_PERMISSIONS,
    version: 3,
    draftVersion: 4,
    publishedVersion: 3,
    hasDraft: true,
    publishedAt: "03/06/2026",
    publishedByName: "System Administrator",
    etag: "folder-kiem-hang-v3",
    updatedAt: "03/06/2026",
    updatedByName: "System Administrator",
    children: [
      {
        nodeType: "page",
        id: "page-damaged-stock",
        key: "phieu_kiem_hang_hong",
        label: "Phiếu kiểm hàng hỏng",
        icon: "file",
        parentKey: "kiem_hang",
        routePath: "/custom/phieu_kiem_hang_hong",
        entityKey: "damaged_stock_report",
        pageType: "table_detail",
        status: "NeedsConfig",
        sortOrder: 0,
        description: "Ghi nhận sản phẩm hỏng và chuẩn bị quy trình kiểm duyệt.",
        permissions: DEFAULT_PERMISSIONS,
        version: 5,
        draftVersion: 6,
        publishedVersion: 5,
        hasDraft: true,
        publishedAt: "03/06/2026",
        publishedByName: "System Administrator",
        etag: "page-phieu-kiem-hang-hong-v5",
        updatedAt: "03/06/2026",
        updatedByName: "System Administrator",
      },
    ],
  },
]

function slugify(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "d")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
}

function makeUniqueKey(base: string, keys: Set<string>) {
  const clean = slugify(base) || "muc_moi"
  let next = clean
  let index = 2
  while (keys.has(next)) {
    next = `${clean}_${index}`
    index += 1
  }
  return next
}

function orderedFolders(folders: CustomMenuFolderNode[]) {
  return [...folders].sort((a, b) => a.sortOrder - b.sortOrder)
}

function orderedPages(pages: CustomMenuPageNode[]) {
  return [...pages].sort((a, b) => a.sortOrder - b.sortOrder)
}

function reindexFolders(folders: CustomMenuFolderNode[]) {
  return folders.map((folder, index) => ({ ...folder, sortOrder: index }))
}

function reindexPages(pages: CustomMenuPageNode[]) {
  return pages.map((page, index) => ({ ...page, sortOrder: index }))
}

function allKeys(folders: CustomMenuFolderNode[]) {
  const keys = new Set<string>()
  folders.forEach((folder) => {
    keys.add(folder.key)
    folder.children.forEach((page) => keys.add(page.key))
  })
  return keys
}

function getSelectedItem(folders: CustomMenuFolderNode[], selected: SelectedRef) {
  const folder = folders.find((item) => item.key === selected.folderKey)
  if (!folder) {
    return null
  }
  if (selected.type === "folder") {
    return folder
  }
  return folder.children.find((page) => page.key === selected.pageKey) ?? null
}

function statusBadgeClass(status: FolderStatus | PageStatus) {
  if (status === "Published") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700"
  }
  if (status === "NeedsConfig") {
    return "border-slate-300 bg-slate-100 text-slate-700"
  }
  if (status === "Hidden") {
    return "border-slate-200 bg-slate-50 text-slate-500"
  }
  return "border-amber-200 bg-amber-50 text-amber-700"
}

function validateFolder(
  folder: CustomMenuFolderNode,
  folders: CustomMenuFolderNode[],
): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!folder.label.trim()) {
    errors.label = "Tên danh mục không được để trống."
  }
  if (!folder.key.trim()) {
    errors.key = "Mã danh mục không được để trống."
  } else if (!/^[a-z0-9_]+$/.test(folder.key)) {
    errors.key = "Mã chỉ gồm chữ thường, số và dấu gạch dưới."
  } else if (folders.some((item) => item.key === folder.key && item.id !== folder.id)) {
    errors.key = "Mã danh mục đã tồn tại."
  }
  return errors
}

function validatePage(
  page: CustomMenuPageNode,
  folders: CustomMenuFolderNode[],
): ValidationErrors {
  const errors: ValidationErrors = {}
  if (!page.label.trim()) {
    errors.label = "Tên giao diện không được để trống."
  }
  if (!page.key.trim()) {
    errors.key = "Mã giao diện không được để trống."
  } else if (!/^[a-z0-9_]+$/.test(page.key)) {
    errors.key = "Mã chỉ gồm chữ thường, số và dấu gạch dưới."
  } else if (
    folders.some((folder) =>
      folder.children.some((item) => item.key === page.key && item.id !== page.id),
    ) ||
    folders.some((folder) => folder.key === page.key)
  ) {
    errors.key = "Mã giao diện đã tồn tại."
  }
  if (!page.routePath.trim()) {
    errors.routePath = "Route không được để trống."
  }
  if (!page.entityKey.trim()) {
    errors.entityKey = "Entity liên kết không được để trống."
  }
  return errors
}

function FieldError({ message }: { message?: string }) {
  if (!message) {
    return null
  }
  return <p className="mt-1 text-xs font-medium text-red-600">{message}</p>
}

export function CustomBuilderPage() {
  const { setTitle } = usePageTitle()
  const [folders, setFolders] = useState<CustomMenuFolderNode[]>(initialFolders)
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["kiem_hang"]))
  const [selectedRef, setSelectedRef] = useState<SelectedRef>({
    type: "folder",
    folderKey: "kiem_hang",
  })
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(true)

  useEffect(() => {
    setTitle("Trình thiết kế dữ liệu")
  }, [setTitle])

  const selectedItem = getSelectedItem(folders, selectedRef)
  const selectedFolder =
    selectedRef.type === "folder"
      ? folders.find((folder) => folder.key === selectedRef.folderKey) ?? null
      : folders.find((folder) => folder.key === selectedRef.folderKey) ?? null
  const validationErrors = useMemo(() => {
    if (!selectedItem) {
      return {}
    }
    return selectedItem.nodeType === "folder"
      ? validateFolder(selectedItem, folders)
      : validatePage(selectedItem, folders)
  }, [folders, selectedItem])
  const publishWarnings = useMemo(() => {
    if (!selectedItem || selectedItem.nodeType === "folder") {
      return []
    }
    const warnings: string[] = []
    if (!selectedItem.entityKey.trim()) warnings.push("Chưa chọn entity liên kết.")
    if (!selectedItem.routePath.trim()) warnings.push("Chưa có route cho giao diện.")
    if (selectedItem.status === "NeedsConfig") warnings.push("Giao diện vẫn đang ở trạng thái cần cấu hình.")
    return warnings
  }, [selectedItem])

  const setFoldersDirty = (updater: (prev: CustomMenuFolderNode[]) => CustomMenuFolderNode[]) => {
    setFolders((prev) => updater(prev))
    setDirty(true)
  }

  const toggleFolder = (folderKey: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(folderKey)) {
        next.delete(folderKey)
      } else {
        next.add(folderKey)
      }
      return next
    })
  }

  const createFolder = () => {
    const key = makeUniqueKey("danh_muc_moi", allKeys(folders))
    const newFolder: CustomMenuFolderNode = {
      nodeType: "folder",
      id: `folder-${Date.now()}`,
      key,
      label: "Danh mục mới",
      icon: "folder",
      description: "",
      status: "Draft",
      sortOrder: folders.length,
      permissions: DEFAULT_PERMISSIONS,
      version: 1,
      draftVersion: 1,
      publishedVersion: undefined,
      hasDraft: true,
      publishedAt: undefined,
      publishedByName: undefined,
      etag: `folder-${key}-draft-1`,
      updatedAt: "03/06/2026",
      updatedByName: "Bạn",
      children: [],
    }
    setFoldersDirty((prev) => reindexFolders([...orderedFolders(prev), newFolder]))
    setExpanded((prev) => new Set(prev).add(key))
    setSelectedRef({ type: "folder", folderKey: key })
  }

  const createPage = () => {
    const parent = selectedFolder ?? folders[0]
    if (!parent) {
      return
    }
    const key = makeUniqueKey("giao_dien_moi", allKeys(folders))
    const newPage: CustomMenuPageNode = {
      nodeType: "page",
      id: `page-${Date.now()}`,
      key,
      label: "Giao diện mới",
      icon: "file",
      parentKey: parent.key,
      routePath: `/custom/${key}`,
      entityKey: key,
      pageType: "table_detail",
      status: "NeedsConfig",
      sortOrder: parent.children.length,
      description: "",
      permissions: DEFAULT_PERMISSIONS,
      version: 1,
      draftVersion: 1,
      publishedVersion: undefined,
      hasDraft: true,
      publishedAt: undefined,
      publishedByName: undefined,
      etag: `page-${key}-draft-1`,
      updatedAt: "03/06/2026",
      updatedByName: "Bạn",
    }
    setFoldersDirty((prev) =>
      prev.map((folder) =>
        folder.key === parent.key
          ? { ...folder, children: reindexPages([...orderedPages(folder.children), newPage]) }
          : folder,
      ),
    )
    setExpanded((prev) => new Set(prev).add(parent.key))
    setSelectedRef({ type: "page", folderKey: parent.key, pageKey: key })
  }

  const updateSelectedField = (field: string, value: string) => {
    if (!selectedItem) {
      return
    }
    setFoldersDirty((prev) =>
      prev.map((folder) => {
        if (selectedRef.type === "folder" && folder.key === selectedRef.folderKey) {
          if (field === "key") {
            setSelectedRef({ type: "folder", folderKey: value })
            setExpanded((current) => {
              const nextExpanded = new Set(current)
              nextExpanded.delete(folder.key)
              nextExpanded.add(value)
              return nextExpanded
            })
            return {
              ...folder,
              key: value,
              children: folder.children.map((page) => ({ ...page, parentKey: value })),
            }
          }
          return { ...folder, [field]: value }
        }
        if (selectedRef.type === "page" && folder.key === selectedRef.folderKey) {
          return {
            ...folder,
            children: folder.children.map((page) => {
              if (page.key !== selectedRef.pageKey) {
                return page
              }
              const nextPage = { ...page, [field]: value }
              if (field === "key") {
                nextPage.routePath = `/custom/${value}`
                setSelectedRef({ type: "page", folderKey: folder.key, pageKey: value })
              }
              return nextPage
            }),
          }
        }
        return folder
      }),
    )
  }

  const updatePageType = (pageType: PageType) => {
    if (selectedRef.type !== "page") {
      return
    }
    setFoldersDirty((prev) =>
      prev.map((folder) =>
        folder.key === selectedRef.folderKey
          ? {
              ...folder,
              children: folder.children.map((page) =>
                page.key === selectedRef.pageKey ? { ...page, pageType } : page,
              ),
            }
          : folder,
      ),
    )
  }

  const moveSelected = (direction: -1 | 1) => {
    setFoldersDirty((prev) => {
      if (selectedRef.type === "folder") {
        const sorted = orderedFolders(prev)
        const index = sorted.findIndex((folder) => folder.key === selectedRef.folderKey)
        const target = index + direction
        if (index < 0 || target < 0 || target >= sorted.length) {
          return prev
        }
        const next = [...sorted]
        const current = next[index]
        next[index] = next[target]
        next[target] = current
        return reindexFolders(next)
      }
      return prev.map((folder) => {
        if (folder.key !== selectedRef.folderKey) {
          return folder
        }
        const sorted = orderedPages(folder.children)
        const index = sorted.findIndex((page) => page.key === selectedRef.pageKey)
        const target = index + direction
        if (index < 0 || target < 0 || target >= sorted.length) {
          return folder
        }
        const next = [...sorted]
        const current = next[index]
        next[index] = next[target]
        next[target] = current
        return { ...folder, children: reindexPages(next) }
      })
    })
  }

  const selectedIndex = useMemo(() => {
    if (selectedRef.type === "folder") {
      return orderedFolders(folders).findIndex((folder) => folder.key === selectedRef.folderKey)
    }
    return orderedPages(selectedFolder?.children ?? []).findIndex((page) => page.key === selectedRef.pageKey)
  }, [folders, selectedFolder?.children, selectedRef])
  const selectedListLength =
    selectedRef.type === "folder" ? folders.length : selectedFolder?.children.length ?? 0

  const handleSave = async () => {
    if (Object.keys(validationErrors).length > 0) {
      toast.error("Vui lòng kiểm tra lại các trường được đánh dấu.")
      return
    }
    setSaving(true)
    await new Promise((resolve) => window.setTimeout(resolve, 350))
    setSaving(false)
    setDirty(false)
    toast.success("Đã lưu bản nháp cấu hình giao diện")
  }

  const handlePublish = async () => {
    if (!selectedItem) {
      return
    }
    if (Object.keys(validationErrors).length > 0 || publishWarnings.length > 0) {
      toast.error("Cấu hình chưa hợp lệ để publish.")
      return
    }
    setPublishing(true)
    await new Promise((resolve) => window.setTimeout(resolve, 350))
    setFoldersDirty((prev) =>
      prev.map((folder) => {
        if (selectedItem.nodeType === "folder" && folder.key === selectedItem.key) {
          return { ...folder, status: "Published" }
        }
        if (selectedItem.nodeType === "page" && folder.key === selectedRef.folderKey) {
          return {
            ...folder,
            children: folder.children.map((page) =>
              page.key === selectedItem.key ? { ...page, status: "Published" } : page,
            ),
          }
        }
        return folder
      }),
    )
    setPublishing(false)
    toast.success("Đã publish cấu hình mô phỏng")
  }

  return (
    <div className="h-full overflow-y-auto bg-slate-50/40 p-4 md:p-6 lg:p-8">
      <div className="mx-auto flex min-h-full max-w-7xl flex-col gap-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-950">Trình thiết kế dữ liệu</h1>
            <p className="mt-1 max-w-3xl text-sm text-slate-500">
              Tạo danh mục menu cha và giao diện menu con theo mô hình folder/file cho các màn hình nghiệp vụ custom.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => setPreviewOpen((value) => !value)}>
              <Eye className="mr-2 h-4 w-4" />
              {previewOpen ? "Ẩn xem trước" : "Xem trước"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleSave}
              disabled={!dirty || saving}
            >
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Đang lưu..." : "Lưu nháp"}
            </Button>
            <Button
              type="button"
              className="bg-slate-900 text-white hover:bg-slate-800"
              onClick={handlePublish}
              disabled={publishing || Object.keys(validationErrors).length > 0 || publishWarnings.length > 0}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              {publishing ? "Đang publish..." : "Publish"}
            </Button>
          </div>
        </div>

        <div className="grid flex-1 gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
          <section className="flex min-h-[600px] flex-col rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-200 p-4">
              <div className="flex flex-col gap-2">
                <Button type="button" className="h-11 w-full justify-start bg-slate-900 text-white hover:bg-slate-800" onClick={createFolder}>
                  <FolderPlus className="mr-2 h-4 w-4" />
                  Tạo danh mục menu cha
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="h-11 w-full justify-start"
                  onClick={createPage}
                  disabled={folders.length === 0}
                  title={folders.length === 0 ? "Cần tạo danh mục menu cha trước" : "Tạo giao diện menu con"}
                >
                  <FilePlus className="mr-2 h-4 w-4" />
                  Tạo giao diện menu con
                </Button>
              </div>
              {folders.length === 0 && (
                <p className="mt-2 text-xs text-slate-500">Cần tạo danh mục menu cha trước khi tạo giao diện menu con.</p>
              )}
              <Input className="mt-3 h-10" placeholder="Tìm nhanh danh mục hoặc giao diện..." />
            </div>

            <div className="flex-1 overflow-y-auto p-3">
              {orderedFolders(folders).map((folder) => {
                const isFolderSelected = selectedRef.type === "folder" && selectedRef.folderKey === folder.key
                const isExpanded = expanded.has(folder.key)
                return (
                  <div key={folder.id} className="space-y-1">
                    <button
                      type="button"
                      onClick={() => setSelectedRef({ type: "folder", folderKey: folder.key })}
                      className={cn(
                        "flex min-h-11 w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                        isFolderSelected
                          ? "border-slate-500 bg-slate-100 text-slate-950"
                          : "border-transparent text-slate-700 hover:bg-slate-50",
                      )}
                    >
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(event) => {
                          event.stopPropagation()
                          toggleFolder(folder.key)
                        }}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault()
                            event.stopPropagation()
                            toggleFolder(folder.key)
                          }
                        }}
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded hover:bg-slate-200"
                      >
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </span>
                      <Folder className="h-4 w-4 shrink-0 text-slate-500" />
                      <span className="min-w-0 flex-1 truncate font-medium">{folder.label}</span>
                      <span className="shrink-0 text-xs text-slate-500">{folder.children.length}</span>
                    </button>
                    {isExpanded && (
                      <div className="space-y-1 pl-9">
                        {orderedPages(folder.children).map((page) => {
                          const isPageSelected =
                            selectedRef.type === "page" &&
                            selectedRef.folderKey === folder.key &&
                            selectedRef.pageKey === page.key
                          return (
                            <button
                              type="button"
                              key={page.id}
                              onClick={() =>
                                setSelectedRef({ type: "page", folderKey: folder.key, pageKey: page.key })
                              }
                              className={cn(
                                "flex min-h-10 w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                                isPageSelected
                                  ? "border-slate-500 bg-slate-100 text-slate-950"
                                  : "border-transparent text-slate-700 hover:bg-slate-50",
                              )}
                            >
                              <FileText className="h-4 w-4 shrink-0 text-slate-500" />
                              <span className="min-w-0 flex-1 truncate font-medium">{page.label}</span>
                              <Badge variant="outline" className={cn("shrink-0", statusBadgeClass(page.status))}>
                                {STATUS_LABELS[page.status]}
                              </Badge>
                            </button>
                          )
                        })}
                        {folder.children.length === 0 && (
                          <div className="rounded-md border border-dashed border-slate-200 px-3 py-4 text-sm text-slate-500">
                            Chưa có giao diện menu con
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>

          <section className="flex min-h-[600px] flex-col rounded-lg border border-slate-200 bg-white">
            {!selectedItem ? (
              <div className="flex flex-1 items-center justify-center p-8 text-sm text-slate-500">
                Chọn một danh mục hoặc giao diện để cấu hình.
              </div>
            ) : (
              <>
                <div className="flex flex-col gap-3 border-b border-slate-200 p-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="truncate text-lg font-semibold text-slate-950">{selectedItem.label}</h2>
                      <Badge variant="outline" className={statusBadgeClass(selectedItem.status)}>
                        {STATUS_LABELS[selectedItem.status]}
                      </Badge>
                      <Badge variant="secondary">{selectedItem.nodeType === "folder" ? "Folder" : "File"}</Badge>
                      <Badge variant="outline">v{selectedItem.version}</Badge>
                      {selectedItem.hasDraft && <Badge variant="secondary">Có bản nháp</Badge>}
                    </div>
                    <p className="mt-1 text-sm text-slate-500">
                      {selectedItem.nodeType === "folder"
                        ? "Cấu hình danh mục menu cha hiển thị trên sidebar."
                        : "Cấu hình giao diện menu con và liên kết metadata nghiệp vụ."}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      ETag <span className="font-mono">{selectedItem.etag}</span>
                      {selectedItem.publishedAt ? ` · Published ${selectedItem.publishedAt}` : " · Chưa publish"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => moveSelected(-1)}
                      disabled={selectedIndex <= 0}
                      title="Di chuyển lên"
                    >
                      <ArrowUp className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={() => moveSelected(1)}
                      disabled={selectedIndex < 0 || selectedIndex >= selectedListLength - 1}
                      title="Di chuyển xuống"
                    >
                      <ArrowDown className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid gap-5 p-4 2xl:grid-cols-[minmax(0,1fr)_320px]">
                  <div className="space-y-5">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="builder-label">
                          {selectedItem.nodeType === "folder" ? "Tên danh mục" : "Tên giao diện"}
                        </Label>
                        <Input
                          id="builder-label"
                          className="mt-1.5"
                          value={selectedItem.label}
                          onChange={(event) => updateSelectedField("label", event.target.value)}
                        />
                        <FieldError message={validationErrors.label} />
                      </div>
                      <div>
                        <Label htmlFor="builder-key">
                          {selectedItem.nodeType === "folder" ? "Mã danh mục" : "Mã giao diện"}
                        </Label>
                        <Input
                          id="builder-key"
                          className="mt-1.5 font-mono text-sm"
                          value={selectedItem.key}
                          onChange={(event) => updateSelectedField("key", event.target.value)}
                        />
                        <FieldError message={validationErrors.key} />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="builder-description">Mô tả</Label>
                      <Textarea
                        id="builder-description"
                        className="mt-1.5 min-h-24"
                        value={selectedItem.description ?? ""}
                        onChange={(event) => updateSelectedField("description", event.target.value)}
                        placeholder="Ghi chú nghiệp vụ cho cấu hình này"
                      />
                    </div>

                    {selectedItem.nodeType === "page" && (
                      <>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <Label htmlFor="builder-route">Route</Label>
                            <Input
                              id="builder-route"
                              className="mt-1.5 font-mono text-sm"
                              value={selectedItem.routePath}
                              onChange={(event) => updateSelectedField("routePath", event.target.value)}
                            />
                            <FieldError message={validationErrors.routePath} />
                          </div>
                          <div>
                            <Label htmlFor="builder-entity">Entity liên kết</Label>
                            <Input
                              id="builder-entity"
                              className="mt-1.5 font-mono text-sm"
                              value={selectedItem.entityKey}
                              onChange={(event) => updateSelectedField("entityKey", event.target.value)}
                            />
                            <FieldError message={validationErrors.entityKey} />
                          </div>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <Label>Loại giao diện</Label>
                            <Select value={selectedItem.pageType} onValueChange={(value) => updatePageType(value as PageType)}>
                              <SelectTrigger className="mt-1.5 h-10">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {Object.entries(PAGE_TYPE_LABELS).map(([value, label]) => (
                                  <SelectItem key={value} value={value}>
                                    {label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Danh mục menu cha</Label>
                            <div className="mt-1.5 flex h-10 items-center rounded-md border border-slate-200 bg-slate-50 px-3 text-sm text-slate-600">
                              {selectedFolder?.label ?? "Chưa chọn"}
                            </div>
                          </div>
                        </div>
                      </>
                    )}

                    <div className="grid gap-3 md:grid-cols-3">
                      {[
                        selectedItem.nodeType === "folder" ? "Thông tin chung" : "Dữ liệu",
                        selectedItem.nodeType === "folder" ? "Hiển thị trên menu" : "Giao diện",
                        selectedItem.nodeType === "folder" ? "Quyền truy cập" : "Quy trình",
                      ].map((label) => (
                        <div key={label} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3">
                          <p className="text-sm font-semibold text-slate-800">{label}</p>
                          <p className="mt-1 text-xs leading-5 text-slate-500">Sẵn sàng cho backend validate ở bước tiếp theo.</p>
                        </div>
                      ))}
                    </div>

                    {publishWarnings.length > 0 && (
                      <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                          <div>
                            <p className="text-sm font-semibold text-amber-800">Chưa đủ điều kiện publish</p>
                            <ul className="mt-1 space-y-1 text-sm text-amber-700">
                              {publishWarnings.map((warning) => (
                                <li key={warning}>{warning}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {previewOpen && (
                    <aside className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                      <h3 className="text-sm font-semibold text-slate-900">Xem trước menu</h3>
                      <div className="mt-3 space-y-2 rounded-md border border-slate-200 bg-white p-3">
                        {orderedFolders(folders).map((folder) => (
                          <div key={folder.id} className="space-y-1">
                            <div className="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-800">
                              <Folder className="h-4 w-4 text-slate-500" />
                              <span className="truncate">{folder.label}</span>
                            </div>
                            {orderedPages(folder.children).map((page) => (
                              <div key={page.id} className="ml-5 flex items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-600">
                                <FileText className="h-4 w-4 text-slate-400" />
                                <span className="truncate">{page.label}</span>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    </aside>
                  )}
                </div>
              </>
            )}
          </section>
        </div>

        <div className="sticky bottom-0 flex flex-col gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <span className="text-sm text-slate-600">
            {dirty ? "Có thay đổi chưa lưu" : "Không có thay đổi chưa lưu"}
          </span>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={createFolder}>
              <FolderPlus className="mr-2 h-4 w-4" />
              Tạo danh mục menu cha
            </Button>
            <Button type="button" variant="outline" onClick={createPage} disabled={folders.length === 0}>
              <FilePlus className="mr-2 h-4 w-4" />
              Tạo giao diện menu con
            </Button>
            <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" onClick={handleSave} disabled={!dirty || saving}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? "Đang lưu..." : "Lưu nháp"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
