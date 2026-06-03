import type { UserRole } from "@/features/auth/store/useAuthStore"
import type { MenuPermissions } from "@/features/auth/types/menuPermissions"

export type CustomRuntimeStatus = "Draft" | "Published" | "NeedsConfig" | "Hidden"
export type CustomRuntimePageType = "record_list" | "form" | "table_detail"

export type ValidationSummary = {
  valid: boolean
  errors: { section: string; message: string; fieldKey?: string }[]
  warnings: { section: string; message: string }[]
}

export type RuntimeCustomPage = {
  nodeType: "page"
  id: string
  key: string
  label: string
  parentKey: string
  routePath: string
  entityKey: string
  pageType: CustomRuntimePageType
  status: CustomRuntimeStatus
  sortOrder: number
  description?: string
  roles: UserRole[]
  entityPermission?: keyof MenuPermissions
  dataPermission?: keyof MenuPermissions
  version: number
  draftVersion?: number
  publishedVersion: number
  hasDraft: boolean
  publishedAt?: string
  publishedByName?: string
  updatedAt: string
  updatedByName?: string
  etag: string
  validationSummary: ValidationSummary
}

export type RuntimeCustomFolder = {
  nodeType: "folder"
  id: string
  key: string
  label: string
  description?: string
  status: Exclude<CustomRuntimeStatus, "NeedsConfig">
  sortOrder: number
  roles: UserRole[]
  version: number
  draftVersion?: number
  publishedVersion: number
  hasDraft: boolean
  publishedAt?: string
  publishedByName?: string
  updatedAt: string
  updatedByName?: string
  etag: string
  validationSummary: ValidationSummary
  children: RuntimeCustomPage[]
}

export type RuntimeCustomMenuFolder = RuntimeCustomFolder & {
  children: RuntimeCustomPage[]
}

export const customRuntimeCatalog: RuntimeCustomFolder[] = [
  {
    nodeType: "folder",
    id: "folder-quality",
    key: "kiem_hang",
    label: "Kiểm hàng",
    description: "Nhóm giao diện kiểm hàng và xử lý sự cố kho.",
    status: "Published",
    sortOrder: 0,
    roles: ["Owner", "Admin", "Staff", "Warehouse"],
    version: 3,
    draftVersion: 4,
    publishedVersion: 3,
    hasDraft: true,
    publishedAt: "03/06/2026",
    publishedByName: "System Administrator",
    updatedAt: "03/06/2026",
    updatedByName: "System Administrator",
    etag: "folder-kiem-hang-v3",
    validationSummary: {
      valid: true,
      errors: [],
      warnings: [{ section: "workflow", message: "Quy trình đang dùng cấu hình mặc định." }],
    },
    children: [
      {
        nodeType: "page",
        id: "page-damaged-stock",
        key: "phieu_kiem_hang_hong",
        label: "Phiếu kiểm hàng hỏng",
        parentKey: "kiem_hang",
        routePath: "/custom/phieu_kiem_hang_hong",
        entityKey: "damaged_stock_report",
        pageType: "table_detail",
        status: "Published",
        sortOrder: 0,
        description: "Ghi nhận sản phẩm hỏng và chuẩn bị quy trình kiểm duyệt.",
        roles: ["Owner", "Admin", "Staff", "Warehouse"],
        entityPermission: "can_manage_inventory",
        dataPermission: "can_manage_inventory",
        version: 5,
        draftVersion: 6,
        publishedVersion: 5,
        hasDraft: true,
        publishedAt: "03/06/2026",
        publishedByName: "System Administrator",
        updatedAt: "03/06/2026",
        updatedByName: "System Administrator",
        etag: "page-phieu-kiem-hang-hong-v5",
        validationSummary: {
          valid: true,
          errors: [],
          warnings: [
            { section: "runtime", message: "Runtime hiện là bản preview, chưa ghi dữ liệu thật." },
          ],
        },
      },
      {
        nodeType: "page",
        id: "page-internal-quality-audit",
        key: "kiem_toan_chat_luong_noi_bo",
        label: "Kiểm toán chất lượng nội bộ",
        parentKey: "kiem_hang",
        routePath: "/custom/kiem_toan_chat_luong_noi_bo",
        entityKey: "internal_quality_audit",
        pageType: "record_list",
        status: "Published",
        sortOrder: 1,
        description: "Trang minh họa page bị ẩn với role không phù hợp.",
        roles: ["Owner", "Admin"],
        entityPermission: "can_manage_staff",
        dataPermission: "can_manage_staff",
        version: 1,
        publishedVersion: 1,
        hasDraft: false,
        publishedAt: "03/06/2026",
        publishedByName: "System Administrator",
        updatedAt: "03/06/2026",
        updatedByName: "System Administrator",
        etag: "page-kiem-toan-chat-luong-v1",
        validationSummary: { valid: true, errors: [], warnings: [] },
      },
    ],
  },
]

function roleAllowed(allowedRoles: UserRole[], role: UserRole | null) {
  return role == null || allowedRoles.includes(role)
}

function permissionAllowed(
  permission: keyof MenuPermissions | undefined,
  permissions: MenuPermissions,
  role: UserRole | null,
) {
  if (!permission) {
    return true
  }
  if (role == null) {
    return true
  }
  return Boolean(permissions[permission])
}

export function canSeeRuntimeFolder(
  folder: RuntimeCustomFolder,
  permissions: MenuPermissions,
  role: UserRole | null,
) {
  return folder.status === "Published" && roleAllowed(folder.roles, role) && getVisibleRuntimePages(folder, permissions, role).length > 0
}

export function canSeeRuntimePage(
  page: RuntimeCustomPage,
  permissions: MenuPermissions,
  role: UserRole | null,
) {
  return (
    page.status === "Published" &&
    roleAllowed(page.roles, role) &&
    permissionAllowed(page.entityPermission, permissions, role) &&
    permissionAllowed(page.dataPermission, permissions, role)
  )
}

export function getVisibleRuntimePages(
  folder: RuntimeCustomFolder,
  permissions: MenuPermissions,
  role: UserRole | null,
) {
  return folder.children
    .filter((page) => canSeeRuntimePage(page, permissions, role))
    .sort((a, b) => a.sortOrder - b.sortOrder)
}

export function getRuntimeCustomMenuForUser(
  permissions: MenuPermissions,
  role: UserRole | null,
  source: RuntimeCustomFolder[] = customRuntimeCatalog,
): RuntimeCustomMenuFolder[] {
  return source
    .filter((folder) => canSeeRuntimeFolder(folder, permissions, role))
    .sort((a, b) => a.sortOrder - b.sortOrder)
    .map((folder) => ({
      ...folder,
      children: getVisibleRuntimePages(folder, permissions, role),
    }))
}

export function findRuntimeCustomPage(pageKey: string, source: RuntimeCustomFolder[] = customRuntimeCatalog) {
  for (const folder of source) {
    const page = folder.children.find((child) => child.key === pageKey)
    if (page) {
      return { folder, page }
    }
  }
  return null
}
