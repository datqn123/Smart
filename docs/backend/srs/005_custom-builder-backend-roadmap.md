# SRS-BE-005 — Custom Builder: Backend Development Roadmap

> File: `docs/backend/srs/005_custom-builder-backend-roadmap.md`
> Agent: SRS_WRITER
> Ngày tạo: 2026-06-06
> Trạng thái: READY_FOR_TECH_SPEC
> Phạm vi: Backend Spring Boot + PostgreSQL cho toàn bộ Custom Builder feature

---

## 1. Bối cảnh và mục tiêu

Frontend Custom Builder đã hoàn thiện ở dạng mock (prototype sử dụng `customBuilderMockAdapter.ts`). Tất cả dữ liệu đang được lưu in-memory trong fixture frontend, không có persistence, không có RBAC backend, không có published version thật.

Mục tiêu của SRS này: định nghĩa **thứ tự phát triển backend từng bước**, để từng bước có thể tích hợp với frontend và test độc lập.

**Tài liệu gốc đã đọc:**

| File | Vai trò |
|------|---------|
| `docs/dev/common/001_custom-builder-program-overview.md` | Nguyên tắc metadata-driven, no free script |
| `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md` | Data model, API contract, scale |
| `docs/dev/common/003_custom-builder-phase2-workflow.md` | Workflow state machine |
| `docs/dev/common/004_custom-builder-phase3-logic-connector.md` | Logic connector execution |
| `docs/backend/srs/003_custom-interface-builder-task1.md` | API contract builder menu |
| `docs/frontend/srs/010_custom-builder-menu-interface-design.md` | Suggested API list, runtime rules |
| `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts` | Toàn bộ types mock làm contract tham chiếu |

**Stack hiện tại của backend:**
- Spring Boot (Java), JDBC Repository pattern (không dùng JPA/Hibernate)
- PostgreSQL
- JWT auth với `MenuPermissionClaims` (`mp` claim)
- Pattern: `Controller → Service → JdbcRepository`

---

## 2. Nguyên tắc bắt buộc (từ program overview)

| Nguyên tắc | Bắt buộc |
|-----------|---------|
| Metadata-driven | User tạo definition/field/view/workflow metadata, không tạo SQL table vật lý |
| Backend authoritative | Backend validate/publish/execute; UI chỉ là trải nghiệm builder |
| No free script | Không cho SQL/JS/Groovy/SpEL/custom API call từ user |
| Polymorphic reference | Reference dùng `{refType, refEntityKey, refId, labelSnapshot}` |
| Versioned definition | Record giữ `definition_version`, không tự động áp definition mới |
| No optimistic update | Không update UI trước khi backend confirm cho publish/transition |
| etag conflict | Mọi save/publish gửi `etag`, backend trả 409 nếu conflict |

---

## 3. Thứ tự phát triển — 7 bước

```
Step 1: Database Schema
    ↓
Step 2: RBAC — Thêm permissions vào JWT
    ↓
Step 3: Entity + Field + View Foundation (metadata CRUD)
    ↓
Step 4: Menu Tree (Folder + Page builder API)
    ↓
Step 5: Record CRUD (runtime workspace)
    ↓
Step 6: Workflow (state machine)
    ↓
Step 7: Logic Connector (rule execution engine)
```

Mỗi step độc lập đủ để frontend tích hợp thật. Step sau phụ thuộc step trước.

---

## Step 1 — Database Schema

### 1.1 Bảng cần tạo

