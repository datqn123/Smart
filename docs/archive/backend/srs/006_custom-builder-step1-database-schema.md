# SRS-BE-006 — Custom Builder Step 1: Database Schema Foundation

> File: `docs/backend/srs/006_custom-builder-step1-database-schema.md`
> Agent: SRS_WRITER
> Ngày tạo: 2026-06-06
> Trạng thái: READY_FOR_TECH_SPEC
> Phạm vi: PostgreSQL schema, 10 bảng + indexes + Flyway migration cho Custom Builder MVP

---

## 1. Tổng quan

**Mục tiêu:** Xây dựng schema PostgreSQL để lưu trữ metadata và dữ liệu của Custom Builder backend, cho phép tạo/quản lý entity tùy chỉnh, field definitions, view layouts, menu tree, và records.

**Phạm vi quyết định:**
- KHÔNG thay đổi schema hiện tại (bảng core như products, customers, users)
- KHÔNG dùng JPA/Hibernate — JDBC Repository pattern
- Schema phải hỗ trợ versioning (draft/published) cho entity, folder, page
- Schema phải hỗ trợ audit events cho tất cả thay đổi

**Tài liệu gốc tham chiếu:**
- `docs/dev/common/001_custom-builder-program-overview.md` — program principles
- `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md` — data model
- `docs/backend/srs/005_custom-builder-backend-roadmap.md` — Step 1 requirement

---

## 2. Yêu cầu chức năng

### 2.1 Metadata storage — Entity + Field + View

| Bảng | Mục đích | Khóa chính | Constraint |
|------|---------|-----------|-----------|
| `custom_entity_definitions` | Mô tả loại entity tùy chỉnh | `id` | `entity_key` UNIQUE |
| `custom_field_definitions` | Định nghĩa field trong entity | `id` | `(entity_key, field_key)` UNIQUE |
| `custom_view_definitions` | Layout bảng/form cho entity | `id` | `entity_key` UNIQUE |
| `custom_entity_permissions` | Permission rules per entity/action | `id` | `(entity_key, action)` UNIQUE |

**Lý do 4 bảng riêng:** Phân tách concerns — entity là container, field là definition, view là presentation, permission là policy.

### 2.2 Menu tree — Folder + Page

| Bảng | Mục đích | Khóa chính | Constraint |
|------|---------|-----------|-----------|
| `custom_menu_folders` | Nhóm menu cha (sidebar folder) | `id` | `folder_key` UNIQUE |
| `custom_menu_pages` | Menu con (actual page) | `id` | `page_key` UNIQUE |

**Lý do 2 bảng riêng:** Folder có versioning (draft/published), page cũng có. Mỗi page dùng `parent_key` foreign key tới folder.

### 2.3 Runtime records — Custom Records + References

| Bảng | Mục đích | Khóa chính | Constraint |
|------|---------|-----------|-----------|
| `custom_records` | Dữ liệu thực tế của custom entity | `id` | Relation to entity via `entity_key` |
| `custom_record_references` | Index polymorphic references | Composite | (record_id, field_key, ref_id) |

**Lý do:** Reference index giúp impact check nhanh khi xóa master data. JSONB `values_json` lưu dữ liệu, nhưng cần index riêng cho reference resolution.

### 2.4 Audit events — Definition + Record events

| Bảng | Mục đích | Khóa chính | Retention |
|------|---------|-----------|-----------|
| `custom_definition_events` | Audit cho entity/field/view changes | `id` | Keep forever (compliance) |
| `custom_record_events` | Audit cho record CRUD + transitions | `id` | Keep forever (compliance) |

**Lý do:** Metadata thay đổi (entity definition) phải audit tách từ record data changes.

---

## 3. Chi tiết schema SQL

### 3.1 Entity Definitions

```sql
CREATE TABLE custom_entity_definitions (
  id                BIGSERIAL PRIMARY KEY,
  entity_key        VARCHAR(80) NOT NULL UNIQUE,
  label             VARCHAR(255) NOT NULL,
  description       TEXT,
  page_type         VARCHAR(30) NOT NULL,           
                    -- Enum: table_detail | record_list | form
  status            VARCHAR(20) NOT NULL DEFAULT 'Draft',
                    -- Draft | Published | Archived
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
```

