import type { UserRole } from "@/features/auth/store/useAuthStore"
import type { MenuPermissions } from "@/features/auth/types/menuPermissions"
import type {
  CustomRuntimePageType,
  CustomRuntimeStatus,
  RuntimeCustomFolder,
  RuntimeCustomMenuFolder,
  RuntimeCustomPage,
  ValidationSummary,
} from "@/features/custom-builder/runtime/customMenuRuntime"

export type BuilderStatus = CustomRuntimeStatus
export type BuilderRolePreview = UserRole | "All"
export type BuilderFieldType =
  | "text"
  | "long_text"
  | "number"
  | "money"
  | "date"
  | "boolean"
  | "single_select"
  | "select"
  | "reference"
  | "line_items"
export type ValidationSection = "menu" | "data" | "view" | "workflow" | "logic" | "inventory" | "permission" | "runtime"

export type BuilderFieldDefinition = {
  id: string
  label: string
  fieldKey: string
  type: BuilderFieldType
  required: boolean
  filterable: boolean
  sortable: boolean
  searchable: boolean
  order: number
  helperText?: string
  refType?: "core" | "custom"
  refEntityKey?: string
  options?: string[]
  defaultValue?: string | number | boolean
  readOnly?: boolean
  hidden?: boolean
  validation?: {
    minLength?: string
    maxLength?: string
    min?: string
    max?: string
    pattern?: string
    message?: string
  }
  conditionalVisibility?: {
    sourceFieldKey?: string
    operator: "equals" | "not_empty"
    value?: string
    effect: "show" | "hide"
  }
  computed?: {
    enabled: boolean
    label?: string
  }
  status: "Active" | "Draft" | "Archived"
}

export type BuilderViewColumn = {
  fieldKey: string
  label: string
  width: number
  align: "left" | "right" | "center"
  format: "text" | "number" | "currency" | "date" | "badge"
}

export function inferColumnFormat(fieldType: BuilderFieldType): BuilderViewColumn["format"] {
  if (fieldType === "money") return "currency"
  if (fieldType === "number") return "number"
  if (fieldType === "date") return "date"
  return "text"
}

export type BuilderFormSection = {
  id: string
  title: string
  fieldKeys: string[]
}

export type BuilderViewDefinition = {
  listColumns: BuilderViewColumn[]
  filterFields: string[]
  defaultSort: string
  formSections: BuilderFormSection[]
  previewMode: "desktop" | "tablet" | "mobile"
}

export type BuilderPermissionDraft = {
  view: UserRole[]
  create: UserRole[]
  update: UserRole[]
  delete: UserRole[]
}

export type BuilderWorkflowState = {
  id: string
  key: string
  label: string
  type: "start" | "normal" | "final"
}

export type BuilderWorkflowTransition = {
  id: string
  label: string
  fromStateKey: string
  toStateKey: string
  allowedRoles: UserRole[]
}

export type BuilderWorkflowDefinition = {
  enabled: boolean
  states: BuilderWorkflowState[]
  transitions: BuilderWorkflowTransition[]
}

export type BuilderLogicConnectorTrigger = "onCreate" | "onUpdate" | "onWorkflowTransition"
export type BuilderLogicConnectorOperation = "copy" | "set" | "add" | "subtract" | "multiply" | "sumLines"

export const LOGIC_CONNECTOR_OPERATIONS: Record<BuilderLogicConnectorOperation, true> = {
  copy: true,
  set: true,
  add: true,
  subtract: true,
  multiply: true,
  sumLines: true,
}

export type BuilderLogicConnectorRule = {
  id: string
  name: string
  trigger: BuilderLogicConnectorTrigger
  sourceFieldKey: string
  operation: BuilderLogicConnectorOperation
  targetFieldKey: string
  value: string
}

export type BuilderLogicConnectorDefinition = {
  enabled: boolean
  rules: BuilderLogicConnectorRule[]
}

export type BuilderPageBundle = {
  menuPage: RuntimeCustomPage
  entityDefinition: {
    key: string
    label: string
    description: string
    status: BuilderStatus
    version: number
  }
  fields: BuilderFieldDefinition[]
  views: BuilderViewDefinition
  permissions: BuilderPermissionDraft
  workflow: BuilderWorkflowDefinition
  logicConnector: BuilderLogicConnectorDefinition
  validationSummary: ValidationSummary
  etag: string
  sampleRecords: RuntimeRecord[]
}

export type RuntimeRecord = {
  id: string
  state: "Draft" | "Pending" | "Approved"
  audit: { at: string; actor: string; action: string }[]
  values: Record<string, string | number>
}

export type BuilderMenuTree = {
  treeEtag: string
  folders: RuntimeCustomMenuFolder[]
}

