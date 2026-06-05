import { useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  Edit,
  Eye,
  FolderPlus,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Search,
  SlidersHorizontal,
  Wand2,
} from "lucide-react"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import { usePageTitle } from "@/context/PageTitleContext"
import { useAuthStore, type UserRole } from "@/features/auth/store/useAuthStore"
import {
  createMockBuilderPage,
  getMockBuilderMenuTree,
  getMockBuilderPageBundle,
  previewMockLogicConnectorRule,
  saveMockBuilderDraft,
  validateBundle,
  type BuilderFieldDefinition,
  type BuilderFieldType,
  type BuilderLogicConnectorDefinition,
  type BuilderLogicConnectorOperation,
  type BuilderLogicConnectorRule,
  type BuilderLogicConnectorTrigger,
  type BuilderPageBundle,
  type BuilderWorkflowDefinition,
  type BuilderWorkflowState,
  type BuilderWorkflowTransition,
  type CreatePageWizardDraft,
} from "@/features/custom-builder/api/customBuilderMockAdapter"
import type { RuntimeCustomMenuFolder, RuntimeCustomPage, ValidationSummary } from "@/features/custom-builder/runtime/customMenuRuntime"
import { cn } from "@/lib/utils"

type BuilderMode = "list" | "create" | "edit"
type ListFilter = "all" | "Draft" | "NeedsConfig" | "Published" | "Hidden"
type WizardStep = 1 | 2 | 3 | 4 | 5
type EditSection = "overview" | "data" | "display" | "permissions" | "check" | "advanced"

type FlatInterface = {
  folder: RuntimeCustomMenuFolder
  page: RuntimeCustomPage
  fieldCount: number
}

const roleOptions: UserRole[] = ["Owner", "Admin", "Manager", "Staff", "Warehouse"]
const fieldTypeOptions: BuilderFieldType[] = ["text", "long_text", "number", "money", "date", "boolean", "single_select", "reference"]
const referenceTargets = [
  { key: "products", label: "Sản phẩm" },
  { key: "inventory_locations", label: "Kho / vị trí" },
  { key: "suppliers", label: "Nhà cung cấp" },
  { key: "customers", label: "Khách hàng" },
  { key: "users", label: "Người dùng" },
]

const statusLabels: Record<string, string> = {
  Draft: "Bản nháp",
  NeedsConfig: "Cần sửa",
  Published: "Đã publish",
  Hidden: "Ngừng hiển thị",
}

const pageTypeLabels: Record<RuntimeCustomPage["pageType"], string> = {
  record_list: "Bảng dữ liệu",
  form: "Form nhập",
  table_detail: "Bảng + chi tiết",
}

const fieldTypeLabels: Record<BuilderFieldType, string> = {
  text: "Text ngắn",
  long_text: "Text dài",
  number: "Số",
  money: "Tiền",
  date: "Ngày",
  boolean: "Đúng/sai",
  single_select: "Một lựa chọn",
  select: "Lựa chọn",
  reference: "Tham chiếu",
  line_items: "Dòng chi tiết",
}

const logicTriggerLabels: Record<BuilderLogicConnectorTrigger, string> = {
  onCreate: "Khi tạo bản ghi",
  onUpdate: "Khi cập nhật bản ghi",
  onWorkflowTransition: "Khi chuyển workflow",
}

const logicOperationLabels: Record<BuilderLogicConnectorOperation, string> = {
  copy: "Copy source sang target",
  set: "Set giá trị cố định",
  add: "Cộng",
  subtract: "Trừ",
  multiply: "Nhân",
  sumLines: "Tổng dòng chi tiết",
}

const logicOperations = Object.keys(logicOperationLabels) as BuilderLogicConnectorOperation[]

const sectionLabels: Record<EditSection, string> = {
  overview: "Tổng quan",
  data: "Dữ liệu",
  display: "Hiển thị",
  permissions: "Quyền truy cập",
  check: "Kiểm tra",
  advanced: "Nâng cao",
}