**Giải thích:**
- `entity_key`: Unique identifier (e.g. `damaged_stock_report`), dùng để reference trong API
- `page_type`: UI type — table với detail, record list, hoặc form-only
- `draft_version` vs `published_version`: Track draft độc lập từ published
- `has_draft`: Flag để UI biết có draft edit chưa save hay không
- `etag`: UUID hoặc hash(updated_at+version) để conflict detection
- `deleted_at`: Soft delete

### 3.2 Field Definitions

```sql
CREATE TABLE custom_field_definitions (
  id                  BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT NOT NULL REFERENCES custom_entity_definitions(id),
  entity_key          VARCHAR(80) NOT NULL,
  field_key           VARCHAR(80) NOT NULL,
  label               VARCHAR(255) NOT NULL,
  field_type          VARCHAR(30) NOT NULL,
                      -- Enum: text, long_text, number, money, date, boolean,
                      --       single_select, reference, line_items
  required            BOOLEAN NOT NULL DEFAULT FALSE,
  filterable          BOOLEAN NOT NULL DEFAULT FALSE,
  sortable            BOOLEAN NOT NULL DEFAULT FALSE,
  searchable          BOOLEAN NOT NULL DEFAULT FALSE,
  read_only           BOOLEAN NOT NULL DEFAULT FALSE,
  hidden              BOOLEAN NOT NULL DEFAULT FALSE,
  field_order         INT NOT NULL DEFAULT 0,
  helper_text         TEXT,
  ref_type            VARCHAR(20),                  
                      -- core | custom (cho reference field)
  ref_entity_key      VARCHAR(80),
  options_json        JSONB,                        
                      -- Single_select: ["option1", "option2"]
  default_value       TEXT,
  validation_json     JSONB,                        
                      -- {minLength, maxLength, min, max, pattern, message}
  conditional_json    JSONB,                        
                      -- {sourceFieldKey, operator, value, effect}
  status              VARCHAR(20) NOT NULL DEFAULT 'Active',
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (entity_key, field_key)
);
```

**Giải thích:**
- `REFERENCES custom_entity_definitions(id)`: Foreign key tới entity
- `(entity_key, field_key)` UNIQUE: Ensure không duplicate field key trong entity
- `field_type` allowlist: text, long_text, number, money, date, boolean, single_select, reference, line_items
- `ref_type`, `ref_entity_key`: Config cho reference field (có thể trỏ tới core entity hoặc custom entity)
- `options_json`: Cho single_select — JSON array string values
- `validation_json`, `conditional_json`: JSONB config objects

### 3.3 View Definitions