export type CreatePageWizardDraft = {
  parentKey: string
  parentLabel?: string
  label: string
  key: string
  description?: string
  routePath: string
  entityKey: string
  pageType: CustomRuntimePageType
  roles: UserRole[]
  fields?: BuilderFieldDefinition[]
  listColumnKeys?: string[]
  formFieldKeys?: string[]
}

const okSummary: ValidationSummary = { valid: true, errors: [], warnings: [] }

const workflowOff: BuilderWorkflowDefinition = {
  enabled: false,
  states: [],
  transitions: [],
}

const logicConnectorOff: BuilderLogicConnectorDefinition = {
  enabled: false,
  rules: [],
}

const damagedStockWorkflow: BuilderWorkflowDefinition = {
  enabled: true,
  states: [
    { id: "wf-state-draft", key: "draft", label: "Nháp", type: "start" },
    { id: "wf-state-pending", key: "pending_review", label: "Chờ duyệt", type: "normal" },
    { id: "wf-state-done", key: "approved", label: "Đã duyệt", type: "final" },
  ],
  transitions: [
    { id: "wf-transition-submit", label: "Gửi duyệt", fromStateKey: "draft", toStateKey: "pending_review", allowedRoles: ["Owner", "Admin", "Warehouse"] },
    { id: "wf-transition-approve", label: "Duyệt", fromStateKey: "pending_review", toStateKey: "approved", allowedRoles: ["Owner", "Admin"] },
  ],
}

const damagedStockLogicConnector: BuilderLogicConnectorDefinition = {
  enabled: true,
  rules: [
    {
      id: "logic-rule-damage-label",
      name: "Đặt trạng thái khi có số lượng hỏng",
      trigger: "onCreate",
      sourceFieldKey: "damaged_quantity",
      operation: "set",
      targetFieldKey: "handling_status",
      value: "Chờ xử lý",
    },
  ],
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
      warnings: [{ section: "workflow", message: "Quy trình đang tắt ở stage UI-1 đến UI-3." }],
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
          warnings: [{ section: "runtime", message: "Runtime đang dùng fixture frontend, chưa ghi dữ liệu thật." }],
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
        validationSummary: okSummary,
      },
    ],
  },
  {
    nodeType: "folder",
    id: "folder-sales-custom",
    key: "ban_hang_mo_rong",
    label: "Bán hàng mở rộng",
    description: "Các trang custom đang ở bản nháp UI-first.",
    status: "Draft",
    sortOrder: 1,
    roles: ["Owner", "Admin"],
    version: 1,
    draftVersion: 1,
    publishedVersion: 0,
    hasDraft: true,
    updatedAt: "03/06/2026",
    updatedByName: "Bạn",
    etag: "folder-ban-hang-mo-rong-draft-1",
    validationSummary: {
      valid: false,
      errors: [{ section: "menu", message: "Danh mục chưa publish nên chưa hiện ở runtime." }],
      warnings: [],
    },
    children: [],
  },
]

const damagedStockFields: BuilderFieldDefinition[] = [
  {
    id: "field-code",
    label: "Mã phiếu",
    fieldKey: "report_code",
    type: "text",
    required: true,
    filterable: true,
    sortable: true,
    searchable: true,
    order: 0,
    helperText: "Sinh theo định dạng KH-YYYY-NNNN.",
    defaultValue: "KH-2026-0001",
    readOnly: true,
    validation: { pattern: "^KH-[0-9]{4}-[0-9]{4}$", message: "Mã phiếu cần theo dạng KH-YYYY-NNNN." },
    status: "Active",
  },
  {
    id: "field-product",
    label: "Sản phẩm",
    fieldKey: "product_ref",
    type: "reference",
    required: true,
    filterable: true,
    sortable: false,
    searchable: true,
    order: 1,
    helperText: "Reference canonical dùng refType/refEntityKey.",
    refType: "core",
    refEntityKey: "Product",
    status: "Active",
  },
  {
    id: "field-location",
    label: "Vị trí kho",
    fieldKey: "location_ref",
    type: "reference",
    required: true,
    filterable: true,
    sortable: false,
    searchable: false,
    order: 2,
    refType: "core",
    refEntityKey: "InventoryLocation",
    status: "Active",
  },
  {
    id: "field-quantity",
    label: "Số lượng hỏng",
    fieldKey: "damaged_quantity",
    type: "number",
    required: true,
    filterable: false,
    sortable: true,
    searchable: false,
    order: 3,
    validation: { min: "1", max: "999" },
    status: "Active",
  },
  {
    id: "field-status",
    label: "Trạng thái xử lý",
    fieldKey: "handling_status",
    type: "single_select",
    required: false,
    filterable: true,
    sortable: false,
    searchable: false,
    order: 4,
    options: ["Nháp", "Chờ xử lý", "Đã xử lý"],
    defaultValue: "Chờ xử lý",
    status: "Draft",
  },
  {
    id: "field-lines",
    label: "Dòng kiểm hàng",
    fieldKey: "inspection_lines",
    type: "line_items",
    required: false,
    filterable: false,
    sortable: false,
    searchable: false,
    order: 5,
    helperText: "Có row limit và cảnh báo trước khi nối inventory effect ở stage sau.",
    conditionalVisibility: { sourceFieldKey: "damaged_quantity", operator: "not_empty", effect: "show" },
    status: "Draft",
  },
]