const validationSectionLabels: Record<string, string> = {
  menu: "Menu",
  data: "Dữ liệu",
  view: "Hiển thị",
  logic: "Logic field & connector",
  permission: "Quyền truy cập",
  workflow: "Workflow",
  inventory: "Nâng cao",
  runtime: "Preview/runtime",
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

function statusClass(status: string) {
  if (status === "Published") return "border-emerald-200 bg-emerald-50 text-emerald-700"
  if (status === "NeedsConfig") return "border-amber-200 bg-amber-50 text-amber-700"
  if (status === "Hidden") return "border-slate-200 bg-slate-50 text-slate-500"
  return "border-sky-200 bg-sky-50 text-sky-700"
}

function collectInterfaces(folders: RuntimeCustomMenuFolder[], bundles: Record<string, BuilderPageBundle | null>): FlatInterface[] {
  return folders.flatMap((folder) =>
    folder.children.map((page) => ({
      folder,
      page,
      fieldCount: bundles[page.key]?.fields.length ?? 0,
    })),
  )
}

function validationSectionLabel(section: string) {
  return validationSectionLabels[section] ?? section
}

function groupValidationItems<T extends { section: string }>(items: T[]) {
  return items.reduce<Record<string, T[]>>((groups, item) => {
    const key = item.section || "runtime"
    groups[key] = [...(groups[key] ?? []), item]
    return groups
  }, {})
}

function firstValidationSection(summary?: ValidationSummary) {
  return summary?.errors[0]?.section ?? summary?.warnings[0]?.section ?? null
}

function makeDraftField(index: number): BuilderFieldDefinition {
  return {
    id: `field-draft-${index}-${Date.now()}`,
    label: index === 0 ? "Tên bản ghi" : `Trường mới ${index + 1}`,
    fieldKey: index === 0 ? "name" : `truong_moi_${index + 1}`,
    type: "text",
    required: index === 0,
    filterable: index === 0,
    sortable: index === 0,
    searchable: index === 0,
    order: index,
    status: "Draft",
  }
}

function ValidationSummaryPanel({
  summary,
  onJump,
  compact = false,
  title = "Kiểm tra cấu hình",
}: {
  summary?: ValidationSummary
  onJump?: (section: string) => void
  compact?: boolean
  title?: string
}) {
  const errors = summary?.errors ?? []
  const warnings = summary?.warnings ?? []
  const errorGroups = groupValidationItems(errors)
  const warningGroups = groupValidationItems(warnings)
  const firstSection = firstValidationSection(summary)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
        <Badge variant="outline" className={summary?.valid ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}>
          {summary?.valid ? "Sẵn sàng publish" : `${errors.length} lỗi`}
        </Badge>
      </div>
      {firstSection && onJump && errors.length > 0 && (
        <Button type="button" className="w-full bg-slate-900 text-white hover:bg-slate-800" onClick={() => onJump(firstSection)}>
          Sửa lỗi đầu tiên
        </Button>
      )}
      {errors.length === 0 && warnings.length === 0 ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          Không còn lỗi bắt buộc. Publish thật vẫn do backend validate khi nối API.
        </div>
      ) : (
        <div className="space-y-3">
          {Object.entries(errorGroups).map(([section, items]) => (
            <div key={`error-${section}`} className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold">{validationSectionLabel(section)}</p>
                <Badge variant="outline" className="border-red-200 bg-white text-red-700">{items.length} lỗi</Badge>
              </div>
              <ul className={cn("mt-2 space-y-1", compact && "text-xs")}>
                {items.map((error) => (
                  <li key={`${error.section}-${error.message}-${error.fieldKey ?? ""}`}>{error.message}</li>
                ))}
              </ul>
              {onJump && (
                <Button type="button" variant="outline" size="sm" className="mt-3 bg-white" onClick={() => onJump(section)}>
                  Sửa section này
                </Button>
              )}
            </div>
          ))}
          {Object.entries(warningGroups).map(([section, items]) => (
            <div key={`warning-${section}`} className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold">{validationSectionLabel(section)}</p>
                <Badge variant="outline" className="border-amber-200 bg-white text-amber-700">{items.length} cảnh báo</Badge>
              </div>
              <ul className={cn("mt-2 space-y-1", compact && "text-xs")}>
                {items.slice(0, compact ? 2 : items.length).map((warning) => (
                  <li key={`${warning.section}-${warning.message}`}>{warning.message}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PublishReadinessPanel({
  summary,
  dirty,
  saving,
  publishing,
  conflict,
  onFixFirst,
}: {
  summary: ValidationSummary
  dirty: boolean
  saving: boolean
  publishing: boolean
  conflict: boolean
  onFixFirst: () => void
}) {
  const blockers = [
    ...summary.errors.map((error) => error.message),
    ...(dirty ? ["Có thay đổi chưa lưu."] : []),
    ...(conflict ? ["Có mock conflict, cần reload/compare trước khi publish API thật."] : []),
    ...(saving || publishing ? ["Đang xử lý thao tác, vui lòng chờ."] : []),
  ]
  const ready = blockers.length === 0

  return (
    <div className={cn("rounded-md border p-4", ready ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50")}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className={cn("text-sm font-semibold", ready ? "text-emerald-800" : "text-amber-800")}>Publish readiness</h3>
          <p className={cn("mt-1 text-sm", ready ? "text-emerald-700" : "text-amber-700")}>
            {ready ? "Không còn blocker trong UI draft. Backend vẫn là nguồn validate cuối khi có API thật." : "Publish đang bị khóa để tránh thao tác nguy hiểm."}
          </p>
        </div>
        <Badge variant="outline" className={ready ? "border-emerald-200 bg-white text-emerald-700" : "border-amber-200 bg-white text-amber-700"}>
          {ready ? "Có thể publish" : `${blockers.length} blocker`}
        </Badge>
      </div>
      {!ready && (
        <div className="mt-3 space-y-2">
          <ul className="space-y-1 text-sm text-amber-800">
            {blockers.slice(0, 5).map((blocker) => (
              <li key={blocker}>{blocker}</li>
            ))}
          </ul>
          {summary.errors.length > 0 && (
            <Button type="button" variant="outline" className="bg-white" onClick={onFixFirst}>
              Sửa lỗi đầu tiên
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

function previewValue(field: BuilderFieldDefinition, bundle: BuilderPageBundle) {
  const sample = bundle.sampleRecords[0]?.values[field.fieldKey]
  if (sample != null && sample !== "") return String(sample)
  if (field.defaultValue != null && field.defaultValue !== "") return String(field.defaultValue)
  if (field.type === "number") return "12"
  if (field.type === "money") return "1.250.000"
  if (field.type === "date") return "04/06/2026"
  if (field.type === "boolean") return "Có"
  if (field.type === "reference") return field.refEntityKey ? `Mẫu ${field.refEntityKey}` : "Chưa chọn target"
  if (field.type === "single_select" || field.type === "select") return field.options?.[0] ?? "Lựa chọn mẫu"
  return `Dữ liệu mẫu ${field.label.toLowerCase()}`
}

function LightweightPreview({ bundle, mode }: { bundle: BuilderPageBundle; mode: "table" | "form" }) {
  const activeFields = bundle.fields.filter((field) => field.status !== "Archived" && !field.hidden)
  const columns = bundle.views.listColumns
    .map((column) => {
      const field = activeFields.find((item) => item.fieldKey === column.fieldKey)
      return field ? { ...column, field } : null
    })
    .filter(Boolean) as Array<BuilderPageBundle["views"]["listColumns"][number] & { field: BuilderFieldDefinition }>
  const formFieldKeys = bundle.views.formSections[0]?.fieldKeys ?? []
  const formFields = formFieldKeys
    .map((fieldKey) => activeFields.find((field) => field.fieldKey === fieldKey))
    .filter(Boolean) as BuilderFieldDefinition[]

  if (mode === "table") {
    return (
      <div className="rounded-md border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-950">Xem thử bảng danh sách</h3>
            <p className="mt-1 text-xs text-slate-500">Preview dùng sample data trong fixture, không phải runtime thật.</p>
          </div>
          <Badge variant="outline">{columns.length} cột</Badge>
        </div>
        {columns.length === 0 ? (
          <div className="p-6 text-center text-sm text-slate-500">Chưa chọn cột để xem thử.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[640px] w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  {columns.map((column) => (
                    <th key={column.fieldKey} className="px-3 py-2">{column.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {(bundle.sampleRecords.length ? bundle.sampleRecords.slice(0, 3) : [{ id: "preview-empty", values: {}, state: "Draft", audit: [] }]).map((record) => (
                  <tr key={record.id}>
                    {columns.map((column) => (
                      <td key={column.fieldKey} className={cn("px-3 py-3", column.align === "right" && "text-right", column.align === "center" && "text-center")}>
                        {record.values[column.fieldKey] ?? previewValue(column.field, bundle)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="rounded-md border border-slate-200">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">Xem thử form nhập liệu</h3>
          <p className="mt-1 text-xs text-slate-500">Form preview chỉ minh họa layout và field bắt buộc.</p>
        </div>
        <Badge variant="outline">{formFields.length} field</Badge>
      </div>
      {formFields.length === 0 ? (
        <div className="p-6 text-center text-sm text-slate-500">Chưa chọn field để xem thử form.</div>
      ) : (
        <div className="grid gap-3 p-4 md:grid-cols-2">
          {formFields.map((field) => (
            <div key={field.id}>
              <div className="flex items-center gap-2">
                <Label>{field.label}{field.required ? " *" : ""}</Label>
                {field.readOnly && <Badge variant="outline" className="text-[11px]">read-only</Badge>}
              </div>
              <Input className="mt-1.5" value={previewValue(field, bundle)} readOnly />
              {field.type === "reference" && (
                <p className="mt-1 text-xs text-slate-500">
                  canonical: {field.refType ?? "core"}/{field.refEntityKey ?? "chưa chọn"}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function FieldLogicSettings({
  field,
  fields,
  onUpdate,
}: {
  field: BuilderFieldDefinition
  fields: BuilderFieldDefinition[]
  onUpdate: (patch: Partial<BuilderFieldDefinition>) => void
}) {
  const validation = field.validation ?? {}
  const conditional = field.conditionalVisibility
  const options = field.options ?? []
  const canHaveOptions = field.type === "single_select" || field.type === "select"
  const canHaveTextRules = field.type === "text" || field.type === "long_text"
  const canHaveNumberRules = field.type === "number" || field.type === "money"
  const canHavePattern = field.type === "text"

  const updateValidation = (patch: NonNullable<BuilderFieldDefinition["validation"]>) => {
    onUpdate({ validation: { ...validation, ...patch } })
  }

  const updateOption = (index: number, value: string) => {
    onUpdate({ options: options.map((option, optionIndex) => (optionIndex === index ? value : option)) })
  }

  return (
    <div className="md:col-span-4 rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-950">Logic cơ bản</p>
          <p className="mt-1 text-xs text-slate-500">Chỉ lưu draft trong fixture adapter; chưa chạy workflow, connector hoặc công thức thật.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs">
            <Checkbox checked={Boolean(field.readOnly)} onCheckedChange={(checked) => onUpdate({ readOnly: Boolean(checked) })} />
            Read-only
          </label>
          <label className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs">
            <Checkbox checked={Boolean(field.hidden)} onCheckedChange={(checked) => onUpdate({ hidden: Boolean(checked) })} />
            Ẩn field
          </label>
        </div>
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-3">
        <div>
          <Label>Default value</Label>
          <Input
            className="mt-1.5 bg-white"
            value={field.defaultValue == null ? "" : String(field.defaultValue)}
            onChange={(event) => onUpdate({ defaultValue: field.type === "number" || field.type === "money" ? event.target.value : event.target.value })}
            placeholder={field.type === "boolean" ? "true / false" : "Giá trị mặc định"}
          />
        </div>
        <div>
          <Label>Thông báo lỗi</Label>
          <Input
            className="mt-1.5 bg-white"
            value={validation.message ?? ""}
            onChange={(event) => updateValidation({ message: event.target.value })}
            placeholder="Nội dung lỗi dễ hiểu"
          />
        </div>
        <div>
          <Label>Computed field</Label>
          <Button type="button" variant="outline" className="mt-1.5 w-full justify-start bg-white" disabled>
            Placeholder, chưa khả dụng
          </Button>
        </div>
      </div>

      {(canHaveTextRules || canHaveNumberRules || canHavePattern) && (
        <div className="mt-3 grid gap-3 lg:grid-cols-4">
          {canHaveTextRules && (
            <>
              <div>
                <Label>Min length</Label>
                <Input className="mt-1.5 bg-white" value={validation.minLength ?? ""} onChange={(event) => updateValidation({ minLength: event.target.value })} />
              </div>
              <div>
                <Label>Max length</Label>
                <Input className="mt-1.5 bg-white" value={validation.maxLength ?? ""} onChange={(event) => updateValidation({ maxLength: event.target.value })} />
              </div>
            </>
          )}
          {canHaveNumberRules && (
            <>
              <div>
                <Label>Min</Label>
                <Input className="mt-1.5 bg-white" value={validation.min ?? ""} onChange={(event) => updateValidation({ min: event.target.value })} />
              </div>
              <div>
                <Label>Max</Label>
                <Input className="mt-1.5 bg-white" value={validation.max ?? ""} onChange={(event) => updateValidation({ max: event.target.value })} />
              </div>
            </>
          )}
          {canHavePattern && (
            <div className="lg:col-span-2">
              <Label>Regex pattern</Label>
              <Input className="mt-1.5 bg-white font-mono text-sm" value={validation.pattern ?? ""} onChange={(event) => updateValidation({ pattern: event.target.value })} />
            </div>
          )}
        </div>
      )}

      {canHaveOptions && (
        <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-950">Option editor</p>
              <p className="mt-1 text-xs text-slate-500">Dùng cho select trong preview và validation draft.</p>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={() => onUpdate({ options: [...options, `Option ${options.length + 1}`] })}>
              <Plus className="mr-2 h-4 w-4" />
              Thêm
            </Button>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {options.length === 0 ? (
              <div className="rounded-md border border-dashed border-slate-300 p-3 text-sm text-slate-500">Chưa có option.</div>
            ) : (
              options.map((option, index) => (
                <div key={`${field.id}-option-${index}`} className="flex gap-2">
                  <Input className="bg-white" value={option} onChange={(event) => updateOption(index, event.target.value)} />
                  <Button type="button" variant="outline" size="sm" onClick={() => onUpdate({ options: options.filter((_, optionIndex) => optionIndex !== index) })}>
                    Xóa
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
        <div className="flex flex-col gap-3 lg:grid lg:grid-cols-[1fr_160px_1fr_140px_auto]">
          <div>
            <Label>Điều kiện theo field</Label>
            <Select
              value={conditional?.sourceFieldKey ?? "__none"}
              onValueChange={(value) =>
                onUpdate({
                  conditionalVisibility:
                    value === "__none"
                      ? undefined
                      : { sourceFieldKey: value, operator: conditional?.operator ?? "equals", value: conditional?.value ?? "", effect: conditional?.effect ?? "show" },
                })
              }
            >
              <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none">Không dùng</SelectItem>
                {fields
                  .filter((item) => item.id !== field.id && item.status !== "Archived")
                  .map((item) => <SelectItem key={item.id} value={item.fieldKey}>{item.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Toán tử</Label>
            <Select
              value={conditional?.operator ?? "equals"}
              onValueChange={(value) => onUpdate({ conditionalVisibility: { sourceFieldKey: conditional?.sourceFieldKey, value: conditional?.value ?? "", effect: conditional?.effect ?? "show", operator: value as "equals" | "not_empty" } })}
              disabled={!conditional}
            >
              <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="equals">Bằng</SelectItem>
                <SelectItem value="not_empty">Có dữ liệu</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Giá trị</Label>
            <Input
              className="mt-1.5 bg-white"
              value={conditional?.value ?? ""}
              onChange={(event) => onUpdate({ conditionalVisibility: { sourceFieldKey: conditional?.sourceFieldKey, operator: conditional?.operator ?? "equals", effect: conditional?.effect ?? "show", value: event.target.value } })}
              disabled={!conditional || conditional.operator === "not_empty"}
            />
          </div>
          <div>
            <Label>Hành động</Label>
            <Select
              value={conditional?.effect ?? "show"}
              onValueChange={(value) => onUpdate({ conditionalVisibility: { sourceFieldKey: conditional?.sourceFieldKey, operator: conditional?.operator ?? "equals", value: conditional?.value ?? "", effect: value as "show" | "hide" } })}
              disabled={!conditional}
            >
              <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="show">Hiện</SelectItem>
                <SelectItem value="hide">Ẩn</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button type="button" variant="outline" className="w-full" disabled={!conditional} onClick={() => onUpdate({ conditionalVisibility: undefined })}>
              Xóa
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function makeWorkflowState(index: number): BuilderWorkflowState {
  return {
    id: `wf-state-${index}-${Date.now()}`,
    key: index === 0 ? "draft" : `state_${index + 1}`,
    label: index === 0 ? "Nháp" : `State ${index + 1}`,
    type: index === 0 ? "start" : "normal",
  }
}

function makeWorkflowTransition(index: number, workflow: BuilderWorkflowDefinition): BuilderWorkflowTransition {
  const fromStateKey = workflow.states[0]?.key ?? ""
  const toStateKey = workflow.states[1]?.key ?? workflow.states[0]?.key ?? ""
  return {
    id: `wf-transition-${index}-${Date.now()}`,
    label: index === 0 ? "Gửi bước tiếp theo" : `Transition ${index + 1}`,
    fromStateKey,
    toStateKey,
    allowedRoles: ["Owner", "Admin"],
  }
}

function WorkflowDesigner({
  workflow,
  onChange,
}: {
  workflow: BuilderWorkflowDefinition
  onChange: (workflow: BuilderWorkflowDefinition) => void
}) {
  const updateState = (stateId: string, patch: Partial<BuilderWorkflowState>) => {
    const previous = workflow.states.find((state) => state.id === stateId)
    onChange({
      ...workflow,
      states: workflow.states.map((state) => (state.id === stateId ? { ...state, ...patch } : state)),
      transitions: patch.key && previous
        ? workflow.transitions.map((transition) => ({
            ...transition,
            fromStateKey: transition.fromStateKey === previous.key ? patch.key! : transition.fromStateKey,
            toStateKey: transition.toStateKey === previous.key ? patch.key! : transition.toStateKey,
          }))
        : workflow.transitions,
    })
  }

  const updateTransition = (transitionId: string, patch: Partial<BuilderWorkflowTransition>) => {
    onChange({
      ...workflow,
      transitions: workflow.transitions.map((transition) => (transition.id === transitionId ? { ...transition, ...patch } : transition)),
    })
  }

  const toggleTransitionRole = (transition: BuilderWorkflowTransition, role: UserRole, checked: boolean) => {
    updateTransition(transition.id, {
      allowedRoles: checked
        ? [...new Set([...transition.allowedRoles, role])]
        : transition.allowedRoles.filter((item) => item !== role),
    })
  }

  const activeStateOptions = workflow.states.filter((state) => state.key.trim())

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-slate-500" />
            <h3 className="text-sm font-semibold text-slate-950">Workflow cơ bản</h3>
          </div>
          <p className="mt-1 text-sm text-slate-500">Chỉ thiết kế trạng thái và bước chuyển trong settings. Chưa chạy workflow thật.</p>
        </div>
        <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm">
          <Checkbox
            checked={workflow.enabled}
            onCheckedChange={(checked) => {
              const enabled = Boolean(checked)
              onChange({
                ...workflow,
                enabled,
                states: enabled && workflow.states.length === 0 ? [makeWorkflowState(0), { ...makeWorkflowState(1), key: "approved", label: "Hoàn tất", type: "final" }] : workflow.states,
              })
            }}
          />
          Bật workflow
        </label>
      </div>

      {!workflow.enabled ? (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
          Workflow đang tắt. Runtime sẽ dùng trạng thái mặc định từ fixture.
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="rounded-md border border-slate-200 p-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-950">State designer</p>
                <p className="mt-1 text-xs text-slate-500">Mỗi workflow cần một state bắt đầu và một state kết thúc.</p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={() => onChange({ ...workflow, states: [...workflow.states, makeWorkflowState(workflow.states.length)] })}>
                <Plus className="mr-2 h-4 w-4" />
                Thêm state
              </Button>
            </div>
            <div className="mt-3 space-y-2">
              {workflow.states.map((state) => (
                <div key={state.id} className="grid gap-2 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_1fr_150px_auto]">
                  <Input value={state.label} onChange={(event) => updateState(state.id, { label: event.target.value })} placeholder="Tên state" />
                  <Input className="font-mono text-sm" value={state.key} onChange={(event) => updateState(state.id, { key: slugify(event.target.value) })} placeholder="state_key" />
                  <Select value={state.type} onValueChange={(value) => updateState(state.id, { type: value as BuilderWorkflowState["type"] })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="start">Bắt đầu</SelectItem>
                      <SelectItem value="normal">Trung gian</SelectItem>
                      <SelectItem value="final">Kết thúc</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={workflow.states.length <= 2}
                    onClick={() =>
                      onChange({
                        ...workflow,
                        states: workflow.states.filter((item) => item.id !== state.id),
                        transitions: workflow.transitions.filter((transition) => transition.fromStateKey !== state.key && transition.toStateKey !== state.key),
                      })
                    }
                  >
                    Xóa
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-md border border-slate-200 p-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-950">Transition designer</p>
                <p className="mt-1 text-xs text-slate-500">Transition chỉ là cấu hình draft; không gọi API duyệt thật.</p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={() => onChange({ ...workflow, transitions: [...workflow.transitions, makeWorkflowTransition(workflow.transitions.length, workflow)] })}>
                <Plus className="mr-2 h-4 w-4" />
                Thêm transition
              </Button>
            </div>
            <div className="mt-3 space-y-2">
              {workflow.transitions.length === 0 ? (
                <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">Chưa có transition.</div>
              ) : (
                workflow.transitions.map((transition) => (
                  <div key={transition.id} className="rounded-md border border-slate-200 p-3">
                    <div className="grid gap-2 md:grid-cols-[1fr_160px_160px_auto]">
                      <Input value={transition.label} onChange={(event) => updateTransition(transition.id, { label: event.target.value })} placeholder="Tên transition" />
                      <Select value={transition.fromStateKey || "__none"} onValueChange={(value) => updateTransition(transition.id, { fromStateKey: value === "__none" ? "" : value })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="__none">Nguồn</SelectItem>
                          {activeStateOptions.map((state) => <SelectItem key={state.id} value={state.key}>{state.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                      <Select value={transition.toStateKey || "__none"} onValueChange={(value) => updateTransition(transition.id, { toStateKey: value === "__none" ? "" : value })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="__none">Đích</SelectItem>
                          {activeStateOptions.map((state) => <SelectItem key={state.id} value={state.key}>{state.label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                      <Button type="button" variant="outline" onClick={() => onChange({ ...workflow, transitions: workflow.transitions.filter((item) => item.id !== transition.id) })}>
                        Xóa
                      </Button>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {roleOptions.map((role) => (
                        <label key={role} className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-xs">
                          <Checkbox checked={transition.allowedRoles.includes(role)} onCheckedChange={(checked) => toggleTransitionRole(transition, role, Boolean(checked))} />
                          {role}
                        </label>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <p className="text-sm font-semibold text-slate-950">Preview workflow nhẹ</p>
            <div className="mt-3 flex flex-col gap-2 md:flex-row md:flex-wrap">
              {workflow.states.map((state, index) => (
                <div key={state.id} className="flex items-center gap-2">
                  <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                    <span className="font-medium text-slate-950">{state.label}</span>
                    <span className="ml-2 text-xs text-slate-500">{state.type}</span>
                  </div>
                  {index < workflow.states.length - 1 && <span className="text-slate-400">-&gt;</span>}
                </div>
              ))}
            </div>
            {workflow.transitions.length > 0 && (
              <div className="mt-3 space-y-1 text-xs text-slate-600">
                {workflow.transitions.map((transition) => (
                  <div key={transition.id}>
                    {transition.label}: {transition.fromStateKey || "?"} -&gt; {transition.toStateKey || "?"}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function makeLogicConnectorRule(index: number, fields: BuilderFieldDefinition[]): BuilderLogicConnectorRule {
  const activeFields = fields.filter((field) => field.status !== "Archived")
  const firstSource = activeFields.find((field) => field.type === "number" || field.type === "money") ?? activeFields[0]
  const firstTarget = activeFields.find((field) => field.fieldKey !== firstSource?.fieldKey) ?? activeFields[0]
  return {
    id: `logic-rule-${index}-${Date.now()}`,
    name: index === 0 ? "Quy tắc tự động đầu tiên" : `Quy tắc ${index + 1}`,
    trigger: "onCreate",
    sourceFieldKey: firstSource?.fieldKey ?? "",
    operation: "copy",
    targetFieldKey: firstTarget?.fieldKey ?? "",
    value: "",
  }
}

function LogicConnectorBuilder({
  logicConnector,
  bundle,
  onChange,
}: {
  logicConnector: BuilderLogicConnectorDefinition
  bundle: BuilderPageBundle
  onChange: (logicConnector: BuilderLogicConnectorDefinition) => void
}) {
  const [selectedRuleId, setSelectedRuleId] = useState(logicConnector.rules[0]?.id ?? "")
  const activeFields = bundle.fields.filter((field) => field.status !== "Archived")
  const selectedRule = logicConnector.rules.find((rule) => rule.id === selectedRuleId) ?? logicConnector.rules[0]

  const updateRule = (ruleId: string, patch: Partial<BuilderLogicConnectorRule>) => {
    onChange({
      ...logicConnector,
      rules: logicConnector.rules.map((rule) => (rule.id === ruleId ? { ...rule, ...patch } : rule)),
    })
  }

  const addRule = () => {
    const rule = makeLogicConnectorRule(logicConnector.rules.length, activeFields)
    onChange({ ...logicConnector, rules: [...logicConnector.rules, rule] })
    setSelectedRuleId(rule.id)
  }

  const dryRun = selectedRule ? previewMockLogicConnectorRule(selectedRule, bundle) : null
  const readonlyJson = selectedRule
    ? JSON.stringify(
        {
          trigger: selectedRule.trigger,
          sourceFieldKey: selectedRule.sourceFieldKey,
          operation: selectedRule.operation,
          targetFieldKey: selectedRule.targetFieldKey,
          value: selectedRule.value,
        },
        null,
        2,
      )
    : "{\n  \"enabled\": true,\n  \"rules\": []\n}"

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Wand2 className="h-4 w-4 text-slate-500" />
            <h3 className="text-sm font-semibold text-slate-950">Logic Connector cơ bản</h3>
          </div>
          <p className="mt-1 text-sm text-slate-500">Tạo rule tự động an toàn bằng allowlist operation. Không có SQL, JS, formula tự do hoặc endpoint tùy chỉnh.</p>
        </div>
        <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm">
          <Checkbox
            checked={logicConnector.enabled}
            onCheckedChange={(checked) => {
              const enabled = Boolean(checked)
              const rules = enabled && logicConnector.rules.length === 0 ? [makeLogicConnectorRule(0, activeFields)] : logicConnector.rules
              onChange({ ...logicConnector, enabled, rules })
              setSelectedRuleId(rules[0]?.id ?? "")
            }}
          />
          Bật logic tự động
        </label>
      </div>

      {!logicConnector.enabled ? (
        <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
          Logic tự động đang tắt. Không có connector nào chạy trong fixture.
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="rounded-md border border-slate-200 p-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-950">Connector list</p>
                <p className="mt-1 text-xs text-slate-500">Mỗi rule chạy trong mock adapter frontend, không gọi backend.</p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={addRule}>
                <Plus className="mr-2 h-4 w-4" />
                Thêm connector
              </Button>
            </div>
            <div className="mt-3 space-y-2">
              {logicConnector.rules.length === 0 ? (
                <div className="rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">Chưa có connector rule.</div>
              ) : (
                logicConnector.rules.map((rule) => (
                  <button
                    key={rule.id}
                    type="button"
                    className={cn(
                      "flex w-full flex-col gap-2 rounded-md border p-3 text-left sm:flex-row sm:items-center sm:justify-between",
                      selectedRule?.id === rule.id ? "border-slate-900 bg-slate-50" : "border-slate-200 bg-white",
                    )}
                    onClick={() => setSelectedRuleId(rule.id)}
                  >
                    <span>
                      <span className="block text-sm font-semibold text-slate-950">{rule.name || "Chưa đặt tên"}</span>
                      <span className="mt-1 block text-xs text-slate-500">
                        {logicTriggerLabels[rule.trigger]} / {rule.operation} / {rule.targetFieldKey || "chưa chọn target"}
                      </span>
                    </span>
                    <Badge variant="outline">{logicOperationLabels[rule.operation]}</Badge>
                  </button>
                ))
              )}
            </div>
          </div>

          {selectedRule && (
            <div className="rounded-md border border-slate-200 p-3">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-950">Connector wizard</p>
                  <p className="mt-1 text-xs text-slate-500">Đi theo 5 bước: trigger, source, operation, target, review.</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const nextRules = logicConnector.rules.filter((rule) => rule.id !== selectedRule.id)
                    onChange({ ...logicConnector, rules: nextRules })
                    setSelectedRuleId(nextRules[0]?.id ?? "")
                  }}
                >
                  Xóa rule
                </Button>
              </div>

              <div className="mt-3 grid gap-3 lg:grid-cols-5">
                <div>
                  <Label>1. Trigger</Label>
                  <Select value={selectedRule.trigger} onValueChange={(value) => updateRule(selectedRule.id, { trigger: value as BuilderLogicConnectorTrigger })}>
                    <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {(Object.keys(logicTriggerLabels) as BuilderLogicConnectorTrigger[]).map((trigger) => (
                        <SelectItem key={trigger} value={trigger}>{logicTriggerLabels[trigger]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>2. Source</Label>
                  <Select
                    value={selectedRule.sourceFieldKey || "__none"}
                    onValueChange={(value) => updateRule(selectedRule.id, { sourceFieldKey: value === "__none" ? "" : value })}
                    disabled={selectedRule.operation === "set"}
                  >
                    <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none">Không dùng</SelectItem>
                      {activeFields.map((field) => <SelectItem key={field.id} value={field.fieldKey}>{field.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>3. Operation</Label>
                  <Select
                    value={selectedRule.operation}
                    onValueChange={(value) =>
                      updateRule(selectedRule.id, {
                        operation: value as BuilderLogicConnectorOperation,
                        sourceFieldKey: value === "set" ? "" : selectedRule.sourceFieldKey,
                      })
                    }
                  >
                    <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {logicOperations.map((operation) => (
                        <SelectItem key={operation} value={operation}>{logicOperationLabels[operation]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>4. Target</Label>
                  <Select value={selectedRule.targetFieldKey || "__none"} onValueChange={(value) => updateRule(selectedRule.id, { targetFieldKey: value === "__none" ? "" : value })}>
                    <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none">Chọn target</SelectItem>
                      {activeFields.map((field) => <SelectItem key={field.id} value={field.fieldKey}>{field.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Giá trị set / hệ số</Label>
                  <Input
                    className="mt-1.5"
                    value={selectedRule.value}
                    onChange={(event) => updateRule(selectedRule.id, { value: event.target.value })}
                    placeholder={selectedRule.operation === "set" ? "Giá trị cố định" : "Tùy chọn"}
                  />
                </div>
              </div>

              <div className="mt-3">
                <Label>Tên rule</Label>
                <Input className="mt-1.5" value={selectedRule.name} onChange={(event) => updateRule(selectedRule.id, { name: event.target.value })} />
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                  <p className="text-sm font-semibold text-slate-950">5. Review dry-run mock</p>
                  {dryRun && (
                    <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
                      <div className="rounded-md border border-slate-200 bg-white p-3">
                        <p className="text-xs text-slate-500">Source</p>
                        <p className="mt-1 font-medium text-slate-950">{dryRun.sourceValue}</p>
                      </div>
                      <div className="rounded-md border border-slate-200 bg-white p-3">
                        <p className="text-xs text-slate-500">Target trước</p>
                        <p className="mt-1 font-medium text-slate-950">{dryRun.beforeValue}</p>
                      </div>
                      <div className="rounded-md border border-slate-200 bg-white p-3">
                        <p className="text-xs text-slate-500">Target sau</p>
                        <p className="mt-1 font-medium text-slate-950">{dryRun.afterValue}</p>
                      </div>
                    </div>
                  )}
                  <p className="mt-3 text-xs text-slate-500">{dryRun?.description}</p>
                </div>
                <div className="rounded-md border border-slate-200 p-3">
                  <p className="text-sm font-semibold text-slate-950">Rule JSON read-only</p>
                  <Textarea className="mt-3 min-h-44 font-mono text-xs" value={readonlyJson} readOnly />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function BuilderListPage({
  interfaces,
  loading,
  error,
  search,
  filter,
  pendingKey,
  onSearch,
  onFilter,
  onReload,
  onCreate,
  onEdit,
}: {
  interfaces: FlatInterface[]
  loading: boolean
  error: string | null
  search: string
  filter: ListFilter
  pendingKey: string | null
  onSearch: (value: string) => void
  onFilter: (value: ListFilter) => void
  onReload: () => void
  onCreate: () => void
  onEdit: (pageKey: string) => void
}) {
  return (
    <div className="space-y-4">
      <header className="flex flex-col gap-4 rounded-md border border-slate-200 bg-white p-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">Trình thiết kế giao diện</h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-500">
            Tạo và cấu hình giao diện custom theo từng bước. Dữ liệu hiện tại đến từ fixture frontend.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={onReload} disabled={loading}>
            <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
            Tải lại
          </Button>
          <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" onClick={onCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Tạo giao diện mới
          </Button>
        </div>
      </header>

      <section className="rounded-md border border-slate-200 bg-white">
        <div className="flex flex-col gap-3 border-b border-slate-200 p-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-950">Danh sách giao diện custom</h2>
            <p className="mt-1 text-xs text-slate-500">Không hiển thị workflow, inventory hoặc AI trong trang danh sách.</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="relative sm:w-80">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input className="pl-9" placeholder="Tìm theo tên, key, menu..." value={search} onChange={(event) => onSearch(event.target.value)} />
            </div>
            <Select value={filter} onValueChange={(value) => onFilter(value as ListFilter)}>
              <SelectTrigger className="sm:w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tất cả</SelectItem>
                <SelectItem value="Draft">Bản nháp</SelectItem>
                <SelectItem value="NeedsConfig">Cần sửa</SelectItem>
                <SelectItem value="Published">Đã publish</SelectItem>
                <SelectItem value="Hidden">Ngừng hiển thị</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {loading ? (
          <div className="space-y-3 p-4">
            {[1, 2, 3].map((item) => (
              <div key={item} className="h-16 animate-pulse rounded-md bg-slate-100" />
            ))}
          </div>
        ) : error ? (
          <div className="p-4">
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
              <Button type="button" variant="outline" className="mt-3 bg-white" onClick={onReload}>
                Thử lại
              </Button>
            </div>
          </div>
        ) : interfaces.length === 0 ? (
          <div className="flex min-h-[360px] flex-col items-center justify-center p-8 text-center">
            <Wand2 className="h-12 w-12 text-slate-400" />
            <h3 className="mt-4 text-lg font-semibold text-slate-950">Chưa có giao diện phù hợp</h3>
            <p className="mt-2 max-w-md text-sm text-slate-500">Bắt đầu bằng một wizard rõ ràng, từng bước, không nhồi nhiều panel.</p>
            <Button type="button" className="mt-4 bg-slate-900 text-white hover:bg-slate-800" onClick={onCreate}>
              <Plus className="mr-2 h-4 w-4" />
              Tạo giao diện mới
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[980px] w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Tên giao diện</th>
                  <th className="px-4 py-3">Menu cha</th>
                  <th className="px-4 py-3">Loại</th>
                  <th className="px-4 py-3">Trường</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Cập nhật</th>
                  <th className="px-4 py-3 text-right">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {interfaces.map(({ folder, page, fieldCount }) => (
                  <tr key={page.key} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-950">{page.label}</div>
                      <div className="mt-1 font-mono text-xs text-slate-500">{page.key}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-700">{folder.label}</td>
                    <td className="px-4 py-3">{pageTypeLabels[page.pageType]}</td>
                    <td className="px-4 py-3">{fieldCount || "-"}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline" className={statusClass(page.status)}>{statusLabels[page.status]}</Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{page.updatedAt}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <Button type="button" variant="outline" size="sm" onClick={() => onEdit(page.key)} disabled={pendingKey === page.key}>
                          {pendingKey === page.key ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Edit className="mr-2 h-4 w-4" />}
                          Sửa
                        </Button>
                        <Button type="button" variant="outline" size="icon-sm" title="Xem thử" disabled>
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button type="button" variant="outline" size="icon-sm" title="Nhân bản" disabled>
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

function CreateInterfaceWizard({
  folders,
  pending,
  existingKeys,
  onCancel,
  onCreate,
}: {
  folders: RuntimeCustomMenuFolder[]
  pending: boolean
  existingKeys: Set<string>
  onCancel: () => void
  onCreate: (draft: CreatePageWizardDraft) => void
}) {
  const [step, setStep] = useState<WizardStep>(1)
  const [summaryOpen, setSummaryOpen] = useState(true)
  const [label, setLabel] = useState("Giao diện quản lý mới")
  const [manualKey, setManualKey] = useState(false)
  const [key, setKey] = useState(slugify("Giao diện quản lý mới"))
  const [description, setDescription] = useState("")
  const [pageType, setPageType] = useState<RuntimeCustomPage["pageType"]>("table_detail")
  const [menuMode, setMenuMode] = useState<"existing" | "new">(folders.length ? "existing" : "new")
  const [parentKey, setParentKey] = useState(folders[0]?.key ?? "")
  const [newParentLabel, setNewParentLabel] = useState("Giao diện custom")
  const [fields, setFields] = useState<BuilderFieldDefinition[]>([makeDraftField(0)])
  const [listColumnKeys, setListColumnKeys] = useState<string[]>(["name"])
  const [formFieldKeys, setFormFieldKeys] = useState<string[]>(["name"])
  const [roles] = useState<UserRole[]>(["Owner", "Admin"])

  const routePath = `/custom/${key || "ma_giao_dien"}`
  const parentValue = menuMode === "new" ? slugify(newParentLabel) || "giao_dien_custom" : parentKey

  const stepErrors = useMemo(() => {
    const errors: Record<WizardStep, string[]> = { 1: [], 2: [], 3: [], 4: [], 5: [] }
    if (!label.trim()) errors[1].push("Tên giao diện không được để trống.")
    if (!/^[a-z0-9_]+$/.test(key)) errors[1].push("Mã giao diện chỉ gồm lowercase, số và underscore.")
    if (existingKeys.has(key)) errors[1].push("Mã giao diện đã tồn tại.")
    if (menuMode === "existing" && !parentKey) errors[2].push("Cần chọn menu cha.")
    if (menuMode === "new" && !newParentLabel.trim()) errors[2].push("Cần nhập tên menu cha mới.")
    if (fields.length === 0) errors[3].push("Cần tối thiểu một field.")
    const seen = new Set<string>()
    fields.forEach((field) => {
      if (!field.label.trim()) errors[3].push("Field cần tên hiển thị.")
      if (!/^[a-z0-9_]+$/.test(field.fieldKey)) errors[3].push(`${field.fieldKey || "field"} sai định dạng key.`)
      if (seen.has(field.fieldKey)) errors[3].push(`${field.fieldKey} bị trùng.`)
      seen.add(field.fieldKey)
      if (field.type === "reference" && (!field.refType || !field.refEntityKey)) errors[3].push(`${field.label} cần target tham chiếu.`)
    })
    if ((pageType === "record_list" || pageType === "table_detail") && listColumnKeys.length === 0) errors[4].push("Cần chọn ít nhất một cột bảng.")
    fields.filter((field) => field.required).forEach((field) => {
      if (!formFieldKeys.includes(field.fieldKey)) errors[4].push(`${field.label} bắt buộc nên phải có trong form.`)
    })
    errors[5] = [...errors[1], ...errors[2], ...errors[3], ...errors[4]]
    return errors
  }, [existingKeys, fields, formFieldKeys, key, label, listColumnKeys.length, menuMode, newParentLabel, pageType, parentKey])

  const canContinue = stepErrors[step].length === 0
  const firstStepWithError = ([1, 2, 3, 4] as WizardStep[]).find((item) => stepErrors[item].length > 0) ?? 1
  const wizardValidationSummary: ValidationSummary = {
    valid: stepErrors[5].length === 0,
    errors: [
      ...stepErrors[1].map((message) => ({ section: "data", message })),
      ...stepErrors[2].map((message) => ({ section: "menu", message })),
      ...stepErrors[3].map((message) => ({ section: "data", message })),
      ...stepErrors[4].map((message) => ({ section: "view", message })),
    ],
    warnings: [{ section: "runtime", message: "Publish thật đang khóa ở UI-first; bước này chỉ lưu draft bằng fixture adapter." }],
  }

  const updateLabel = (value: string) => {
    setLabel(value)
    if (!manualKey) setKey(slugify(value))
  }

  const updateField = (fieldId: string, patch: Partial<BuilderFieldDefinition>) => {
    setFields((current) => {
      const previous = current.find((field) => field.id === fieldId)
      if (previous && patch.fieldKey && patch.fieldKey !== previous.fieldKey) {
        setListColumnKeys((keys) => keys.map((key) => (key === previous.fieldKey ? patch.fieldKey! : key)))
        setFormFieldKeys((keys) => keys.map((key) => (key === previous.fieldKey ? patch.fieldKey! : key)))
      }
      return current.map((field) => (field.id === fieldId ? { ...field, ...patch } : field))
    })
  }

  const addField = () => {
    const next = makeDraftField(fields.length)
    setFields((current) => [...current, next])
    setListColumnKeys((current) => [...current, next.fieldKey])
    setFormFieldKeys((current) => [...current, next.fieldKey])
  }

  const submit = () => {
    onCreate({
      parentKey: parentValue,
      parentLabel: menuMode === "new" ? newParentLabel : undefined,
      label,
      key,
      description,
      routePath,
      entityKey: key,
      pageType,
      roles,
      fields,
      listColumnKeys,
      formFieldKeys,
    })
  }

  const steps: { id: WizardStep; label: string; description: string }[] = [
    { id: 1, label: "Thông tin cơ bản", description: "Đặt tên, mã, mô tả và loại giao diện." },
    { id: 2, label: "Vị trí trên menu", description: "Chọn giao diện này nằm ở đâu trong sidebar." },
    { id: 3, label: "Dữ liệu cần quản lý", description: "Tạo field cơ bản và reference canonical." },
    { id: 4, label: "Cách hiển thị", description: "Chọn cột bảng và field trong form." },
    { id: 5, label: "Kiểm tra & lưu", description: "Xem lỗi, lưu nháp hoặc chuẩn bị publish." },
  ]

  return (
    <div className="space-y-4">
      <header className="flex flex-col gap-3 rounded-md border border-slate-200 bg-white p-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">Tạo giao diện mới</h1>
          <p className="mt-1 text-sm text-slate-500">Wizard 5 bước, mỗi bước chỉ tập trung một nhóm quyết định.</p>
        </div>
        <Button type="button" variant="outline" onClick={onCancel} disabled={pending}>Quay lại danh sách</Button>
      </header>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <main className="rounded-md border border-slate-200 bg-white">
          <div className="border-b border-slate-200 p-4">
            <div className="grid gap-2 md:grid-cols-5">
              {steps.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={cn(
                    "rounded-md border px-3 py-2 text-left text-sm",
                    step === item.id ? "border-slate-900 bg-slate-100 font-semibold text-slate-950" : "border-slate-200 text-slate-600 hover:bg-slate-50",
                  )}
                  onClick={() => setStep(item.id)}
                >
                  <span className="block text-xs text-slate-500">Bước {item.id}</span>
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-5 p-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">{steps[step - 1].label}</h2>
              <p className="mt-1 text-sm text-slate-500">{steps[step - 1].description}</p>
            </div>

            {step === 1 && (
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Tên giao diện *</Label>
                  <Input className="mt-1.5" value={label} onChange={(event) => updateLabel(event.target.value)} />
                </div>
                <div>
                  <Label>Mã giao diện *</Label>
                  <Input
                    className="mt-1.5 font-mono text-sm"
                    value={key}
                    onChange={(event) => {
                      setManualKey(true)
                      setKey(slugify(event.target.value))
                    }}
                  />
                  <p className="mt-1 text-xs text-slate-500">Dùng cho route và tích hợp, nên giữ ngắn gọn.</p>
                </div>
                <div>
                  <Label>Loại giao diện *</Label>
                  <div className="mt-1.5 grid gap-2 sm:grid-cols-3">
                    {(["record_list", "form", "table_detail"] as const).map((type) => (
                      <button
                        key={type}
                        type="button"
                        className={cn(
                          "rounded-md border px-3 py-2 text-sm",
                          pageType === type ? "border-slate-900 bg-slate-100 font-semibold text-slate-950" : "border-slate-200 text-slate-600",
                        )}
                        onClick={() => setPageType(type)}
                      >
                        {pageTypeLabels[type]}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label>Route đề xuất</Label>
                  <Input className="mt-1.5 font-mono text-sm" value={routePath} readOnly />
                </div>
                <div className="md:col-span-2">
                  <Label>Mô tả</Label>
                  <Textarea className="mt-1.5 min-h-20" value={description} onChange={(event) => setDescription(event.target.value)} />
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
                <div className="space-y-4">
                  <div className="grid gap-2 sm:grid-cols-2">
                    <button type="button" className={cn("rounded-md border p-3 text-left text-sm", menuMode === "existing" ? "border-slate-900 bg-slate-100" : "border-slate-200")} onClick={() => setMenuMode("existing")} disabled={!folders.length}>
                      Dùng menu cha có sẵn
                    </button>
                    <button type="button" className={cn("rounded-md border p-3 text-left text-sm", menuMode === "new" ? "border-slate-900 bg-slate-100" : "border-slate-200")} onClick={() => setMenuMode("new")}>
                      Tạo menu cha mới
                    </button>
                  </div>
                  {menuMode === "existing" ? (
                    <div>
                      <Label>Menu cha</Label>
                      <Select value={parentKey} onValueChange={setParentKey}>
                        <SelectTrigger className="mt-1.5">
                          <SelectValue placeholder="Chọn menu cha" />
                        </SelectTrigger>
                        <SelectContent>
                          {folders.map((folder) => (
                            <SelectItem key={folder.key} value={folder.key}>{folder.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ) : (
                    <div>
                      <Label>Tên menu cha mới</Label>
                      <Input className="mt-1.5" value={newParentLabel} onChange={(event) => setNewParentLabel(event.target.value)} />
                    </div>
                  )}
                </div>
                <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase text-slate-500">Preview sidebar</p>
                  <div className="mt-3 rounded-md bg-white p-3">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                      <FolderPlus className="h-4 w-4" />
                      {menuMode === "new" ? newParentLabel || "Menu mới" : folders.find((folder) => folder.key === parentKey)?.label || "Menu cha"}
                    </div>
                    <div className="mt-2 rounded-md border-l-2 border-slate-900 bg-slate-100 px-3 py-2 text-sm text-slate-950">{label || "Giao diện mới"}</div>
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-950">Field builder</h3>
                    <p className="mt-1 text-xs text-slate-500">Reference dùng `refType/refEntityKey`, không dùng key hard-code như product_ref làm contract chính.</p>
                  </div>
                  <Button type="button" variant="outline" onClick={addField}>
                    <Plus className="mr-2 h-4 w-4" />
                    Thêm trường
                  </Button>
                </div>
                <div className="space-y-3">
                  {fields.map((field) => (
                    <div key={field.id} className="grid gap-3 rounded-md border border-slate-200 p-3 lg:grid-cols-[1fr_1fr_180px_120px_120px]">
                      <div>
                        <Label>Tên trường</Label>
                        <Input className="mt-1.5" value={field.label} onChange={(event) => updateField(field.id, { label: event.target.value })} />
                      </div>
                      <div>
                        <Label>Mã trường</Label>
                        <Input className="mt-1.5 font-mono text-sm" value={field.fieldKey} onChange={(event) => updateField(field.id, { fieldKey: slugify(event.target.value) })} />
                      </div>
                      <div>
                        <Label>Kiểu</Label>
                        <Select value={field.type} onValueChange={(value) => updateField(field.id, { type: value as BuilderFieldType, refType: value === "reference" ? field.refType ?? "core" : field.refType })}>
                          <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {fieldTypeOptions.map((type) => (
                              <SelectItem key={type} value={type}>{fieldTypeLabels[type]}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <label className="mt-7 flex items-center gap-2 text-sm">
                        <Checkbox checked={field.required} onCheckedChange={(checked) => updateField(field.id, { required: Boolean(checked) })} />
                        Bắt buộc
                      </label>
                      <label className="mt-7 flex items-center gap-2 text-sm">
                        <Checkbox checked={listColumnKeys.includes(field.fieldKey)} onCheckedChange={(checked) => setListColumnKeys((current) => checked ? [...new Set([...current, field.fieldKey])] : current.filter((key) => key !== field.fieldKey))} />
                        Hiện bảng
                      </label>
                      {field.type === "reference" && (
                        <div className="grid gap-3 lg:col-span-5 md:grid-cols-2">
                          <div>
                            <Label>Loại tham chiếu</Label>
                            <Select value={field.refType ?? "core"} onValueChange={(value) => updateField(field.id, { refType: value as "core" | "custom" })}>
                              <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="core">Core entity</SelectItem>
                                <SelectItem value="custom">Custom entity published</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Target</Label>
                            <Select value={field.refEntityKey ?? ""} onValueChange={(value) => updateField(field.id, { refEntityKey: value })}>
                              <SelectTrigger className="mt-1.5"><SelectValue placeholder="Chọn target" /></SelectTrigger>
                              <SelectContent>
                                {referenceTargets.map((target) => (
                                  <SelectItem key={target.key} value={target.key}>{target.label}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-md border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-950">Bảng danh sách</h3>
                  <div className="mt-3 space-y-2">
                    {fields.map((field) => (
                      <label key={field.id} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm">
                        <span>{field.label}</span>
                        <Checkbox checked={listColumnKeys.includes(field.fieldKey)} onCheckedChange={(checked) => setListColumnKeys((current) => checked ? [...new Set([...current, field.fieldKey])] : current.filter((key) => key !== field.fieldKey))} />
                      </label>
                    ))}
                  </div>
                </div>
                <div className="rounded-md border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-950">Form nhập liệu</h3>
                  <div className="mt-3 space-y-2">
                    {fields.map((field) => (
                      <label key={field.id} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm">
                        <span>{field.label}{field.required ? " *" : ""}</span>
                        <Checkbox checked={formFieldKeys.includes(field.fieldKey)} onCheckedChange={(checked) => setFormFieldKeys((current) => checked ? [...new Set([...current, field.fieldKey])] : current.filter((key) => key !== field.fieldKey))} />
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
                <div className="space-y-4">
                  <div className="rounded-md border border-slate-200 p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-950">Publish readiness</h3>
                        <p className="mt-1 text-xs text-slate-500">Kiểm tra trước khi lưu draft. Publish API thật chưa nằm trong scope.</p>
                      </div>
                      <Badge variant="outline" className={wizardValidationSummary.valid ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700"}>
                        {wizardValidationSummary.valid ? "Sẵn sàng lưu" : "Cần sửa"}
                      </Badge>
                    </div>
                    <dl className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                      <div><dt className="text-slate-500">Tên</dt><dd className="font-medium text-slate-950">{label}</dd></div>
                      <div><dt className="text-slate-500">Route</dt><dd className="break-all font-mono text-slate-950">{routePath}</dd></div>
                      <div><dt className="text-slate-500">Menu cha</dt><dd className="font-medium text-slate-950">{menuMode === "new" ? newParentLabel : folders.find((folder) => folder.key === parentKey)?.label}</dd></div>
                      <div><dt className="text-slate-500">Field</dt><dd className="font-medium text-slate-950">{fields.length}</dd></div>
                      <div><dt className="text-slate-500">Loại hiển thị</dt><dd className="font-medium text-slate-950">{pageTypeLabels[pageType]}</dd></div>
                      <div><dt className="text-slate-500">Quyền mặc định</dt><dd className="font-medium text-slate-950">{roles.join(", ")}</dd></div>
                    </dl>
                  </div>
                  <ValidationSummaryPanel
                    summary={wizardValidationSummary}
                    title="Lỗi cần xử lý"
                    onJump={() => setStep(firstStepWithError)}
                  />
                </div>
                <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm">
                  <h3 className="font-semibold text-slate-950">Hành động</h3>
                  <p className="mt-2 text-slate-500">
                    Lưu nháp luôn dùng fixture adapter. Publish chỉ được bật khi không còn lỗi và đã lưu draft.
                  </p>
                  <Button type="button" variant="outline" className="mt-4 w-full bg-white" disabled={wizardValidationSummary.valid} onClick={() => setStep(firstStepWithError)}>
                    Sửa lỗi đầu tiên
                  </Button>
                </div>
              </div>
            )}

            {stepErrors[step].length > 0 && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {stepErrors[step].map((error) => <div key={error}>{error}</div>)}
              </div>
            )}

            <div className="flex flex-col gap-2 border-t border-slate-200 pt-4 sm:flex-row sm:justify-between">
              <Button type="button" variant="outline" onClick={() => setStep((current) => Math.max(1, current - 1) as WizardStep)} disabled={step === 1 || pending}>
                Quay lại
              </Button>
              <div className="flex gap-2">
                {step < 5 ? (
                  <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" onClick={() => setStep((current) => Math.min(5, current + 1) as WizardStep)} disabled={!canContinue || pending}>
                    Tiếp tục
                  </Button>
                ) : (
                  <>
                    <Button type="button" variant="outline" disabled={pending || stepErrors[1].length > 0} onClick={submit}>
                      {pending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Lưu bản nháp
                    </Button>
                    <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" disabled={pending || stepErrors[5].length > 0} onClick={submit}>
                      Lưu và mở cài đặt
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>
        </main>

        <aside className="rounded-md border border-slate-200 bg-white p-4 xl:sticky xl:top-4 xl:self-start">
          <button type="button" className="flex w-full items-center justify-between text-left" onClick={() => setSummaryOpen((value) => !value)}>
            <span className="text-sm font-semibold text-slate-950">Tóm tắt</span>
            <Badge variant="outline">{summaryOpen ? "Đang mở" : "Đã đóng"}</Badge>
          </button>
          {summaryOpen && (
            <div className="mt-4 space-y-3 text-sm">
              <div><span className="text-slate-500">Tên:</span> <span className="font-medium">{label}</span></div>
              <div><span className="text-slate-500">Route:</span> <span className="font-mono">{routePath}</span></div>
              <div><span className="text-slate-500">Field:</span> <span className="font-medium">{fields.length}</span></div>
              <div><span className="text-slate-500">Lỗi bước hiện tại:</span> <span className="font-medium">{stepErrors[step].length}</span></div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

function EditInterfaceSettings({
  bundle,
  dirty,
  saving,
  publishing,
  conflict,
  onBack,
  onSave,
  onPublish,
  onChange,
}: {
  bundle: BuilderPageBundle
  dirty: boolean
  saving: boolean
  publishing: boolean
  conflict: boolean
  onBack: () => void
  onSave: () => void
  onPublish: () => void
  onChange: (updater: (current: BuilderPageBundle) => BuilderPageBundle) => void
}) {
  const [section, setSection] = useState<EditSection>("overview")
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [previewMode, setPreviewMode] = useState<"table" | "form">("table")
  const summary = validateBundle(bundle)
  const firstErrorSection = firstValidationSection(summary)

  const jumpTo = (target: string) => {
    if (target === "data" || target === "logic") setSection("data")
    else if (target === "view") setSection("display")
    else if (target === "permission") setSection("permissions")
    else setSection("check")
  }

  const updateField = (fieldId: string, patch: Partial<BuilderFieldDefinition>) => {
    onChange((current) => ({
      ...current,
      fields: current.fields.map((field) => (field.id === fieldId ? { ...field, ...patch } : field)),
      views: patch.fieldKey
        ? {
            ...current.views,
            listColumns: current.views.listColumns.map((column) =>
              column.fieldKey === current.fields.find((field) => field.id === fieldId)?.fieldKey
                ? { ...column, fieldKey: patch.fieldKey!, label: patch.label ?? column.label }
                : column,
            ),
            filterFields: current.views.filterFields.map((key) =>
              key === current.fields.find((field) => field.id === fieldId)?.fieldKey ? patch.fieldKey! : key,
            ),
            formSections: current.views.formSections.map((section) => ({
              ...section,
              fieldKeys: section.fieldKeys.map((key) =>
                key === current.fields.find((field) => field.id === fieldId)?.fieldKey ? patch.fieldKey! : key,
              ),
            })),
          }
        : current.views,
    }))
  }

  const addField = () => {
    onChange((current) => {
      const field = makeDraftField(current.fields.length)
      return {
        ...current,
        fields: [...current.fields, field],
        views: {
          ...current.views,
          listColumns: [...current.views.listColumns, { fieldKey: field.fieldKey, label: field.label, width: 180, align: "left", format: "text" }],
          formSections: current.views.formSections.map((item, index) => index === 0 ? { ...item, fieldKeys: [...item.fieldKeys, field.fieldKey] } : item),
        },
      }
    })
  }

  return (
    <div className="space-y-4">
      <header className="rounded-md border border-slate-200 bg-white p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold text-slate-950">{bundle.menuPage.label}</h1>
              <Badge variant="outline" className={statusClass(bundle.menuPage.status)}>{statusLabels[bundle.menuPage.status]}</Badge>
              {dirty && <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">Có thay đổi chưa lưu</Badge>}
            </div>
            <p className="mt-1 text-sm text-slate-500">{bundle.menuPage.description}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={onBack} disabled={saving || publishing}>Danh sách</Button>
            <Button type="button" variant="outline" onClick={onSave} disabled={!dirty || saving || publishing}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              Lưu nháp
            </Button>
            <Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" onClick={onPublish} disabled={!summary.valid || dirty || saving || publishing}>
              {publishing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
              Publish
            </Button>
          </div>
        </div>
        {conflict && (
          <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
            Mock 409: cần reload/compare trước khi publish API thật. UI không ghi đè dữ liệu.
          </div>
        )}
      </header>

      <div className="grid gap-4 xl:grid-cols-[240px_minmax(0,1fr)_320px]">
        <nav className="rounded-md border border-slate-200 bg-white p-2 xl:self-start">
          {(Object.keys(sectionLabels) as EditSection[]).map((key) => (
            <button
              key={key}
              type="button"
              className={cn(
                "flex h-10 w-full items-center rounded-md px-3 text-left text-sm",
                section === key ? "bg-slate-100 font-semibold text-slate-950" : "text-slate-600 hover:bg-slate-50",
              )}
              onClick={() => setSection(key)}
            >
              {sectionLabels[key]}
            </button>
          ))}
        </nav>

        <main className="rounded-md border border-slate-200 bg-white p-4">
          {section === "overview" && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-950">Tổng quan</h2>
              <div className="grid gap-3 md:grid-cols-4">
                {[
                  ["Trạng thái", statusLabels[bundle.menuPage.status]],
                  ["Menu cha", bundle.menuPage.parentKey],
                  ["Số field", bundle.fields.length],
                  ["Loại hiển thị", pageTypeLabels[bundle.menuPage.pageType]],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-md border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs font-semibold uppercase text-slate-500">{label}</p>
                    <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
                  </div>
                ))}
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Tên giao diện</Label>
                  <Input className="mt-1.5" value={bundle.menuPage.label} onChange={(event) => onChange((current) => ({ ...current, menuPage: { ...current.menuPage, label: event.target.value }, entityDefinition: { ...current.entityDefinition, label: event.target.value } }))} />
                </div>
                <div>
                  <Label>Route</Label>
                  <Input className="mt-1.5 font-mono text-sm" value={bundle.menuPage.routePath} readOnly />
                </div>
                <div className="md:col-span-2">
                  <Label>Mô tả</Label>
                  <Textarea className="mt-1.5 min-h-20" value={bundle.entityDefinition.description} onChange={(event) => onChange((current) => ({ ...current, entityDefinition: { ...current.entityDefinition, description: event.target.value }, menuPage: { ...current.menuPage, description: event.target.value } }))} />
                </div>
              </div>
            </div>
          )}

          {section === "data" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Dữ liệu</h2>
                  <p className="mt-1 text-sm text-slate-500">Cấu hình field, default value, validation và logic hiển thị cơ bản.</p>
                </div>
                <Button type="button" variant="outline" onClick={addField}>
                  <Plus className="mr-2 h-4 w-4" />
                  Thêm field
                </Button>
              </div>
              <div className="space-y-3">
                {bundle.fields.map((field) => (
                  <div key={field.id} className="grid gap-3 rounded-md border border-slate-200 p-3 md:grid-cols-[1fr_1fr_180px_120px]">
                    <div>
                      <Label>Tên field</Label>
                      <Input className="mt-1.5" value={field.label} onChange={(event) => updateField(field.id, { label: event.target.value })} />
                    </div>
                    <div>
                      <Label>Field key</Label>
                      <Input className="mt-1.5 font-mono text-sm" value={field.fieldKey} onChange={(event) => updateField(field.id, { fieldKey: slugify(event.target.value) })} />
                    </div>
                    <div>
                      <Label>Kiểu dữ liệu</Label>
                      <Select
                        value={field.type}
                        onValueChange={(value) =>
                          updateField(field.id, {
                            type: value as BuilderFieldType,
                            refType: value === "reference" ? field.refType ?? "core" : field.refType,
                            options: value === "single_select" || value === "select" ? field.options?.length ? field.options : ["Nháp", "Đang xử lý", "Hoàn tất"] : field.options,
                          })
                        }
                      >
                        <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {fieldTypeOptions.map((type) => <SelectItem key={type} value={type}>{fieldTypeLabels[type]}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <label className="mt-7 flex items-center gap-2 text-sm">
                      <Checkbox checked={field.required} onCheckedChange={(checked) => updateField(field.id, { required: Boolean(checked) })} />
                      Bắt buộc
                    </label>
                    {field.type === "reference" && (
                      <div className="grid gap-3 md:col-span-4 md:grid-cols-2">
                        <div>
                          <Label>Loại tham chiếu</Label>
                          <Select value={field.refType ?? "core"} onValueChange={(value) => updateField(field.id, { refType: value as "core" | "custom" })}>
                            <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="core">Core entity</SelectItem>
                              <SelectItem value="custom">Custom entity</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Target</Label>
                          <Select value={field.refEntityKey ?? ""} onValueChange={(value) => updateField(field.id, { refEntityKey: value })}>
                            <SelectTrigger className="mt-1.5"><SelectValue placeholder="Target" /></SelectTrigger>
                            <SelectContent>{referenceTargets.map((target) => <SelectItem key={target.key} value={target.key}>{target.label}</SelectItem>)}</SelectContent>
                          </Select>
                        </div>
                      </div>
                    )}
                    <FieldLogicSettings field={field} fields={bundle.fields} onUpdate={(patch) => updateField(field.id, patch)} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {section === "display" && (
            <div className="space-y-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-950">Hiển thị</h2>
                  <p className="mt-1 text-sm text-slate-500">Chọn field cho bảng/form rồi xem thử ngay trong settings.</p>
                </div>
                <div className="grid grid-cols-2 gap-2 rounded-md border border-slate-200 bg-slate-50 p-1">
                  {[
                    ["table", "Bảng"],
                    ["form", "Form"],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      className={cn(
                        "rounded px-3 py-1.5 text-sm",
                        previewMode === value ? "bg-white font-semibold text-slate-950 shadow-sm" : "text-slate-600",
                      )}
                      onClick={() => setPreviewMode(value as "table" | "form")}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-md border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-950">Bảng danh sách</h3>
                  <div className="mt-3 space-y-2">
                    {bundle.fields.map((field) => {
                      const checked = bundle.views.listColumns.some((column) => column.fieldKey === field.fieldKey)
                      return (
                        <label key={field.id} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm">
                          {field.label}
                          <Checkbox
                            checked={checked}
                            onCheckedChange={(value) =>
                              onChange((current) => ({
                                ...current,
                                views: {
                                  ...current.views,
                                  listColumns: value
                                    ? [...current.views.listColumns, { fieldKey: field.fieldKey, label: field.label, width: 180, align: "left", format: "text" }]
                                    : current.views.listColumns.filter((column) => column.fieldKey !== field.fieldKey),
                                },
                              }))
                            }
                          />
                        </label>
                      )
                    })}
                  </div>
                </div>
                <div className="rounded-md border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-950">Form nhập liệu</h3>
                  <div className="mt-3 space-y-2">
                    {bundle.fields.map((field) => {
                      const section = bundle.views.formSections[0]
                      const checked = section?.fieldKeys.includes(field.fieldKey) ?? false
                      return (
                        <label key={field.id} className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm">
                          {field.label}{field.required ? " *" : ""}
                          <Checkbox
                            checked={checked}
                            onCheckedChange={(value) =>
                              onChange((current) => ({
                                ...current,
                                views: {
                                  ...current.views,
                                  formSections: current.views.formSections.map((item, index) =>
                                    index === 0
                                      ? { ...item, fieldKeys: value ? [...new Set([...item.fieldKeys, field.fieldKey])] : item.fieldKeys.filter((key) => key !== field.fieldKey) }
                                      : item,
                                  ),
                                },
                              }))
                            }
                          />
                        </label>
                      )
                    })}
                  </div>
                </div>
              </div>
              <LightweightPreview bundle={bundle} mode={previewMode} />
            </div>
          )}

          {section === "permissions" && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-950">Quyền truy cập</h2>
              {(["view", "create", "update", "delete"] as const).map((action) => (
                <div key={action} className="rounded-md border border-slate-200 p-3">
                  <p className="text-sm font-semibold text-slate-950">{action === "view" ? "Có thể xem" : action === "create" ? "Có thể tạo" : action === "update" ? "Có thể sửa" : "Có thể xóa"}</p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-3">
                    {roleOptions.map((role) => (
                      <label key={role} className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm">
                        <Checkbox
                          checked={bundle.permissions[action].includes(role)}
                          onCheckedChange={(checked) =>
                            onChange((current) => ({
                              ...current,
                              permissions: {
                                ...current.permissions,
                                [action]: checked
                                  ? [...current.permissions[action], role]
                                  : current.permissions[action].filter((item) => item !== role),
                              },
                            }))
                          }
                        />
                        {role}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {section === "check" && (
            <div className="space-y-4">
              <PublishReadinessPanel
                summary={summary}
                dirty={dirty}
                saving={saving}
                publishing={publishing}
                conflict={conflict}
                onFixFirst={() => firstErrorSection && jumpTo(firstErrorSection)}
              />
              <ValidationSummaryPanel summary={summary} title="Lỗi và cảnh báo theo section" onJump={jumpTo} />
              <div className="grid gap-4 lg:grid-cols-2">
                <LightweightPreview bundle={bundle} mode="table" />
                <LightweightPreview bundle={bundle} mode="form" />
              </div>
            </div>
          )}

          {section === "advanced" && (
            <div className="space-y-4">
              <button type="button" className="flex w-full items-center justify-between rounded-md border border-slate-200 p-4 text-left" onClick={() => setAdvancedOpen((value) => !value)}>
                  <span>
                    <span className="block font-semibold text-slate-950">Nâng cao</span>
                  <span className="mt-1 block text-sm text-slate-500">Mở khi cần workflow hoặc logic connector cơ bản. Inventory và AI vẫn là placeholder.</span>
                </span>
                <Badge variant="outline">{advancedOpen ? "Đang mở" : "Đang đóng"}</Badge>
              </button>
              {advancedOpen && (
                <div className="space-y-3">
                  <WorkflowDesigner
                    workflow={bundle.workflow}
                    onChange={(workflow) => onChange((current) => ({ ...current, workflow }))}
                  />
                  <LogicConnectorBuilder
                    logicConnector={bundle.logicConnector}
                    bundle={bundle}
                    onChange={(logicConnector) => onChange((current) => ({ ...current, logicConnector }))}
                  />
                  <div className="grid gap-3 md:grid-cols-2">
                  {["Inventory effect", "AI copilot"].map((item) => (
                    <div key={item} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                      <p className="font-semibold text-slate-950">{item}</p>
                      <p className="mt-2 text-sm text-slate-500">Tính năng này sẽ được cấu hình sau khi giao diện dữ liệu cơ bản đã ổn định.</p>
                      <Button type="button" variant="outline" className="mt-3" disabled>Chưa khả dụng</Button>
                    </div>
                  ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>

        <aside className="rounded-md border border-slate-200 bg-white p-4 xl:self-start">
          <ValidationSummaryPanel summary={summary} onJump={jumpTo} compact />
          <div className="mt-4 rounded-md border border-slate-200 p-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-950">
              <Eye className="h-4 w-4 text-slate-500" />
              Preview nhẹ
            </div>
            <p className="mt-2 text-xs text-slate-500">Preview nằm trong settings, chỉ dùng sample fixture và không ghi runtime.</p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setSection("display")}>
                Bảng
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={() => {
                setPreviewMode("form")
                setSection("display")
              }}>
                Form
              </Button>
            </div>
          </div>
          <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
            Backend: không sửa. ai_python: không sửa. Mock adapter frontend đang dùng.
          </div>
        </aside>
      </div>
    </div>
  )
}

export function CustomBuilderPage() {
  const { setTitle } = usePageTitle()
  const canManageBuilder = useAuthStore((state) => state.menuPermissions.can_manage_custom_builder)
  const [mode, setMode] = useState<BuilderMode>("list")
  const [folders, setFolders] = useState<RuntimeCustomMenuFolder[]>([])
  const [bundleCache, setBundleCache] = useState<Record<string, BuilderPageBundle | null>>({})
  const [selectedBundle, setSelectedBundle] = useState<BuilderPageBundle | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState<ListFilter>("all")
  const [pendingKey, setPendingKey] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [dirty, setDirty] = useState(false)
  const [conflict, setConflict] = useState(false)

  useEffect(() => {
    setTitle("Trình thiết kế giao diện")
  }, [setTitle])

  const loadTree = async () => {
    setLoading(true)
    setError(null)
    try {
      const tree = await getMockBuilderMenuTree()
      setFolders(tree.folders)
      const bundleEntries = await Promise.all(
        tree.folders.flatMap((folder) => folder.children.map(async (page) => [page.key, await getMockBuilderPageBundle(page.key)] as const)),
      )
      setBundleCache(Object.fromEntries(bundleEntries))
    } catch {
      setError("Không tải được danh sách giao diện từ fixture adapter.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadTree()
  }, [])

  const interfaces = useMemo(() => {
    const clean = search.trim().toLowerCase()
    return collectInterfaces(folders, bundleCache)
      .filter(({ page }) => filter === "all" || page.status === filter)
      .filter(({ folder, page }) => !clean || page.label.toLowerCase().includes(clean) || page.key.toLowerCase().includes(clean) || folder.label.toLowerCase().includes(clean))
  }, [bundleCache, filter, folders, search])

  const existingKeys = useMemo(() => {
    const keys = new Set<string>()
    folders.forEach((folder) => {
      keys.add(folder.key)
      folder.children.forEach((page) => keys.add(page.key))
    })
    return keys
  }, [folders])

  const openEditor = async (pageKey: string) => {
    setPendingKey(pageKey)
    try {
      const bundle = bundleCache[pageKey] ?? await getMockBuilderPageBundle(pageKey)
      if (!bundle) {
        toast.error("Không tìm thấy bundle trong fixture.")
        return
      }
      setSelectedBundle(bundle)
      setDirty(false)
      setConflict(false)
      setMode("edit")
    } finally {
      setPendingKey(null)
    }
  }

  const handleCreate = async (draft: CreatePageWizardDraft) => {
    setCreating(true)
    try {
      const bundle = await createMockBuilderPage(draft)
      const tree = await getMockBuilderMenuTree()
      setFolders(tree.folders)
      setBundleCache((current) => ({ ...current, [bundle.menuPage.key]: bundle }))
      setSelectedBundle(bundle)
      setDirty(false)
      setConflict(false)
      setMode("edit")
      toast.success("Đã tạo bản nháp giao diện bằng fixture adapter")
    } finally {
      setCreating(false)
    }
  }

  const updateBundle = (updater: (current: BuilderPageBundle) => BuilderPageBundle) => {
    setSelectedBundle((current) => {
      if (!current) return current
      const next = updater(current)
      return { ...next, validationSummary: validateBundle(next) }
    })
    setDirty(true)
  }

  const saveDraft = async () => {
    if (!selectedBundle) return
    setSaving(true)
    try {
      const saved = await saveMockBuilderDraft(selectedBundle)
      setSelectedBundle(saved)
      setBundleCache((current) => ({ ...current, [saved.menuPage.key]: saved }))
      setDirty(false)
      setConflict(false)
      toast.success("Đã lưu bản nháp trong mock adapter")
    } finally {
      setSaving(false)
    }
  }

  const publish = () => {
    setPublishing(true)
    window.setTimeout(() => {
      setPublishing(false)
      setConflict(true)
      toast.error("Mock 409: cần reload/compare trước khi publish API thật")
    }, 520)
  }

  if (!canManageBuilder) {
    return (
      <div className="flex min-h-full items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md rounded-md border border-slate-200 bg-white p-6 text-center shadow-sm">
          <AlertTriangle className="mx-auto h-10 w-10 text-slate-400" />
          <h1 className="mt-4 text-lg font-semibold text-slate-950">Bạn không có quyền mở trình thiết kế</h1>
          <p className="mt-2 text-sm text-slate-500">Frontend chỉ hiển thị; backend sẽ enforce quyền ở API thật.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-4 md:p-6">
      <div className="mx-auto max-w-7xl">
        {mode === "list" && (
          <BuilderListPage
            interfaces={interfaces}
            loading={loading}
            error={error}
            search={search}
            filter={filter}
            pendingKey={pendingKey}
            onSearch={setSearch}
            onFilter={setFilter}
            onReload={() => void loadTree()}
            onCreate={() => setMode("create")}
            onEdit={(pageKey) => void openEditor(pageKey)}
          />
        )}
        {mode === "create" && (
          <CreateInterfaceWizard
            folders={folders}
            pending={creating}
            existingKeys={existingKeys}
            onCancel={() => setMode("list")}
            onCreate={handleCreate}
          />
        )}
        {mode === "edit" && selectedBundle && (
          <EditInterfaceSettings
            bundle={selectedBundle}
            dirty={dirty}
            saving={saving}
            publishing={publishing}
            conflict={conflict}
            onBack={() => {
              setMode("list")
              setSelectedBundle(null)
            }}
            onSave={() => void saveDraft()}
            onPublish={publish}
            onChange={updateBundle}
          />
        )}
      </div>
    </div>
  )
}