```sql
CREATE TABLE custom_view_definitions (
  id                  BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT NOT NULL REFERENCES custom_entity_definitions(id),
  entity_key          VARCHAR(80) NOT NULL UNIQUE,
  list_columns_json   JSONB NOT NULL DEFAULT '[]',
                      -- BuilderViewColumn[]
  filter_fields_json  JSONB NOT NULL DEFAULT '[]',
                      -- string[] — field keys filterable
  default_sort        VARCHAR(80),
  default_sort_dir    VARCHAR(4) DEFAULT 'asc',
  form_sections_json  JSONB NOT NULL DEFAULT '[]',
                      -- BuilderFormSection[]
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Giải thích:**
- Minimal metadata — chỉ lưu layout config
- `list_columns_json`: Array of {fieldKey, label, width, ...}
- `filter_fields_json`: Whitelist field keys mà user có thể filter
- `form_sections_json`: Array of {title, fieldKeys: [...]}

### 3.4 Entity Permissions

```sql
CREATE TABLE custom_entity_permissions (
  id              BIGSERIAL PRIMARY KEY,
  entity_key      VARCHAR(80) NOT NULL,
  action          VARCHAR(20) NOT NULL,
                  -- Enum: view | create | update | delete
  roles_json      JSONB NOT NULL DEFAULT '[]',
                  -- ["Owner", "Admin", "Manager"]
  UNIQUE (entity_key, action)
);
```

**Giải thích:**
- Per-entity permission control (RBAC)
- `roles_json`: Array of role strings allowed to perform `action`

### 3.5 Menu Folders

```sql
CREATE TABLE custom_menu_folders (
  id                BIGSERIAL PRIMARY KEY,
  folder_key        VARCHAR(80) NOT NULL UNIQUE,
  label             VARCHAR(255) NOT NULL,
  description       TEXT,
  status            VARCHAR(20) NOT NULL DEFAULT 'Draft',
  sort_order        INT NOT NULL DEFAULT 0,
  roles_json        JSONB NOT NULL DEFAULT '[]',
                    -- Roles visible folder
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
```

**Giải thích:**
- `folder_key`: Unique sidebar folder identifier
- `sort_order`: Menu tree ordering
- `roles_json`: Whitelist of roles that see this folder
- Versioning fields (`draft_version`, `published_version`) cho draft/publish cycle

### 3.6 Menu Pages

```sql
CREATE TABLE custom_menu_pages (
  id                  BIGSERIAL PRIMARY KEY,
  page_key            VARCHAR(80) NOT NULL UNIQUE,
  parent_key          VARCHAR(80) NOT NULL,
                      -- Foreign key to custom_menu_folders.folder_key
  label               VARCHAR(255) NOT NULL,
  description         TEXT,
  route_path          VARCHAR(255) NOT NULL,
  entity_key          VARCHAR(80) NOT NULL,
                      -- Link to custom_entity_definitions.entity_key
  page_type           VARCHAR(30) NOT NULL,
                      -- table_detail | record_list | form
  status              VARCHAR(20) NOT NULL DEFAULT 'NeedsConfig',
                      -- NeedsConfig | ReadyToPublish | Published | Archived
  sort_order          INT NOT NULL DEFAULT 0,
  roles_json          JSONB NOT NULL DEFAULT '[]',
                      -- Roles visible page
  entity_permission   VARCHAR(80),
                      -- Reference to permission action (optional)
  data_permission     VARCHAR(80),
                      -- Reference to row-level permission rule (Phase 2)
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
```

**Giải thích:**
- `parent_key`: Reference tới `custom_menu_folders.folder_key` (không foreign key vì folder_key là VARCHAR, không BIGINT)
- `entity_key`: Tên entity mà page này display
- `route_path`: Actual URL path (e.g. `/custom/damaged-stock-report`)
- `entity_permission`, `data_permission`: Reference tới permission rules (Phase 2 enhancement)

### 3.7 Custom Records

```sql
CREATE TABLE custom_records (
  id                  BIGSERIAL PRIMARY KEY,
  entity_id           BIGINT NOT NULL,
  entity_key          VARCHAR(80) NOT NULL,
  definition_version  INT NOT NULL,
                      -- Version của entity definition khi record tạo
  state_key           VARCHAR(80),
                      -- Current workflow state (Phase 2)
  values_json         JSONB NOT NULL DEFAULT '{}',
                      -- {fieldKey: value, ...} tất cả field values
  search_text         TEXT,
                      -- Synthesized search index
  created_by          INT NOT NULL,
  updated_by          INT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at          TIMESTAMPTZ
);
```

**Giải thích:**
- `definition_version`: Immutable version reference — record giữ snapshot của schema nó tạo với
- `values_json`: JSONB object lưu tất cả field values (flexibility, denormalized)
- `search_text`: Synthesized full-text index field (tối ưu search query)
- `state_key`: Placeholder cho workflow state (Phase 2)

### 3.8 Record References (Polymorphic index)

```sql
CREATE TABLE custom_record_references (
  record_id       BIGINT NOT NULL,
  entity_key      VARCHAR(80) NOT NULL,
  field_key       VARCHAR(80) NOT NULL,
  ref_type        VARCHAR(20) NOT NULL,
                  -- core | custom
  ref_entity_key  VARCHAR(80) NOT NULL,
  ref_id          BIGINT NOT NULL,
  reference_label TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Giải thích:**
- Polymorphic index để resolve references nhanh
- Dùng cho: impact check khi delete master data, label display
- Composite key: (record_id, field_key, ref_id)

### 3.9 Definition Events (Audit)

```sql
CREATE TABLE custom_definition_events (
  id          BIGSERIAL PRIMARY KEY,
  entity_key  VARCHAR(80) NOT NULL,
  action      VARCHAR(50) NOT NULL,
              -- CREATE_ENTITY | UPDATE_FIELD | PUBLISH_ENTITY | etc.
  actor_id    INT NOT NULL,
  payload     JSONB,
              -- {before: {...}, after: {...}} or context
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.10 Record Events (Audit)

```sql
CREATE TABLE custom_record_events (
  id          BIGSERIAL PRIMARY KEY,
  record_id   BIGINT NOT NULL,
  entity_key  VARCHAR(80) NOT NULL,
  action      VARCHAR(50) NOT NULL,
              -- CREATE_RECORD | UPDATE_RECORD | TRANSITION | etc.
  actor_id    INT NOT NULL,
  payload     JSONB,
              -- {before: {...}, after: {...}} or changes
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 4. Indexes (Performance)

### 4.1 Record list & search

```sql
CREATE INDEX idx_custom_records_entity_created
  ON custom_records(entity_key, created_at DESC, id DESC);
CREATE INDEX idx_custom_records_entity_state
  ON custom_records(entity_key, state_key, created_at DESC);
CREATE INDEX idx_custom_records_created_by
  ON custom_records(created_by, created_at DESC);
CREATE INDEX gin_custom_records_values
  ON custom_records USING gin(values_json);
```

**Lý do:**
- `idx_custom_records_entity_created`: List records by entity + pagination
- `idx_custom_records_entity_state`: Filter by workflow state (Phase 2)
- `idx_custom_records_created_by`: My records filter
- GIN index: JSONB filter/search (`values_json` queries)

### 4.2 Reference resolution

```sql
CREATE INDEX idx_custom_record_refs_target
  ON custom_record_references(ref_type, ref_entity_key, ref_id);
```

**Lý do:** Impact check khi xóa core/custom entity — tìm tất cả record references tới target nhanh.

### 4.3 Menu tree

```sql
CREATE INDEX idx_custom_menu_folders_status
  ON custom_menu_folders(status, sort_order);
CREATE INDEX idx_custom_menu_pages_parent
  ON custom_menu_pages(parent_key, sort_order);
CREATE INDEX idx_custom_menu_pages_entity
  ON custom_menu_pages(entity_key);
```

**Lý do:**
- `idx_custom_menu_folders_status`: Get published folders for menu tree
- `idx_custom_menu_pages_parent`: Get child pages of folder
- `idx_custom_menu_pages_entity`: Resolve page by entity

---

## 5. Migration & Deployment

### 5.1 Flyway script location

```
backend/smart-erp/src/main/resources/db/migration/V3__custom_builder_schema.sql
```

**Naming rule:** V3 (vì schema migration thứ 3 của project)

### 5.2 Content

Script sẽ bao gồm:
1. `CREATE TABLE` cho 10 bảng (theo SQL ở section 3)
2. `CREATE INDEX` cho tất cả indexes (theo section 4)
3. Không có `ALTER TABLE` thay đổi existing tables
4. Không có circular foreign keys

### 5.3 Execution environment

- Target: PostgreSQL 12+
- Encoding: UTF-8
- Transaction: Single transaction (rollback on any error)
- Idempotent: FALSE (Flyway tự handle)

---

## 6. Constraints & Validations (Database Level)

### 6.1 NOT NULL constraints

- Tất cả `*_key` columns NOT NULL (identifier stability)
- Tất cả `created_by`, `created_at` NOT NULL (audit requirement)
- Tất cả `status` NOT NULL (state clarity)

### 6.2 UNIQUE constraints

| Table | Column(s) | Reason |
|-------|-----------|--------|
| `custom_entity_definitions` | `entity_key` | API routing key |
| `custom_field_definitions` | `(entity_key, field_key)` | Field identifier per entity |
| `custom_view_definitions` | `entity_key` | One layout per entity |
| `custom_entity_permissions` | `(entity_key, action)` | Permission rule per action |
| `custom_menu_folders` | `folder_key` | Menu identifier |
| `custom_menu_pages` | `page_key` | Page identifier |
| `custom_record_references` | Composite (see 3.8) | Reference uniqueness |

### 6.3 Check constraints (Optional — enforced in app)

- `entity_key` matches pattern `^[a-z0-9_]{1,80}$`
- `field_key` matches pattern `^[a-z0-9_]{1,80}$`
- `page_type` IN ('table_detail', 'record_list', 'form')
- `field_type` IN ('text', 'long_text', 'number', 'money', 'date', 'boolean', 'single_select', 'reference', 'line_items')

---

## 7. Data Consistency Rules

### 7.1 Field definition constraints

- `field_key` phải lowercase + underscore
- `field_key` unique per entity
- Nếu `field_type = 'reference'` → bắt buộc `ref_type` + `ref_entity_key`
- Nếu `field_type = 'single_select'` → bắt buộc `options_json` (non-empty array)
- Max 50 fields per entity

**Enforcement:** Backend validation trước INSERT/UPDATE

### 7.2 Entity publish validation

- Phải có ít nhất 1 field (checked before publish)
- Phải có ít nhất 1 required field (checked before publish)
- View list_columns không rỗng (checked before publish)
- View form_sections không rỗng (checked before publish)

**Enforcement:** Backend validation + application logic

### 7.3 Menu folder/page consistency

- Page `parent_key` phải tồn tại trong `custom_menu_folders.folder_key`
- Page `entity_key` phải tồn tại trong `custom_entity_definitions.entity_key`
- Page `entity_key` phải có `status = 'Published'` (checked before page publish)

**Enforcement:** Backend validation + application logic

---

## 8. Non-functional Requirements

### 8.1 Performance

- List records endpoint (100 records) < 500ms
- GIN index cho JSONB filter: <100ms
- Reference resolution (impact check) < 200ms
- Menu tree build < 100ms

**Targets:** Reasonable for MVP, no async batch required

### 8.2 Data volume expectations

- MVP: <10K records per entity (soft limit)
- MVP: <100 custom entities
- MVP: <1K menu items total

**Growth:** Indexes designed to scale to 1M records per entity

### 8.3 Backup & Recovery

- PostgreSQL native backup (pg_dump)
- No special schema considerations for recovery
- Soft-deleted records (deleted_at NOT NULL) must be excluded from restore purges

---

## 9. Acceptance Criteria

- [ ] **Step 1.1** — Migration script tạo được trên DB local không có lỗi
- [ ] **Step 1.2** — Tất cả 10 bảng được tạo (verify `SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'`)
- [ ] **Step 1.3** — Tất cả 7 indexes được tạo (verify `\di` trong psql)
- [ ] **Step 1.4** — Không có foreign key circular (graph acyclic check)
- [ ] **Step 1.5** — Không có ALTER TABLE existing tables (verify script)
- [ ] **Step 1.6** — `etag` VARCHAR(100) hoặc tương đương cho conflict detection

---

## 10. Out of Scope

- Audit retention policy (handled by Operations)
- Schema versioning beyond Flyway
- Sharding strategy (single PostgreSQL instance)
- Read replicas (handled at infra level)
- Full-text search engine (PostgreSQL GIN sufficient for MVP)

---

## 11. References & Links

- **SRS Roadmap:** `docs/backend/srs/005_custom-builder-backend-roadmap.md`
- **Program Overview:** `docs/dev/common/001_custom-builder-program-overview.md`
- **Data Model:** `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md`
- **Frontend Mock Contract:** `frontend/mini-erp/src/features/custom-builder/api/customBuilderMockAdapter.ts`

---

## 12. Sign-off & Status

| Role | Name | Date | Status |
|------|------|------|--------|
| SRS Author | Claude Code | 2026-06-06 | READY_FOR_TECH_SPEC |
| Tech Lead Review | (pending) | - | PENDING |

**Next Step:** `TECH_SPEC_WRITER` soạn handoff coding từ SRS này → detail implementation tasks, JDBC repository contract, validation layer.