const damagedStockView: BuilderViewDefinition = {
  listColumns: [
    { fieldKey: "report_code", label: "Mã phiếu", width: 140, align: "left", format: "text" },
    { fieldKey: "product_ref", label: "Sản phẩm", width: 220, align: "left", format: "text" },
    { fieldKey: "location_ref", label: "Vị trí", width: 160, align: "left", format: "text" },
    { fieldKey: "damaged_quantity", label: "SL hỏng", width: 120, align: "right", format: "number" },
    { fieldKey: "handling_status", label: "Trạng thái", width: 140, align: "left", format: "badge" },
  ],
  filterFields: ["report_code", "product_ref", "location_ref", "handling_status"],
  defaultSort: "report_code desc",
  formSections: [
    { id: "section-general", title: "Thông tin chung", fieldKeys: ["report_code", "product_ref", "location_ref"] },
    { id: "section-quantity", title: "Kiểm hàng", fieldKeys: ["damaged_quantity", "handling_status", "inspection_lines"] },
  ],
  previewMode: "desktop",
}

const damagedStockRecords: RuntimeRecord[] = [
  {
    id: "dsr-001",
    state: "Pending",
    values: {
      report_code: "KH-2026-0001",
      product_ref: "Áo khoác chống nước",
      location_ref: "Kho chính / Kệ A4",
      damaged_quantity: 6,
      handling_status: "Chờ xử lý",
    },
    audit: [
      { at: "03/06/2026 09:15", actor: "Nguyễn Admin", action: "Tạo phiếu từ runtime fixture" },
      { at: "03/06/2026 09:20", actor: "Kho hàng", action: "Cập nhật số lượng kiểm đếm" },
    ],
  },
  {
    id: "dsr-002",
    state: "Draft",
    values: {
      report_code: "KH-2026-0002",
      product_ref: "Bình giữ nhiệt 500ml",
      location_ref: "Kho phụ / Kệ B1",
      damaged_quantity: 2,
      handling_status: "Nháp",
    },
    audit: [{ at: "03/06/2026 10:05", actor: "Nguyễn Admin", action: "Tạo nháp" }],
  },
]

const pageBundles: Record<string, BuilderPageBundle> = {
  phieu_kiem_hang_hong: {
    menuPage: customRuntimeCatalog[0].children[0],
    entityDefinition: {
      key: "damaged_stock_report",
      label: "Phiếu kiểm hàng hỏng",
      description: "Entity custom cho ghi nhận sản phẩm hỏng trong kho.",
      status: "Published",
      version: 5,
    },
    fields: damagedStockFields,
    views: damagedStockView,
    workflow: damagedStockWorkflow,
    logicConnector: damagedStockLogicConnector,
    permissions: {
      view: ["Owner", "Admin", "Staff", "Warehouse"],
      create: ["Owner", "Admin", "Warehouse"],
      update: ["Owner", "Admin", "Warehouse"],
      delete: ["Owner", "Admin"],
    },
    validationSummary: {
      valid: true,
      errors: [],
      warnings: [
        { section: "data", message: "3 field filter/sort sẽ cần index backend khi chuyển sang API thật." },
        { section: "inventory", message: "Inventory effect chưa bật trong scope UI-1 đến UI-3." },
      ],
    },
    etag: "bundle-phieu-kiem-hang-hong-v5",
    sampleRecords: damagedStockRecords,
  },
  kiem_toan_chat_luong_noi_bo: {
    menuPage: customRuntimeCatalog[0].children[1],
    entityDefinition: {
      key: "internal_quality_audit",
      label: "Kiểm toán chất lượng nội bộ",
      description: "Entity minh họa page hạn chế quyền.",
      status: "Published",
      version: 1,
    },
    fields: damagedStockFields.slice(0, 3),
    views: {
      ...damagedStockView,
      listColumns: damagedStockView.listColumns.slice(0, 3),
      filterFields: ["report_code"],
    },
    workflow: workflowOff,
    logicConnector: logicConnectorOff,
    permissions: { view: ["Owner", "Admin"], create: ["Owner", "Admin"], update: ["Owner"], delete: ["Owner"] },
    validationSummary: okSummary,
    etag: "bundle-kiem-toan-chat-luong-v1",
    sampleRecords: [],
  },
}

