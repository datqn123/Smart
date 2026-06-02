# SRS - Phase 1 Custom Entity / Record Foundation

> File: `docs/dev/common/002_custom-builder-phase1-entity-record-foundation.md`  
> Agent: SRS_WRITER  
> Ngay cap nhat: 02/06/2026  
> Trang thai: DRAFT_FOR_PO_REVIEW  
> Pham vi: Entity, field, view, record CRUD, polymorphic reference, query/scale nen tang.

---

## 1. Objective

Phase 1 tao nen mong metadata-driven cho custom builder:

- Owner/Admin tao entity draft.
- Cau hinh field va layout list/form.
- Publish definition version.
- User co quyen tao/xem/sua record theo metadata.
- Record luu trong `custom_records.values_json`.
- Polymorphic reference duoc validate va phuc vu impact check.

Phase nay chua lam workflow transition, connector, inventory effect va AI.

---

## 2. Data Model

### 2.1 Proposed Tables

| Nhom | Bang | Vai tro |
| :--- | :--- | :--- |
| Entity metadata | `custom_entity_definitions` | Entity key, name, status draft/published, version, permissions |
| Field metadata | `custom_field_definitions` | Field key, type, required, validation, order |
| View metadata | `custom_view_definitions` | List columns, form sections, display config |
| Record data | `custom_records` | Data records with `values_json` and system columns |
| Reference index | `custom_record_references` | Polymorphic reference index for impact check |
| Audit | `custom_record_events`, `custom_definition_events` | Timeline changes |

### 2.2 `custom_records`

```sql
custom_records:
  id                    BIGSERIAL PRIMARY KEY
  entity_id             BIGINT NOT NULL
  entity_key            VARCHAR(80) NOT NULL
  definition_version    INT NOT NULL
  state_key             VARCHAR(80)
  values_json           JSONB NOT NULL
  search_text           TEXT
  created_by            INT NOT NULL
  updated_by            INT
  created_at            TIMESTAMPTZ NOT NULL
  updated_at            TIMESTAMPTZ NOT NULL
  deleted_at            TIMESTAMPTZ
```

`state_key` duoc de san cho Phase 2; Phase 1 co the set mac dinh `Draft` hoac null theo Tech Spec.

### 2.3 Record Example

```json
{
  "entityKey": "damaged_stock_report",
  "definitionVersion": 3,
  "values": {
    "product": {
      "refType": "core",
      "refEntityKey": "products",
      "refId": 12,
      "labelSnapshot": "SP-00012 - Sua tuoi"
    },
    "location": {
      "refType": "core",
      "refEntityKey": "warehouse_locations",
      "refId": 3,
      "labelSnapshot": "Kho A / Ke 01"
    },
    "quantity": 5,
    "reason": "Vo trong qua trinh van chuyen",
    "reportedDate": "2026-06-02"
  }
}
```

---

## 3. Field Types

| Type | Meaning | Note |
| :--- | :--- | :--- |
| `text` | Short text | max length |
| `long_text` | Long note | textarea |
| `number` | Numeric | min/max/integer |
| `money` | Money | decimal backend |
| `date` | Date | ISO date |
| `datetime` | Date time | ISO datetime |
| `boolean` | Boolean | toggle |
| `single_select` | One option | fixed option list |
| `reference` | Polymorphic reference | `{refType, refEntityKey, refId, labelSnapshot}` |
| `product_ref` | Alias of `reference` | `core/products` |
| `location_ref` | Alias of `reference` | `core/warehouse_locations` |
| `supplier_ref` | Alias of `reference` | `core/suppliers` |
| `customer_ref` | Alias of `reference` | `core/customers` |
| `user_ref` | Alias of `reference` | `core/users` |
| `custom_entity_ref` | Alias of `reference` | `custom/<entityKey>` |
| `line_items` | Bounded child rows | used by later connector/effect phases |

Backend must normalize alias refs to canonical `reference`.

Default MVP limit: `line_items <= 100` rows per record unless Tech Spec chooses another limit.

---

## 4. Polymorphic Reference

Canonical shape:

```json
{
  "refType": "core",
  "refEntityKey": "products",
  "refId": 12,
  "labelSnapshot": "SP-00012 - Sua tuoi"
}
```

Rules:

- `refType=core`: target is backend-known master data.
- `refType=custom`: target is a published custom entity.
- Backend resolves target existence and permission on create/update.
- `labelSnapshot` is display/history only, never a business key.
- Archive/delete/merge target data must impact-check `custom_record_references`.

Reference index:

```sql
custom_record_references:
  record_id       BIGINT NOT NULL
  entity_key      VARCHAR(80) NOT NULL
  field_key       VARCHAR(80) NOT NULL
  ref_type        VARCHAR(20) NOT NULL
  ref_entity_key  VARCHAR(80) NOT NULL
  ref_id          BIGINT NOT NULL
  reference_label TEXT
  created_at      TIMESTAMPTZ NOT NULL
```

Recommended index:

```sql
CREATE INDEX idx_custom_record_refs_target
ON custom_record_references(ref_type, ref_entity_key, ref_id);
```

---

## 5. API Contract