```sql
-- Entity metadata (mô tả một loại dữ liệu tùy chỉnh)
CREATE TABLE custom_entity_definitions (
  id                BIGSERIAL PRIMARY KEY,
  entity_key        VARCHAR(80) NOT NULL UNIQUE,
  label             VARCHAR(255) NOT NULL,
  description       TEXT,
  page_type         VARCHAR(30) NOT NULL,           -- table_detail | record_list | form
  status            VARCHAR(20) NOT NULL DEFAULT 'Draft',
  version           INT NOT NULL DEFAULT 1,
  draft_version     INT NOT NULL DEFAULT 1,
  published_version INT NOT NULL DEFAULT 0,
  has_draft         BOOLEAN NOT NULL DEFAULT TRUE,
  etag              VARCHAR(100) NOT NULL,
  published_at      TIMESTAMPTZ,
  published_by      INT,
  created_by        INT NOT NULL,
  updated_by        INT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

-- Field definitions
CREATE TABLE custom_field_definitions (
  id                  BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT NOT NULL REFERENCES custom_entity_definitions(id),
  entity_key          VARCHAR(80) NOT NULL,
  field_key           VARCHAR(80) NOT NULL,
  label               VARCHAR(255) NOT NULL,
  field_type          VARCHAR(30) NOT NULL,
  required            BOOLEAN NOT NULL DEFAULT FALSE,
  filterable          BOOLEAN NOT NULL DEFAULT FALSE,
  sortable            BOOLEAN NOT NULL DEFAULT FALSE,
  searchable          BOOLEAN NOT NULL DEFAULT FALSE,
  read_only           BOOLEAN NOT NULL DEFAULT FALSE,
  hidden              BOOLEAN NOT NULL DEFAULT FALSE,
  field_order         INT NOT NULL DEFAULT 0,
  helper_text         TEXT,
  ref_type            VARCHAR(20),                  -- core | custom
  ref_entity_key      VARCHAR(80),
  options_json        JSONB,                        -- string[] cho single_select
  default_value       TEXT,
  validation_json     JSONB,                        -- {minLength, maxLength, min, max, pattern, message}
  conditional_json    JSONB,                        -- {sourceFieldKey, operator, value, effect}
  status              VARCHAR(20) NOT NULL DEFAULT 'Active',
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (entity_key, field_key)
);

-- View definitions (layout bảng và form)
CREATE TABLE custom_view_definitions (
  id                  BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT NOT NULL REFERENCES custom_entity_definitions(id),
  entity_key          VARCHAR(80) NOT NULL UNIQUE,
  list_columns_json   JSONB NOT NULL DEFAULT '[]',  -- BuilderViewColumn[]
  filter_fields_json  JSONB NOT NULL DEFAULT '[]',  -- string[]
  default_sort        VARCHAR(80),
  default_sort_dir    VARCHAR(4) DEFAULT 'asc',
  form_sections_json  JSONB NOT NULL DEFAULT '[]',  -- BuilderFormSection[]
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Permission assignments per entity
CREATE TABLE custom_entity_permissions (
  id              BIGSERIAL PRIMARY KEY,
  entity_key      VARCHAR(80) NOT NULL,
  action          VARCHAR(20) NOT NULL,             -- view | create | update | delete
  roles_json      JSONB NOT NULL DEFAULT '[]',      -- UserRole[]
  UNIQUE (entity_key, action)
);

-- Menu folders (nhóm menu cha trên sidebar)
CREATE TABLE custom_menu_folders (
  id                BIGSERIAL PRIMARY KEY,
  folder_key        VARCHAR(80) NOT NULL UNIQUE,
  label             VARCHAR(255) NOT NULL,
  description       TEXT,
  status            VARCHAR(20) NOT NULL DEFAULT 'Draft',
  sort_order        INT NOT NULL DEFAULT 0,
  roles_json        JSONB NOT NULL DEFAULT '[]',
  version           INT NOT NULL DEFAULT 1,
  draft_version     INT NOT NULL DEFAULT 1,
  published_version INT NOT NULL DEFAULT 0,
  has_draft         BOOLEAN NOT NULL DEFAULT TRUE,
  etag              VARCHAR(100) NOT NULL,
  published_at      TIMESTAMPTZ,
  published_by      INT,
  created_by        INT NOT NULL,
  updated_by        INT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ
);

-- Menu pages (giao diện menu con)
CREATE TABLE custom_menu_pages (
  id                  BIGSERIAL PRIMARY KEY,
  page_key            VARCHAR(80) NOT NULL UNIQUE,
  parent_key          VARCHAR(80) NOT NULL,
  label               VARCHAR(255) NOT NULL,
  description         TEXT,
  route_path          VARCHAR(255) NOT NULL,
  entity_key          VARCHAR(80) NOT NULL,
  page_type           VARCHAR(30) NOT NULL,
  status              VARCHAR(20) NOT NULL DEFAULT 'NeedsConfig',
  sort_order          INT NOT NULL DEFAULT 0,
  roles_json          JSONB NOT NULL DEFAULT '[]',
  entity_permission   VARCHAR(80),
  data_permission     VARCHAR(80),
  version             INT NOT NULL DEFAULT 1,
  draft_version       INT NOT NULL DEFAULT 1,
  published_version   INT NOT NULL DEFAULT 0,
  has_draft           BOOLEAN NOT NULL DEFAULT TRUE,
  etag                VARCHAR(100) NOT NULL,
  published_at        TIMESTAMPTZ,
  published_by        INT,
  created_by          INT NOT NULL,
  updated_by          INT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at          TIMESTAMPTZ
);

-- Custom records (dữ liệu thực tế)
CREATE TABLE custom_records (
  id                  BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT NOT NULL,
  entity_key          VARCHAR(80) NOT NULL,
  definition_version  INT NOT NULL,
  state_key           VARCHAR(80),
  values_json         JSONB NOT NULL DEFAULT '{}',
  search_text         TEXT,
  created_by          INT NOT NULL,
  updated_by          INT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at          TIMESTAMPTZ
);

-- Polymorphic reference index (impact check khi xóa master data)
CREATE TABLE custom_record_references (
  record_id       BIGINT NOT NULL,
  entity_key      VARCHAR(80) NOT NULL,
  field_key       VARCHAR(80) NOT NULL,
  ref_type        VARCHAR(20) NOT NULL,
  ref_entity_key  VARCHAR(80) NOT NULL,
  ref_id          BIGINT NOT NULL,
  reference_label TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit events cho definition changes
CREATE TABLE custom_definition_events (
  id          BIGSERIAL PRIMARY KEY,
  entity_key  VARCHAR(80) NOT NULL,
  action      VARCHAR(50) NOT NULL,
  actor_id    INT NOT NULL,
  payload     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit events cho record changes
CREATE TABLE custom_record_events (
  id          BIGSERIAL PRIMARY KEY,
  record_id   BIGINT NOT NULL,
  entity_key  VARCHAR(80) NOT NULL,
  action      VARCHAR(50) NOT NULL,
  actor_id    INT NOT NULL,
  payload     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 1.2 Indexes bắt buộc

```sql
-- Record list performance
CREATE INDEX idx_custom_records_entity_created
  ON custom_records(entity_key, created_at DESC, id DESC);