function delay<T>(value: T, ms = 260) {
  return new Promise<T>((resolve) => window.setTimeout(() => resolve(structuredClone(value)), ms))
}

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

function allKeys() {
  const keys = new Set<string>()
  customRuntimeCatalog.forEach((folder) => {
    keys.add(folder.key)
    folder.children.forEach((page) => keys.add(page.key))
  })
  return keys
}

function uniqueKey(base: string) {
  const keys = allKeys()
  const clean = slugify(base) || "custom_page"
  let next = clean
  let index = 2
  while (keys.has(next)) {
    next = `${clean}_${index}`
    index += 1
  }
  return next
}

export async function getMockBuilderMenuTree(): Promise<BuilderMenuTree> {
  return delay({ treeEtag: "custom-builder-tree-fixture-20260603", folders: customRuntimeCatalog })
}

export async function getMockRuntimeCustomMenu(): Promise<BuilderMenuTree> {
  return delay({
    treeEtag: "custom-runtime-menu-fixture-20260603",
    folders: customRuntimeCatalog.filter((folder) => folder.status === "Published"),
  })
}

export async function getMockBuilderPageBundle(pageKey: string): Promise<BuilderPageBundle | null> {
  return delay(pageBundles[pageKey] ?? null)
}

export async function getMockRuntimePageBundle(pageKey: string): Promise<BuilderPageBundle | null> {
  const bundle = pageBundles[pageKey]
  if (!bundle || bundle.menuPage.status !== "Published") {
    return delay(null)
  }
  return delay(bundle)
}

export async function createMockBuilderPage(input: CreatePageWizardDraft): Promise<BuilderPageBundle> {
  const key = uniqueKey(input.key || input.label)
  let folder = customRuntimeCatalog.find((item) => item.key === input.parentKey)
  if (!folder) {
    folder = {
      nodeType: "folder",
      id: `folder-${input.parentKey}`,
      key: input.parentKey,
      label: input.parentLabel || input.parentKey,
      description: "Menu cha tạo từ wizard settings-first.",
      status: "Draft",
      sortOrder: customRuntimeCatalog.length,
      roles: input.roles,
      version: 1,
      draftVersion: 1,
      publishedVersion: 0,
      hasDraft: true,
      updatedAt: "03/06/2026",
      updatedByName: "Bạn",
      etag: `folder-${input.parentKey}-draft-1`,
      validationSummary: okSummary,
      children: [],
    }
    customRuntimeCatalog.push(folder)
  }
  const page: RuntimeCustomPage = {
    nodeType: "page",
    id: `page-${key}`,
    key,
    label: input.label,
    parentKey: input.parentKey,
    routePath: input.routePath || `/custom/${key}`,
    entityKey: input.entityKey || key,
    pageType: input.pageType,
    status: "NeedsConfig",
    sortOrder: 99,
    description: input.description || "Trang tạo từ wizard settings-first, đang dùng fixture frontend.",
    roles: input.roles,
    version: 1,
    draftVersion: 1,
    publishedVersion: 0,
    hasDraft: true,
    updatedAt: "03/06/2026",
    updatedByName: "Bạn",
    etag: `page-${key}-draft-1`,
    validationSummary: {
      valid: false,
      errors: [
        { section: "data", message: "Cần thêm tối thiểu một field bắt buộc." },
        { section: "view", message: "Cần chọn cột hiển thị cho list view." },
      ],
      warnings: [{ section: "permission", message: "Quyền đang dùng mặc định từ wizard." }],
    },
  }
  folder.children.push(page)
  const draftFields =
    input.fields && input.fields.length > 0
      ? input.fields.map((field, index) => ({ ...field, order: index, status: field.status ?? "Draft" }))
      : [
          {
            id: `field-${key}-name`,
            label: "Tên bản ghi",
            fieldKey: "name",
            type: "text",
            required: true,
            filterable: true,
            sortable: true,
            searchable: true,
            order: 0,
            defaultValue: "Bản ghi mẫu",
            status: "Draft" as const,
          },
        ]
  const listColumnKeys = input.listColumnKeys?.length ? input.listColumnKeys : draftFields.slice(0, 3).map((field) => field.fieldKey)
  const formFieldKeys = input.formFieldKeys?.length ? input.formFieldKeys : draftFields.map((field) => field.fieldKey)
  const bundle: BuilderPageBundle = {
    menuPage: page,
    entityDefinition: {
      key: page.entityKey,
      label: input.label,
      description: input.description || "Entity draft sinh từ wizard.",
      status: "NeedsConfig",
      version: 1,
    },
    fields: draftFields,
    views: {
      listColumns: listColumnKeys.map((fieldKey) => {
        const field = draftFields.find((item) => item.fieldKey === fieldKey)
        return {
          fieldKey,
          label: field?.label ?? fieldKey,
          width: 180,
          align: field?.type === "number" || field?.type === "money" ? "right" : "left",
          format: inferColumnFormat(field?.type ?? "text"),
        }
      }),
      filterFields: draftFields.filter((field) => field.searchable || field.filterable).map((field) => field.fieldKey),
      defaultSort: `${listColumnKeys[0] ?? draftFields[0]?.fieldKey ?? "name"} asc`,
      formSections: [{ id: "section-main", title: "Thông tin chính", fieldKeys: formFieldKeys }],
      previewMode: "desktop",
    },
    permissions: { view: input.roles, create: input.roles, update: input.roles, delete: ["Owner", "Admin"] },
    workflow: workflowOff,
    logicConnector: logicConnectorOff,
    validationSummary: page.validationSummary,
    etag: `bundle-${key}-draft-1`,
    sampleRecords: [],
  }
  const next = { ...bundle, validationSummary: validateBundle(bundle) }
  page.validationSummary = next.validationSummary
  pageBundles[key] = next
  return delay(next, 420)
}