| Method | Path | Permission | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `/api/v1/custom/entities` | `can_use_custom_entities` or builder permission | List entity definitions |
| POST | `/api/v1/custom/entities` | `can_manage_custom_builder` | Create entity draft |
| GET | `/api/v1/custom/entities/{entityKey}` | Entity read permission | Get definition |
| PATCH | `/api/v1/custom/entities/{entityKey}` | `can_manage_custom_builder` | Update metadata |
| PUT | `/api/v1/custom/entities/{entityKey}/fields` | `can_manage_custom_builder` | Save fields |
| PUT | `/api/v1/custom/entities/{entityKey}/views` | `can_manage_custom_builder` | Save layout |
| POST | `/api/v1/custom/entities/{entityKey}/publish` | Owner/Admin | Publish new version |
| GET | `/api/v1/custom/entities/{entityKey}/records` | Entity read permission | Paginated record list |
| POST | `/api/v1/custom/entities/{entityKey}/records` | Entity create permission | Create record |
| GET | `/api/v1/custom/records/{recordId}` | Entity read permission | Record detail |
| PATCH | `/api/v1/custom/records/{recordId}` | Entity edit permission | Update record |

---

## 6. Validation

### 6.1 Publish Definition

1. Validate `entity_key`: lowercase, number, underscore, unique.
2. Validate fields: unique key, type in allowlist, required label, validation JSON.
3. Validate view: list/form fields exist.
4. Validate reference config: ref target type/entity valid.
5. Create immutable `definition_version`.

### 6.2 Save Record

1. Load definition by entity/version.
2. Check entity permission.
3. Validate required/type/min/max/options/reference.
4. Normalize dates/numbers/money/reference.
5. Write `custom_records`.
6. Refresh `custom_record_references`.
7. Write `custom_record_events`.

---

## 7. Performance / Scale

Minimum indexes:

| Index | Purpose |
| :--- | :--- |
| `custom_records(entity_key, created_at DESC, id DESC)` | List |
| `custom_records(entity_key, state_key, created_at DESC)` | Future workflow list |
| `custom_records(created_by, created_at DESC)` | My records |
| GIN `custom_records(values_json)` | Basic JSONB filters |
| `custom_record_references(ref_type, ref_entity_key, ref_id)` | Impact check |

Rules:

- All list APIs are paginated.
- Default `limit <= 50`, backend max `limit <= 100`.
- Search uses `search_text`, not full JSONB scan.
- Only `filterable=true` fields appear in advanced filters.
- API export du lieu lon phai chay async job o phase sau, khong tai truc tiep qua list request.

### 7.1 Scale Thresholds

| Nguong | Phuong an | Ghi chu |
| :--- | :--- | :--- |
| Duoi 100k records/entity | `custom_records` + B-tree + GIN JSONB | Du cho MVP |
| 100k - 1M | Them `custom_record_field_index` cho field filter/sort pho bien | Giam query JSONB |
| 1M - 10M | Partition theo `entity_key` hoac thoi gian | Tech Spec chot theo workload |
| Tren 10M | Read replica, materialized/report table, async export | UI khong query thang raw data lon |

### 7.2 Field Index Table

```sql
custom_record_field_index:
  record_id     BIGINT NOT NULL
  entity_key    VARCHAR(80) NOT NULL
  field_key     VARCHAR(80) NOT NULL
  value_text    TEXT
  value_number  NUMERIC
  value_date    DATE
  value_bool    BOOLEAN
  created_at    TIMESTAMPTZ NOT NULL
```

Rules:

- Backend chi ghi index phu cho field `filterable=true`, `sortable=true`, hoac `searchBoost=true`.
- MVP toi da 5 field `filterable=true` hoac `sortable=true` per entity, khong tinh system fields.
- Khi record update, field index phai update trong cung transaction.
- Khi bat index cho field sau khi da co du lieu, dung reindex job; khong reindex toan bo trong request publish.

### 7.3 Cache / Metadata

- Backend cache entity/field/view definitions theo `entity_key + version`.
- Cache invalidate khi publish definition moi.
- Frontend cache metadata bang TanStack Query; record list cache theo `entityKey + filters + sort + page`.
- AI schema metadata cache dung fingerprint/version de tranh doc schema custom cu.

### 7.4 Observability

- Log slow query cho custom record list.
- Theo doi record count theo `entity_key`.
- Theo doi ty le JSONB scan.
- Canh bao khi entity vuot nguong can index phu.
- Builder UI canh bao khi Owner/Admin bat filter/sort cho field chua co index.

---

## 8. Frontend Scope

Routes:

| Route | Page |
| :--- | :--- |
| `/settings/custom-builder` | Custom builder |
| `/custom` | Custom workspace |
| `/custom/:entityKey` | Record list |
| modal or `/custom/:entityKey/:recordId` | Record detail |

Tabs in builder for Phase 1:

- Thong tin.
- Truong du lieu.
- Giao dien.
- Kiem thu record mau.

UI guardrails:

- Disable save/publish while pending.
- Inline validation errors.
- No optimistic update after publish.
- Refetch metadata after publish.

---

## 9. Acceptance Criteria

```gherkin
Given Owner tao entity "Phieu kiem hang hong"
When Owner them field product, location, quantity, reason
And publish entity
Then Staff co quyen co the tao record tu form dong
And record xuat hien trong workspace tuy chinh
```

```gherkin
Given custom record dang tham chieu product id 12
When Owner co xoa vat ly product id 12
Then backend chan thao tac hoac yeu cau archive/soft delete
And record custom van hien thi duoc snapshot label lich su
```

## 10. Test Plan

| Test | Expected |
| :--- | :--- |
| Create entity duplicate key | 409 |
| Publish empty fields | 422 |
| Record missing required field | 400 field-level |
| Reference to inactive/deleted core target | Reject |
| Reference to unpublished custom entity | Reject |
| Paginated list | No endpoint returns all records |
| Field filter limit exceeded | Reject or require scale review |

SRS handoff state: `READY_FOR_TECH_SPEC`.