CREATE INDEX idx_custom_records_entity_state
  ON custom_records(entity_key, state_key, created_at DESC);
CREATE INDEX idx_custom_records_created_by
  ON custom_records(created_by, created_at DESC);
CREATE INDEX gin_custom_records_values
  ON custom_records USING gin(values_json);

-- Reference impact check
CREATE INDEX idx_custom_record_refs_target
  ON custom_record_references(ref_type, ref_entity_key, ref_id);

-- Menu tree
CREATE INDEX idx_custom_menu_folders_status
  ON custom_menu_folders(status, sort_order);
CREATE INDEX idx_custom_menu_pages_parent
  ON custom_menu_pages(parent_key, sort_order);
CREATE INDEX idx_custom_menu_pages_entity
  ON custom_menu_pages(entity_key);
```

### 1.3 Migration Flyway

Đặt tại `backend/smart-erp/src/main/resources/db/migration/V3__custom_builder_schema.sql`.

**Acceptance Step 1:**
- [ ] `V3__custom_builder_schema.sql` apply không có lỗi trên DB local
- [ ] Tất cả indexes được tạo
- [ ] Không có FK vòng, không alter bảng hiện tại

---

## Step 2 — RBAC: Thêm permissions mới vào JWT

### 2.1 Permissions mới

| Permission | Ý nghĩa |
|-----------|---------|
| `can_manage_custom_builder` | Owner/Admin có thể tạo/sửa/publish entity, folder, page |
| `can_use_custom_entities` | Mọi user có thể xem và dùng custom interface đã publish |

### 2.2 File cần sửa (backend)

- `backend/.../auth/support/MenuPermissionClaims.java` — thêm 2 constant
- `backend/.../auth/support/RolePermissionReader.java` — thêm mapping: Owner/Admin → `can_manage_custom_builder`; tất cả role → `can_use_custom_entities`
- JWT generation: thêm 2 permission vào `mp` claim

### 2.3 File cần sửa (frontend)

- `frontend/mini-erp/src/features/auth/types/menuPermissions.ts` — thêm 2 key vào type

### 2.4 Rule gán permission

| Role | `can_manage_custom_builder` | `can_use_custom_entities` |
|------|-----------------------------|--------------------------|
| Owner | ✅ | ✅ |
| Admin | ✅ | ✅ |
| Manager | ❌ | ✅ |
| Staff | ❌ | ✅ |
| Warehouse | ❌ | ✅ |

**Acceptance Step 2:**
- [ ] JWT sau khi login có `can_manage_custom_builder` cho Owner/Admin
- [ ] JWT có `can_use_custom_entities` cho tất cả role
- [ ] Frontend đọc được 2 permission từ JWT

---

## Step 3 — Entity + Field + View Foundation

**Scope:** CRUD draft cho entity metadata, field definitions, view layout. Chưa publish, chưa record.

### 3.1 API endpoints

| Method | Path | Permission | Mô tả |
|--------|------|-----------|-------|
| GET | `/api/v1/custom/entities` | `can_manage_custom_builder` | Danh sách entity (builder list page) |
| POST | `/api/v1/custom/entities` | `can_manage_custom_builder` | Tạo entity draft (wizard step 1) |
| GET | `/api/v1/custom/entities/{entityKey}` | `can_manage_custom_builder` | Lấy full bundle (edit settings) |
| PATCH | `/api/v1/custom/entities/{entityKey}` | `can_manage_custom_builder` | Cập nhật overview info |
| PUT | `/api/v1/custom/entities/{entityKey}/fields` | `can_manage_custom_builder` | Lưu toàn bộ fields |
| PUT | `/api/v1/custom/entities/{entityKey}/views` | `can_manage_custom_builder` | Lưu view layout |
| PUT | `/api/v1/custom/entities/{entityKey}/permissions` | Owner/Admin | Lưu permission roles |
| POST | `/api/v1/custom/entities/{entityKey}/publish` | Owner/Admin | Publish entity |
| POST | `/api/v1/custom/entities/{entityKey}/validate` | `can_manage_custom_builder` | Validate trước publish |

### 3.2 Response shape: GET /entities (list)

```json
[
  {
    "entityKey": "damaged_stock_report",
    "label": "Phiếu kiểm hàng hỏng",
    "pageType": "table_detail",
    "status": "Published",
    "fieldCount": 6,
    "version": 5,
    "hasDraft": true,
    "updatedAt": "2026-06-06T10:00:00Z",
    "updatedByName": "Admin"
  }
]
```

### 3.3 Response shape: GET /entities/{entityKey} (bundle)

Shape khớp với `BuilderPageBundle` trong mock adapter — backend trả toàn bộ: `entityDefinition`, `fields`, `views`, `permissions`, `workflow`, `logicConnector`, `validationSummary`, `etag`.

### 3.4 Validation khi save fields

1. `field_key`: lowercase + underscore, unique trong entity
2. `field_type`: phải nằm trong allowlist (`text`, `long_text`, `number`, `money`, `date`, `boolean`, `single_select`, `reference`, `line_items`)
3. Nếu `field_type = reference`: bắt buộc có `ref_type` và `ref_entity_key`
4. Nếu `ref_type = custom`: kiểm tra entity target tồn tại và đã published
5. `options_json` bắt buộc với `single_select`
6. Tối đa 50 fields per entity

### 3.5 Validation khi publish

1. Phải có ít nhất 1 field
2. Phải có ít nhất 1 field `required = true`
3. View có list_columns không rỗng
4. View có form_sections không rỗng
5. Tất cả fieldKey trong view tồn tại trong fields
6. Tạo immutable definition snapshot (tăng `published_version`)

### 3.6 etag conflict

- Mỗi save cập nhật `etag = UUID random hoặc hash(updated_at + version)`
- Client gửi `If-Match: <etag>` header
- Nếu không khớp → 409 Conflict

**Acceptance Step 3:**
- [ ] Tạo entity → xuất hiện trong danh sách với status `Draft`
- [ ] Lưu fields → GET bundle trả về đúng fields
- [ ] Publish với field thiếu required → 422 với validation errors
- [ ] Publish thành công → `status = Published`, `published_version` tăng
- [ ] Save đồng thời với etag cũ → 409
- [ ] Zero TypeScript errors khi frontend dùng response thật thay mock

---

## Step 4 — Menu Tree: Folder & Page Builder API

**Scope:** CRUD folder menu cha, page menu con, publish, runtime menu cho sidebar.

### 4.1 API endpoints

| Method | Path | Permission | Mô tả |
|--------|------|-----------|-------|
| GET | `/api/v1/custom/menu-tree` | `can_manage_custom_builder` | Builder menu tree (tất cả folder/page kể cả draft) |
| GET | `/api/v1/custom/runtime-menu` | `can_use_custom_entities` | Runtime menu (chỉ published, theo role user) |
| POST | `/api/v1/custom/menu-folders` | `can_manage_custom_builder` | Tạo folder |
| PATCH | `/api/v1/custom/menu-folders/{folderKey}` | `can_manage_custom_builder` | Cập nhật folder |
| POST | `/api/v1/custom/menu-folders/{folderKey}/publish` | Owner/Admin | Publish folder |
| DELETE | `/api/v1/custom/menu-folders/{folderKey}` | Owner/Admin | Archive folder |
| POST | `/api/v1/custom/menu-pages` | `can_manage_custom_builder` | Tạo page |
| PATCH | `/api/v1/custom/menu-pages/{pageKey}` | `can_manage_custom_builder` | Cập nhật page |
| POST | `/api/v1/custom/menu-pages/{pageKey}/publish` | Owner/Admin | Publish page |
| DELETE | `/api/v1/custom/menu-pages/{pageKey}` | Owner/Admin | Archive page |
| POST | `/api/v1/custom/menu/reorder` | `can_manage_custom_builder` | Lưu thứ tự |
| GET | `/api/v1/custom/pages/{pageKey}/runtime` | `can_use_custom_entities` | Runtime resolver cho `/custom/:pageKey` |

### 4.2 Runtime menu rules

GET `/api/v1/custom/runtime-menu` chỉ trả folder/page thỏa MỌI điều kiện:
1. `status = Published`
2. User có role nằm trong `roles_json` của folder VÀ page
3. Folder có ít nhất 1 child page thỏa điều kiện trên

### 4.3 Runtime page resolver

GET `/api/v1/custom/pages/{pageKey}/runtime`:
1. Tìm page theo `page_key`
2. Kiểm tra `status = Published` → không published: 404
3. Kiểm tra user permission → không có quyền: 403
4. Load entity definition (published version), field defs, view defs
5. Trả về `BuilderPageBundle` runtime-safe (không trả workflow draft, không trả connector draft)

### 4.4 Publish page validation

Page chỉ publish được khi:
1. `entity_key` tồn tại và entity đã published
2. Không có validation errors trong entity definition
3. `parent_key` folder tồn tại

### 4.5 Frontend integration

Khi Step 4 xong, frontend thay:
- `getMockBuilderMenuTree()` → gọi GET `/api/v1/custom/menu-tree`
- `getMockRuntimeCustomMenu()` → gọi GET `/api/v1/custom/runtime-menu`
- `createMockBuilderPage()` → gọi POST `/api/v1/custom/menu-pages`
- `saveMockBuilderPageBundle()` → gọi PATCH `/api/v1/custom/menu-pages/{pageKey}` + PUT fields/views

**Acceptance Step 4:**
- [ ] GET runtime-menu chỉ trả folder/page published đúng role
- [ ] Tạo folder → xuất hiện trong menu tree
- [ ] Tạo page → nằm dưới folder đúng parent
- [ ] Publish page khi entity chưa published → 422
- [ ] GET runtime-menu với Staff không có quyền → folder đó không hiện
- [ ] etag conflict khi 2 admin cùng sửa → 409

---

## Step 5 — Record CRUD (Runtime Workspace)

**Scope:** User tạo/xem/sửa/xóa record theo metadata entity đã publish.

### 5.1 API endpoints

| Method | Path | Permission | Mô tả |
|--------|------|-----------|-------|
| GET | `/api/v1/custom/entities/{entityKey}/records` | Entity read permission | Danh sách record phân trang |
| POST | `/api/v1/custom/entities/{entityKey}/records` | Entity create permission | Tạo record |
| GET | `/api/v1/custom/records/{recordId}` | Entity read permission | Chi tiết record |
| PATCH | `/api/v1/custom/records/{recordId}` | Entity edit permission | Cập nhật record |
| DELETE | `/api/v1/custom/records/{recordId}` | Entity delete permission | Soft delete |

### 5.2 List records

Query params:
- `page` (default 1), `limit` (default 20, max 50)
- `search` — tìm theo `search_text`
- `sort` — field key, chỉ field `sortable=true`
- `filter[fieldKey]` — chỉ field `filterable=true`
- `stateKey` — filter theo workflow state (Phase 2)

### 5.3 Validate save record

1. Load entity definition theo published version
2. Kiểm tra entity permission của user
3. Validate từng field: required, type, min/max, options, reference
4. Với field `reference`: resolve target entity/record tồn tại + user có quyền xem target
5. Normalize: date → ISO, number → Decimal, money → BigDecimal
6. Ghi `custom_records`
7. Refresh `custom_record_references`
8. Ghi `custom_record_events`

### 5.4 search_text generation

Khi save record, backend tự tổng hợp `search_text`:
```
{labelSnapshot của reference fields} {text fields} {single_select options}
```
Giúp full-text search mà không cần scan JSONB.

### 5.5 Polymorphic reference validation

Reference field phải validate:
- `refType=core`: kiểm tra entity `products`, `warehouse_locations`, `suppliers`, `customers`, `users` có record với `refId` đó không
- `refType=custom`: entity target phải có status `Published`, record target phải tồn tại và user có quyền đọc
- Nếu target soft-deleted: reject create/update, hiện `labelSnapshot` trong readonly display

**Acceptance Step 5:**
- [ ] Tạo record với field required bỏ trống → 400 với field-level error
- [ ] Tạo record với reference đến product không tồn tại → 400
- [ ] Danh sách record phân trang, không bao giờ trả `limit > 50`
- [ ] Search theo text hoạt động
- [ ] Filter theo filterable field hoạt động
- [ ] `search_text` được tổng hợp đúng

---

## Step 6 — Workflow

**Scope:** State machine cho custom records — state, transition, permission, audit.

### 6.1 Database (bổ sung từ Step 1)

```sql
CREATE TABLE custom_workflow_definitions (
  id            BIGSERIAL PRIMARY KEY,
  entity_key    VARCHAR(80) NOT NULL UNIQUE,
  enabled       BOOLEAN NOT NULL DEFAULT FALSE,
  states_json   JSONB NOT NULL DEFAULT '[]',      -- BuilderWorkflowState[]
  transitions_json JSONB NOT NULL DEFAULT '[]',   -- BuilderWorkflowTransition[]
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

(Gộp vào `V3__custom_builder_schema.sql` hoặc `V4__custom_builder_workflow.sql`)

### 6.2 API endpoints

| Method | Path | Permission | Mô tả |
|--------|------|-----------|-------|
| PUT | `/api/v1/custom/entities/{entityKey}/workflow` | `can_manage_custom_builder` | Lưu workflow draft |
| POST | `/api/v1/custom/records/{recordId}/transitions/{transitionKey}` | Transition permission | Thực thi transition |
| GET | `/api/v1/custom/records/{recordId}/events` | Entity read permission | Timeline audit |

### 6.3 Workflow validation khi publish

1. Phải có đúng 1 state `type = "start"`
2. Phải có ít nhất 1 state `type = "final"`
3. Tất cả `fromStateKey` và `toStateKey` trong transitions phải tồn tại trong states
4. Không có state nào orphaned (không có transition đến và không phải start)
5. State `type = "final"` không được có outbound transition

### 6.4 Transition execution

1. Load record + published workflow definition
2. Kiểm tra `current state_key` cho phép transition `transitionKey`
3. Kiểm tra user role có trong `transition.allowedRoles`
4. Execute transition: cập nhật `custom_records.state_key`
5. Ghi `custom_record_events` với action `TRANSITION`
6. Nếu workflow `enabled = false` trên published definition: transition bị từ chối

### 6.5 UI guardrails (backend enforce)

- Khi transition đang pending → backend xử lý idempotency (ghi nhận requestId)
- State `type = "final"`: record không cho edit (backend trả 403 cho PATCH)
- State có `lockEdit = true`: tương tự

**Acceptance Step 6:**
- [ ] Tạo workflow với 2 states thiếu start → 422
- [ ] Transition với role không có quyền → 403
- [ ] Transition thành công → `state_key` trong record cập nhật
- [ ] Record ở terminal state → PATCH trả 403
- [ ] Timeline events hiển thị đúng thứ tự

---

## Step 7 — Logic Connector

**Scope:** Rule execution engine cho custom business logic (copy/set/add/subtract/multiply/sumLines).

### 7.1 Database (bổ sung)

```sql
CREATE TABLE custom_logic_connectors (
  id              BIGSERIAL PRIMARY KEY,
  entity_key      VARCHAR(80) NOT NULL,
  connector_key   VARCHAR(80) NOT NULL,
  label           VARCHAR(255),
  enabled         BOOLEAN NOT NULL DEFAULT TRUE,
  trigger         VARCHAR(50) NOT NULL,         -- onCreate | onUpdate | onWorkflowTransition
  source_field_key VARCHAR(80) NOT NULL,
  operation       VARCHAR(30) NOT NULL,          -- copy | set | add | subtract | multiply | sumLines
  target_field_key VARCHAR(80) NOT NULL,
  value           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (entity_key, connector_key)
);

CREATE TABLE custom_connector_events (
  id              BIGSERIAL PRIMARY KEY,
  entity_key      VARCHAR(80) NOT NULL,
  connector_key   VARCHAR(80) NOT NULL,
  record_id       BIGINT,
  action          VARCHAR(20) NOT NULL,          -- dry_run | executed | failed
  payload         JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 7.2 API endpoints

| Method | Path | Permission | Mô tả |
|--------|------|-----------|-------|
| PUT | `/api/v1/custom/entities/{entityKey}/logic-connectors` | `can_manage_custom_builder` | Lưu toàn bộ rules |
| POST | `/api/v1/custom/entities/{entityKey}/logic-connectors/dry-run` | `can_manage_custom_builder` | Dry-run với sample record |
| POST | `/api/v1/custom/entities/{entityKey}/publish` | Owner/Admin | Publish bao gồm connector rules |

### 7.3 Operation allowlist

| Operation | Mô tả | Điều kiện |
|-----------|-------|----------|
| `copy` | Sao chép giá trị source → target | source và target cùng type |
| `set` | Ghi giá trị cố định vào target | value phải hợp lệ với target type |
| `add` | Cộng source + value vào target | field type phải number/money |
| `subtract` | Trừ source - value vào target | field type phải number/money |
| `multiply` | Nhân source × value → target | field type phải number/money |
| `sumLines` | Tổng line_items[].fieldKey → target | source phải là line_items |

**Không cho phép:** SQL injection qua `value`, cascade connector chains quá 3 level (cycle detection).

### 7.4 Cycle detection

Trước khi save connector rules:
1. Build dependency graph: `sourceField → targetField` cho mỗi rule
2. Detect cycle bằng DFS
3. Nếu có cycle → 422 với thông báo chain cụ thể

### 7.5 Execution flow

Khi record được save/transition:
1. Load active connector rules theo trigger (`onCreate`, `onUpdate`, `onWorkflowTransition`)
2. Execute từng rule theo thứ tự
3. Ghi kết quả vào `values_json` của record
4. Ghi `custom_connector_events` với action `executed`
5. Nếu bất kỳ rule nào fail: rollback toàn bộ transaction, ghi event `failed`

### 7.6 Dry-run

POST `/dry-run` nhận sample record, chạy toàn bộ rules nhưng **không ghi database**:
- Trả về: `{ sourceValue, targetBefore, targetAfter }` cho từng rule
- Không mutate bất kỳ bảng nào

**Acceptance Step 7:**
- [ ] Lưu rules với cycle (A→B→A) → 422
- [ ] Dry-run với sample record → trả đúng `targetBefore` ≠ `targetAfter`
- [ ] Operation `add` với field không phải number → 422
- [ ] Khi record được save với trigger `onCreate` → connector tự chạy
- [ ] Connector fail → record không được tạo (rollback)
- [ ] `custom_connector_events` ghi đúng `executed` hay `failed`

---

## 4. Tổng hợp: thứ tự và dependency

| Step | Tên | Phụ thuộc | Ưu tiên MVP |
|------|-----|----------|------------|
| 1 | Database Schema | Không | Bắt buộc |
| 2 | RBAC Permissions | Không | Bắt buộc |
| 3 | Entity + Field + View | Step 1, 2 | Bắt buộc |
| 4 | Menu Tree | Step 1, 2, 3 | Bắt buộc |
| 5 | Record CRUD | Step 3, 4 | Bắt buộc |
| 6 | Workflow | Step 3, 5 | Khuyến nghị |
| 7 | Logic Connector | Step 3, 5, 6 | Khuyến nghị |

Inventory Effect (Phase 4 trong program overview) và AI Copilot (Phase 5+) **ra khỏi scope MVP** — không implement trong đồ án.

---

## 5. Frontend integration checklist

Sau mỗi step, frontend xóa mock tương ứng trong `customBuilderMockAdapter.ts`:

| Step xong | Mock cần xóa / thay thế |
|-----------|------------------------|
| Step 3 | `getMockBuilderPageBundle`, `saveMockBuilderPageBundle` |
| Step 4 | `getMockBuilderMenuTree`, `getMockRuntimeCustomMenu`, `createMockBuilderPage` |
| Step 5 | `getMockRuntimePageBundle`, `getMockRecords`, `createMockRecord`, `updateMockRecord` |
| Step 6 | `executeMockTransition` |
| Step 7 | `runMockDryRun`, `saveMockLogicConnectors` |

---

## 6. Non-functional requirements

| Nhóm | Yêu cầu |
|------|---------|
| Security | Tất cả endpoint check permission server-side; không trust client-side role |
| Security | `values_json` không render như HTML unsafe |
| Idempotency | Tạo record idempotent với `client_request_id` header (Phase 7) |
| Performance | List records paginated, tối đa 50/request |
| Performance | GIN index trên `values_json` cho JSONB filter |
| Reliability | Connector execution atomic với record save |
| Audit | Mọi create/update/publish/transition ghi event |
| Conflict | Save với etag cũ → 409 |

---

## 7. Out of scope

- Inventory Effect Executor (Phase 4)
- AI Builder Copilot (Phase 5)
- AI Custom Query (Phase 6)
- AI Custom Draft (Phase 7)
- Attachment / file upload
- Custom report builder
- Drag-and-drop reorder persist (có thể dùng up/down buttons thay thế)
- Export async job