export async function saveMockBuilderDraft(bundle: BuilderPageBundle): Promise<BuilderPageBundle> {
  const next: BuilderPageBundle = {
    ...bundle,
    etag: `${bundle.etag}-saved`,
    validationSummary: validateBundle(bundle),
  }
  const folder = customRuntimeCatalog.find((item) => item.children.some((page) => page.key === next.menuPage.key))
  if (folder) {
    folder.children = folder.children.map((page) =>
      page.key === next.menuPage.key ? { ...next.menuPage, validationSummary: next.validationSummary } : page,
    )
  }
  pageBundles[bundle.menuPage.key] = next
  return delay(next, 420)
}

export type BuilderLogicConnectorDryRun = {
  sourceValue: string
  beforeValue: string
  afterValue: string
  description: string
}

function numericValue(value: string | number | undefined) {
  const parsed = Number(value ?? 0)
  return Number.isNaN(parsed) ? 0 : parsed
}

export function previewMockLogicConnectorRule(
  rule: BuilderLogicConnectorRule,
  bundle: BuilderPageBundle,
): BuilderLogicConnectorDryRun {
  const sampleValues = bundle.sampleRecords[0]?.values ?? {}
  const sourceValue = sampleValues[rule.sourceFieldKey]
  const targetValue = sampleValues[rule.targetFieldKey]
  let afterValue: string | number = targetValue ?? ""

  if (rule.operation === "copy") {
    afterValue = sourceValue ?? ""
  }
  if (rule.operation === "set") {
    afterValue = rule.value
  }
  if (rule.operation === "add") {
    afterValue = numericValue(targetValue) + numericValue(sourceValue)
  }
  if (rule.operation === "subtract") {
    afterValue = numericValue(targetValue) - numericValue(sourceValue)
  }
  if (rule.operation === "multiply") {
    const multiplier = rule.sourceFieldKey ? numericValue(sourceValue) : numericValue(rule.value) || 1
    afterValue = numericValue(targetValue) * multiplier
  }
  if (rule.operation === "sumLines") {
    afterValue = numericValue(targetValue) + numericValue(sourceValue)
  }

  return {
    sourceValue: sourceValue == null || sourceValue === "" ? "(trống)" : String(sourceValue),
    beforeValue: targetValue == null || targetValue === "" ? "(trống)" : String(targetValue),
    afterValue: afterValue === "" ? "(trống)" : String(afterValue),
    description: "Dry-run fixture chỉ minh họa trước/sau trong frontend, không ghi dữ liệu thật.",
  }
}

export function validateBundle(bundle: BuilderPageBundle): ValidationSummary {
  const errors: ValidationSummary["errors"] = []
  const warnings: ValidationSummary["warnings"] = []
  const activeFields = bundle.fields.filter((field) => field.status !== "Archived")
  if (bundle.fields.length === 0) {
    errors.push({ section: "data", message: "Entity cần tối thiểu một field." })
  }
  const seenFieldKeys = new Set<string>()
  bundle.fields.forEach((field) => {
    if (!field.label.trim()) {
      errors.push({ section: "data", message: "Field bắt buộc phải có tên hiển thị.", fieldKey: field.fieldKey })
    }
    if (!/^[a-z0-9_]+$/.test(field.fieldKey)) {
      errors.push({ section: "data", message: `${field.fieldKey || "field"} chỉ được dùng lowercase, số và underscore.`, fieldKey: field.fieldKey })
    }
    if (seenFieldKeys.has(field.fieldKey)) {
      errors.push({ section: "data", message: `Field key ${field.fieldKey} bị trùng.`, fieldKey: field.fieldKey })
    }
    seenFieldKeys.add(field.fieldKey)
  })
  if (!bundle.views.listColumns.length) {
    errors.push({ section: "view", message: "List view cần tối thiểu một cột." })
  }
  const fieldKeys = new Set(bundle.fields.map((field) => field.fieldKey))
  bundle.views.listColumns.forEach((column) => {
    if (!fieldKeys.has(column.fieldKey)) {
      errors.push({ section: "view", message: `Cột ${column.fieldKey} đang tham chiếu field không tồn tại.` })
    }
  })
  bundle.views.filterFields.forEach((fieldKey) => {
    if (!fieldKeys.has(fieldKey)) {
      errors.push({ section: "view", message: `Filter ${fieldKey} đang tham chiếu field không tồn tại.` })
    }
  })
  const [sortFieldKey, sortDirection] = bundle.views.defaultSort.split(" ")
  if (sortFieldKey && !fieldKeys.has(sortFieldKey)) {
    errors.push({ section: "view", message: `Default sort ${sortFieldKey} đang tham chiếu field không tồn tại.` })
  }
  if (sortDirection && sortDirection !== "asc" && sortDirection !== "desc") {
    errors.push({ section: "view", message: "Default sort chỉ hỗ trợ asc hoặc desc." })
  }
  bundle.fields.forEach((field) => {
    const options = (field.options ?? []).map((option) => option.trim()).filter(Boolean)
    const normalizedOptions = options.map((option) => option.toLowerCase())
    const validation = field.validation ?? {}

    if ((field.filterable || field.sortable) && field.status !== "Archived") {
      warnings.push({ section: "data", message: `${field.label} cần index backend khi publish API thật.`, fieldKey: field.fieldKey })
    }
    if (field.type === "line_items") {
      warnings.push({ section: "inventory", message: `${field.label} có row limit trước khi nối inventory effect.`, fieldKey: field.fieldKey })
    }
    if (field.type === "reference" && (!field.refType || !field.refEntityKey)) {
      errors.push({ section: "data", message: `${field.label} cần refType và refEntityKey.`, fieldKey: field.fieldKey })
    }
    if ((field.type === "single_select" || field.type === "select") && options.length === 0) {
      errors.push({ section: "logic", message: `${field.label} cần tối thiểu một option.`, fieldKey: field.fieldKey })
    }
    if (new Set(normalizedOptions).size !== normalizedOptions.length) {
      errors.push({ section: "logic", message: `${field.label} có option bị trùng.`, fieldKey: field.fieldKey })
    }
    if ((field.type === "single_select" || field.type === "select") && field.defaultValue && !options.includes(String(field.defaultValue))) {
      errors.push({ section: "logic", message: `${field.label} có giá trị mặc định không nằm trong option.`, fieldKey: field.fieldKey })
    }
    if ((field.type === "number" || field.type === "money") && field.defaultValue !== undefined && Number.isNaN(Number(field.defaultValue))) {
      errors.push({ section: "logic", message: `${field.label} cần default value dạng số.`, fieldKey: field.fieldKey })
    }
    const minLength = validation.minLength ? Number(validation.minLength) : null
    const maxLength = validation.maxLength ? Number(validation.maxLength) : null
    if (minLength != null && Number.isNaN(minLength)) {
      errors.push({ section: "logic", message: `${field.label} có min length không hợp lệ.`, fieldKey: field.fieldKey })
    }
    if (maxLength != null && Number.isNaN(maxLength)) {
      errors.push({ section: "logic", message: `${field.label} có max length không hợp lệ.`, fieldKey: field.fieldKey })
    }
    if (minLength != null && maxLength != null && !Number.isNaN(minLength) && !Number.isNaN(maxLength) && minLength > maxLength) {
      errors.push({ section: "logic", message: `${field.label} có min length lớn hơn max length.`, fieldKey: field.fieldKey })
    }
    const min = validation.min ? Number(validation.min) : null
    const max = validation.max ? Number(validation.max) : null
    if (min != null && Number.isNaN(min)) {
      errors.push({ section: "logic", message: `${field.label} có min number không hợp lệ.`, fieldKey: field.fieldKey })
    }
    if (max != null && Number.isNaN(max)) {
      errors.push({ section: "logic", message: `${field.label} có max number không hợp lệ.`, fieldKey: field.fieldKey })
    }
    if (min != null && max != null && !Number.isNaN(min) && !Number.isNaN(max) && min > max) {
      errors.push({ section: "logic", message: `${field.label} có min number lớn hơn max number.`, fieldKey: field.fieldKey })
    }
    if (validation.pattern) {
      try {
        new RegExp(validation.pattern)
      } catch {
        errors.push({ section: "logic", message: `${field.label} có regex pattern không hợp lệ.`, fieldKey: field.fieldKey })
      }
    }
    if (field.required && field.hidden) {
      errors.push({ section: "logic", message: `${field.label} đang bắt buộc nhưng bị ẩn.`, fieldKey: field.fieldKey })
    }
    if (field.required && field.readOnly && field.defaultValue === undefined) {
      warnings.push({ section: "logic", message: `${field.label} read-only nên cần default value trước khi publish thật.`, fieldKey: field.fieldKey })
    }
    if (field.conditionalVisibility) {
      if (!field.conditionalVisibility.sourceFieldKey) {
        errors.push({ section: "logic", message: `${field.label} cần chọn field điều kiện.`, fieldKey: field.fieldKey })
      } else if (field.conditionalVisibility.sourceFieldKey === field.fieldKey) {
        errors.push({ section: "logic", message: `${field.label} không được dùng chính nó làm điều kiện hiển thị.`, fieldKey: field.fieldKey })
      } else if (!activeFields.some((item) => item.fieldKey === field.conditionalVisibility?.sourceFieldKey)) {
        errors.push({ section: "logic", message: `${field.label} đang tham chiếu field điều kiện không tồn tại.`, fieldKey: field.fieldKey })
      }
    }
    if (field.computed?.enabled) {
      warnings.push({ section: "logic", message: `${field.label} mới là computed placeholder, chưa chạy công thức thật.`, fieldKey: field.fieldKey })
    }
  })
  const formFieldKeys = new Set(bundle.views.formSections.flatMap((section) => section.fieldKeys))
  bundle.views.formSections.forEach((section) => {
    if (!section.title.trim()) {
      errors.push({ section: "view", message: "Form section cần tên hiển thị." })
    }
    section.fieldKeys.forEach((fieldKey) => {
      if (!fieldKeys.has(fieldKey)) {
        errors.push({ section: "view", message: `Form section ${section.title || section.id} đang tham chiếu field ${fieldKey} không tồn tại.` })
      }
    })
  })
  bundle.fields
    .filter((field) => field.required && field.status !== "Archived")
    .forEach((field) => {
      if (!formFieldKeys.has(field.fieldKey)) {
        errors.push({ section: "view", message: `${field.label} là bắt buộc nên phải có trong form.`, fieldKey: field.fieldKey })
      }
    })
  const workflowSummary = validateWorkflow(bundle.workflow)
  workflowSummary.errors.forEach((error) => errors.push(error))
  workflowSummary.warnings.forEach((warning) => warnings.push(warning))
  const logicConnectorSummary = validateLogicConnector(bundle.logicConnector, bundle.fields)
  logicConnectorSummary.errors.forEach((error) => errors.push(error))
  logicConnectorSummary.warnings.forEach((warning) => warnings.push(warning))
  return { valid: errors.length === 0, errors, warnings }
}

function validateLogicConnector(
  logicConnector: BuilderLogicConnectorDefinition,
  fields: BuilderFieldDefinition[],
): Pick<ValidationSummary, "errors" | "warnings"> {
  const errors: ValidationSummary["errors"] = []
  const warnings: ValidationSummary["warnings"] = []
  if (!logicConnector.enabled) {
    return { errors, warnings }
  }
  const activeFields = fields.filter((field) => field.status !== "Archived")
  const fieldByKey = new Map(activeFields.map((field) => [field.fieldKey, field]))
  const operationsRequiringSource: BuilderLogicConnectorOperation[] = ["copy", "add", "subtract", "sumLines"]
  if (logicConnector.rules.length === 0) {
    errors.push({ section: "logic", message: "Logic tự động đang bật cần tối thiểu một connector rule." })
  }
  logicConnector.rules.forEach((rule) => {
    const sourceField = fieldByKey.get(rule.sourceFieldKey)
    const targetField = fieldByKey.get(rule.targetFieldKey)
    if (!rule.name.trim()) {
      errors.push({ section: "logic", message: "Connector rule cần tên hiển thị." })
    }
    if (!(rule.operation in LOGIC_CONNECTOR_OPERATIONS)) {
      errors.push({ section: "logic", message: `${rule.name || "Connector rule"} dùng operation không nằm trong allowlist.` })
    }
    if (!rule.targetFieldKey || !targetField) {
      errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần target field hợp lệ.` })
    }
    if (operationsRequiringSource.includes(rule.operation) && (!rule.sourceFieldKey || !sourceField)) {
      errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần source field hợp lệ.` })
    }
    if (rule.operation === "multiply" && !rule.sourceFieldKey && !rule.value.trim()) {
      errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần source field hoặc giá trị hệ số.` })
    }
    if (rule.operation === "set" && !rule.value.trim()) {
      errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần giá trị set cố định.` })
    }
    if (rule.operation !== "set" && rule.sourceFieldKey && rule.sourceFieldKey === rule.targetFieldKey) {
      errors.push({ section: "logic", message: `${rule.name || "Connector rule"} không được dùng cùng một field làm source và target.` })
    }
    if (["add", "subtract", "multiply"].includes(rule.operation)) {
      const sourceNumeric = sourceField?.type === "number" || sourceField?.type === "money"
      const targetNumeric = targetField?.type === "number" || targetField?.type === "money"
      if (sourceField && !sourceNumeric) {
        errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần source dạng số cho operation ${rule.operation}.`, fieldKey: rule.sourceFieldKey })
      }
      if (targetField && !targetNumeric) {
        errors.push({ section: "logic", message: `${rule.name || "Connector rule"} cần target dạng số cho operation ${rule.operation}.`, fieldKey: rule.targetFieldKey })
      }
    }
    if (rule.operation === "sumLines" && sourceField && sourceField.type !== "line_items") {
      warnings.push({ section: "logic", message: `${rule.name || "Connector rule"} sumLines mới là dry-run mock, cần line_items khi nối API thật.`, fieldKey: rule.sourceFieldKey })
    }
  })
  return { errors, warnings }
}

function validateWorkflow(workflow: BuilderWorkflowDefinition): Pick<ValidationSummary, "errors" | "warnings"> {
  const errors: ValidationSummary["errors"] = []
  const warnings: ValidationSummary["warnings"] = []
  if (!workflow.enabled) {
    return { errors, warnings }
  }
  const activeStates = workflow.states.filter((state) => state.key.trim())
  if (activeStates.length < 2) {
    errors.push({ section: "workflow", message: "Workflow bật cần tối thiểu 2 state." })
  }
  const stateKeys = new Set<string>()
  activeStates.forEach((state) => {
    if (!/^[a-z0-9_]+$/.test(state.key)) {
      errors.push({ section: "workflow", message: `${state.label || state.key} có state key không hợp lệ.` })
    }
    if (!state.label.trim()) {
      errors.push({ section: "workflow", message: `${state.key || "state"} cần tên hiển thị.` })
    }
    if (stateKeys.has(state.key)) {
      errors.push({ section: "workflow", message: `State key ${state.key} bị trùng.` })
    }
    stateKeys.add(state.key)
  })
  if (!activeStates.some((state) => state.type === "start")) {
    errors.push({ section: "workflow", message: "Workflow cần một state bắt đầu." })
  }
  if (!activeStates.some((state) => state.type === "final")) {
    errors.push({ section: "workflow", message: "Workflow cần một state kết thúc." })
  }
  if (workflow.transitions.length === 0) {
    errors.push({ section: "workflow", message: "Workflow bật cần tối thiểu một transition." })
  }
  workflow.transitions.forEach((transition) => {
    if (!transition.label.trim()) {
      errors.push({ section: "workflow", message: "Transition cần tên hiển thị." })
    }
    if (!stateKeys.has(transition.fromStateKey)) {
      errors.push({ section: "workflow", message: `${transition.label || "Transition"} thiếu state nguồn hợp lệ.` })
    }
    if (!stateKeys.has(transition.toStateKey)) {
      errors.push({ section: "workflow", message: `${transition.label || "Transition"} thiếu state đích hợp lệ.` })
    }
    if (transition.fromStateKey && transition.fromStateKey === transition.toStateKey) {
      errors.push({ section: "workflow", message: `${transition.label || "Transition"} không được đi về cùng một state.` })
    }
    if (transition.allowedRoles.length === 0) {
      warnings.push({ section: "workflow", message: `${transition.label || "Transition"} chưa chọn role thực hiện.` })
    }
  })
  return { errors, warnings }
}

export function roleCanOpenPage(page: RuntimeCustomPage, role: UserRole | null) {
  return role == null || page.roles.includes(role)
}

export function permissionCanOpenPage(
  page: RuntimeCustomPage,
  permissions: MenuPermissions,
  role: UserRole | null,
) {
  if (!roleCanOpenPage(page, role)) {
    return false
  }
  const entityAllowed = page.entityPermission ? Boolean(permissions[page.entityPermission]) : true
  const dataAllowed = page.dataPermission ? Boolean(permissions[page.dataPermission]) : true
  return entityAllowed && dataAllowed
}
