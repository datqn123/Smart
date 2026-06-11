# Custom Builder MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current fixture-backed custom-builder into a production MVP with persisted metadata, publish snapshots, runtime menu/page rendering, and JSONB-backed custom records.

**Architecture:** Keep `custom_menu_folders` and `custom_menu_pages` as navigation. Add custom entity metadata tables, immutable published snapshots, and `custom_records` JSONB storage. Backend becomes the source of truth; frontend swaps mock adapter calls for typed API calls while preserving the existing builder/runtime UI shape.

**Tech Stack:** Spring Boot 3.5, Java 21 records/services/JdbcTemplate, PostgreSQL JSONB/Flyway, React 19, TypeScript, Vite, Vitest, Playwright.

---

## Source Spec

Read first: `docs/superpowers/specs/2026-06-11-custom-builder-mvp-design.md`

## File Structure

Backend files to create:

- `backend/smart-erp/src/main/resources/db/migration/V59__custom_builder_mvp_entities_records.sql`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/dto/CustomBuilderBundleRequest.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/dto/CustomFieldRequest.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/dto/CustomViewRequest.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/dto/CustomPermissionRequest.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/dto/CustomRecordRequest.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomBuilderBundleData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomEntityData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomFieldData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomViewData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomPermissionData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomRecordData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response/CustomRecordPageData.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/repository/CustomEntityJdbcRepository.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/repository/CustomRecordJdbcRepository.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomMetadataValidator.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomBuilderService.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomRecordService.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/controller/CustomBuilderController.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/controller/CustomRecordController.java`
- `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomMetadataValidatorTest.java`
- `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomRecordServiceTest.java`
- `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/controller/CustomBuilderControllerWebMvcTest.java`
- `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/controller/CustomRecordControllerWebMvcTest.java`

Backend files to modify:

- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/controller/CustomInterfaceController.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomInterfaceService.java`
- `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/repository/CustomInterfaceJdbcRepository.java`

Frontend files to create:

- `frontend/mini-erp/src/features/custom-builder/api/customBuilderTypes.ts`
- `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.test.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.test.tsx`

Frontend files to modify:

- `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx`
- `frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx`
- `frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts`
- `frontend/mini-erp/src/components/shared/layout/Sidebar.tsx`

E2E files to create:

- `frontend/mini-erp/e2e/custom-builder-mvp.spec.ts`

---

## Task 1: Database Schema And Seed Backfill

**Files:**
- Create: `backend/smart-erp/src/main/resources/db/migration/V59__custom_builder_mvp_entities_records.sql`
- Verify with: `./mvnw -q -DskipTests compile` from `backend/smart-erp`

- [ ] **Step 1: Create Flyway migration**

Create `V59__custom_builder_mvp_entities_records.sql` with this content:

```sql
CREATE TABLE IF NOT EXISTS custom_entities (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'NeedsConfig',
    draft_version INT NOT NULL DEFAULT 1,
    published_version INT,
    etag VARCHAR(160) NOT NULL,
    created_by INT NOT NULL,
    updated_by INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS custom_entity_fields (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    field_key VARCHAR(80) NOT NULL,
    label VARCHAR(160) NOT NULL,
    field_type VARCHAR(40) NOT NULL,
    required BOOLEAN NOT NULL DEFAULT FALSE,
    filterable BOOLEAN NOT NULL DEFAULT FALSE,
    sortable BOOLEAN NOT NULL DEFAULT FALSE,
    searchable BOOLEAN NOT NULL DEFAULT FALSE,
    order_index INT NOT NULL DEFAULT 0,
    helper_text TEXT,
    options_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    default_value_json JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'Draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_entity_views (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    list_columns_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    filter_fields_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    default_sort VARCHAR(180),
    form_sections_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_entity_permissions (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    action VARCHAR(30) NOT NULL,
    roles_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_entity_versions (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    version INT NOT NULL,
    page_key VARCHAR(80) NOT NULL,
    entity_snapshot_json JSONB NOT NULL,
    fields_snapshot_json JSONB NOT NULL,
    views_snapshot_json JSONB NOT NULL,
    permissions_snapshot_json JSONB NOT NULL,
    published_by INT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_key, version)
);

CREATE TABLE IF NOT EXISTS custom_records (
    id BIGSERIAL PRIMARY KEY,
    entity_key VARCHAR(80) NOT NULL,
    published_version INT NOT NULL,
    values_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    state VARCHAR(30) NOT NULL DEFAULT 'Active',
    created_by INT NOT NULL,
    updated_by INT,
    deleted_by INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entities_key_active
ON custom_entities(entity_key)
WHERE archived_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entity_fields_key_active
ON custom_entity_fields(entity_key, field_key)
WHERE status <> 'Archived';

CREATE UNIQUE INDEX IF NOT EXISTS ux_custom_entity_permissions_action
ON custom_entity_permissions(entity_key, action);

CREATE INDEX IF NOT EXISTS idx_custom_entity_fields_entity_order
ON custom_entity_fields(entity_key, order_index, id);

CREATE INDEX IF NOT EXISTS idx_custom_records_entity_active
ON custom_records(entity_key, deleted_at, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_custom_records_values_gin
ON custom_records USING GIN(values_json);

INSERT INTO custom_entities (
    entity_key, label, description, status, draft_version, published_version,
    etag, created_by, updated_by, published_at
)
SELECT
    'damaged_stock_report',
    'Phiếu kiểm hàng hỏng',
    'Entity custom cho ghi nhận sản phẩm hỏng trong kho.',
    'Published',
    1,
    1,
    'entity-damaged_stock_report-draft-1',
    1,
    1,
    now()
WHERE NOT EXISTS (
    SELECT 1 FROM custom_entities WHERE entity_key = 'damaged_stock_report' AND archived_at IS NULL
);

INSERT INTO custom_entity_fields (
    entity_key, field_key, label, field_type, required, filterable, sortable,
    searchable, order_index, helper_text, reference_json, validation_json,
    default_value_json, status
)
VALUES
    ('damaged_stock_report', 'report_code', 'Mã phiếu', 'text', TRUE, TRUE, TRUE, TRUE, 0,
     'Sinh theo định dạng KH-YYYY-NNNN.', '{}'::jsonb,
     '{"pattern":"^KH-[0-9]{4}-[0-9]{4}$","message":"Mã phiếu cần theo dạng KH-YYYY-NNNN."}'::jsonb,
     '"KH-2026-0001"'::jsonb, 'Active'),
    ('damaged_stock_report', 'product_ref', 'Sản phẩm', 'reference', TRUE, TRUE, FALSE, TRUE, 1,
     'Reference canonical dùng refType/refEntityKey.',
     '{"refType":"core","refEntityKey":"products"}'::jsonb, '{}'::jsonb, NULL, 'Active'),
    ('damaged_stock_report', 'location_ref', 'Vị trí kho', 'reference', TRUE, TRUE, FALSE, FALSE, 2,
     NULL, '{"refType":"core","refEntityKey":"inventory_locations"}'::jsonb, '{}'::jsonb, NULL, 'Active'),
    ('damaged_stock_report', 'damaged_quantity', 'Số lượng hỏng', 'number', TRUE, FALSE, TRUE, FALSE, 3,
     NULL, '{}'::jsonb, '{"min":"1","max":"999"}'::jsonb, NULL, 'Active'),
    ('damaged_stock_report', 'handling_status', 'Trạng thái xử lý', 'single_select', FALSE, TRUE, FALSE, FALSE, 4,
     NULL, '{}'::jsonb, '{}'::jsonb, '"Chờ xử lý"'::jsonb, 'Active')
ON CONFLICT DO NOTHING;

INSERT INTO custom_entity_views (
    entity_key, list_columns_json, filter_fields_json, default_sort, form_sections_json
)
SELECT
    'damaged_stock_report',
    '[
      {"fieldKey":"report_code","label":"Mã phiếu","width":140,"align":"left","format":"text"},
      {"fieldKey":"product_ref","label":"Sản phẩm","width":220,"align":"left","format":"text"},
      {"fieldKey":"location_ref","label":"Vị trí","width":160,"align":"left","format":"text"},
      {"fieldKey":"damaged_quantity","label":"SL hỏng","width":120,"align":"right","format":"number"},
      {"fieldKey":"handling_status","label":"Trạng thái","width":140,"align":"left","format":"badge"}
    ]'::jsonb,
    '["report_code","product_ref","location_ref","handling_status"]'::jsonb,
    'report_code desc',
    '[
      {"id":"section-general","title":"Thông tin chung","fieldKeys":["report_code","product_ref","location_ref"]},
      {"id":"section-quantity","title":"Kiểm hàng","fieldKeys":["damaged_quantity","handling_status"]}
    ]'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM custom_entity_views WHERE entity_key = 'damaged_stock_report'
);

INSERT INTO custom_entity_permissions(entity_key, action, roles_json)
VALUES
    ('damaged_stock_report', 'view', '["Owner","Admin","Staff","Warehouse"]'::jsonb),
    ('damaged_stock_report', 'create', '["Owner","Admin","Warehouse"]'::jsonb),
    ('damaged_stock_report', 'update', '["Owner","Admin","Warehouse"]'::jsonb),
    ('damaged_stock_report', 'delete', '["Owner","Admin"]'::jsonb)
ON CONFLICT (entity_key, action) DO NOTHING;

INSERT INTO custom_entity_versions (
    entity_key, version, page_key, entity_snapshot_json, fields_snapshot_json,
    views_snapshot_json, permissions_snapshot_json, published_by
)
SELECT
    'damaged_stock_report',
    1,
    'phieu_kiem_hang_hong',
    jsonb_build_object(
        'entityKey', e.entity_key,
        'label', e.label,
        'description', e.description,
        'status', e.status,
        'version', e.published_version
    ),
    (SELECT jsonb_agg(to_jsonb(f) ORDER BY f.order_index, f.id)
     FROM custom_entity_fields f WHERE f.entity_key = e.entity_key AND f.status <> 'Archived'),
    (SELECT to_jsonb(v) FROM custom_entity_views v WHERE v.entity_key = e.entity_key),
    (SELECT jsonb_agg(to_jsonb(p) ORDER BY p.action)
     FROM custom_entity_permissions p WHERE p.entity_key = e.entity_key),
    1
FROM custom_entities e
WHERE e.entity_key = 'damaged_stock_report'
ON CONFLICT (entity_key, version) DO NOTHING;

INSERT INTO custom_records(entity_key, published_version, values_json, state, created_by, updated_by)
VALUES
    ('damaged_stock_report', 1,
     '{"report_code":"KH-2026-0001","product_ref":"Áo khoác chống nước","location_ref":"Kho chính / Kệ A4","damaged_quantity":6,"handling_status":"Nháp"}'::jsonb,
     'Active', 1, 1),
    ('damaged_stock_report', 1,
     '{"report_code":"KH-2026-0002","product_ref":"Bình giữ nhiệt 500ml","location_ref":"Kho phụ / Kệ B1","damaged_quantity":2,"handling_status":"Nháp"}'::jsonb,
     'Active', 1, 1)
ON CONFLICT DO NOTHING;
```

- [ ] **Step 2: Compile backend to catch migration resource issues**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -DskipTests compile
```

Expected: exit 0.

- [ ] **Step 3: Commit migration**

```powershell
git add backend/smart-erp/src/main/resources/db/migration/V59__custom_builder_mvp_entities_records.sql
git commit -m "feat(custom-builder): add metadata and record schema"
```

---

## Task 2: Backend DTOs And Response Contracts

**Files:**
- Create: DTO and response records listed in File Structure
- Test: compile-only in this task

- [ ] **Step 1: Create field/view/permission request records**

Create `CustomFieldRequest.java`:

```java
package com.example.smart_erp.custominterface.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomFieldRequest(
		String id,
		String label,
		String fieldKey,
		String type,
		boolean required,
		boolean filterable,
		boolean sortable,
		boolean searchable,
		Integer order,
		String helperText,
		JsonNode options,
		JsonNode reference,
		JsonNode validation,
		JsonNode defaultValue,
		boolean readOnly,
		boolean hidden,
		String status) {
}
```

Create `CustomViewRequest.java`:

```java
package com.example.smart_erp.custominterface.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomViewRequest(
		JsonNode listColumns,
		JsonNode filterFields,
		String defaultSort,
		JsonNode formSections,
		String previewMode) {
}
```

Create `CustomPermissionRequest.java`:

```java
package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomPermissionRequest(
		List<String> view,
		List<String> create,
		List<String> update,
		List<String> delete) {
}
```

- [ ] **Step 2: Create bundle and record request records**

Create `CustomBuilderBundleRequest.java`:

```java
package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomBuilderBundleRequest(
		CustomPageRequest menuPage,
		String entityKey,
		String entityLabel,
		String entityDescription,
		List<CustomFieldRequest> fields,
		CustomViewRequest views,
		CustomPermissionRequest permissions,
		String etag) {
}
```

Create `CustomRecordRequest.java`:

```java
package com.example.smart_erp.custominterface.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomRecordRequest(JsonNode values) {
}
```

- [ ] **Step 3: Create response records**

Create `CustomEntityData.java`:

```java
package com.example.smart_erp.custominterface.response;

public record CustomEntityData(
		String key,
		String label,
		String description,
		String status,
		int version,
		Integer draftVersion,
		Integer publishedVersion,
		String etag) {
}
```

Create `CustomFieldData.java`:

```java
package com.example.smart_erp.custominterface.response;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomFieldData(
		String id,
		String label,
		String fieldKey,
		String type,
		boolean required,
		boolean filterable,
		boolean sortable,
		boolean searchable,
		int order,
		String helperText,
		JsonNode options,
		JsonNode reference,
		JsonNode validation,
		JsonNode defaultValue,
		boolean readOnly,
		boolean hidden,
		String status) {
}
```

Create `CustomViewData.java`:

```java
package com.example.smart_erp.custominterface.response;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomViewData(
		JsonNode listColumns,
		JsonNode filterFields,
		String defaultSort,
		JsonNode formSections,
		String previewMode) {
}
```

Create `CustomPermissionData.java`:

```java
package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomPermissionData(
		List<String> view,
		List<String> create,
		List<String> update,
		List<String> delete) {
}
```

Create `CustomBuilderBundleData.java`:

```java
package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomBuilderBundleData(
		CustomMenuPageData menuPage,
		CustomEntityData entityDefinition,
		List<CustomFieldData> fields,
		CustomViewData views,
		CustomPermissionData permissions,
		ValidationSummaryData validationSummary,
		String etag) {
}
```

Create `CustomRecordData.java`:

```java
package com.example.smart_erp.custominterface.response;

import java.time.Instant;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomRecordData(
		long id,
		String entityKey,
		int publishedVersion,
		JsonNode values,
		String state,
		Instant createdAt,
		Instant updatedAt) {
}
```

Create `CustomRecordPageData.java`:

```java
package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomRecordPageData(
		List<CustomRecordData> items,
		int page,
		int size,
		long total) {
}
```

- [ ] **Step 4: Compile response contracts**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -DskipTests compile
```

Expected before implementation: compile may fail only if imports are mistyped. Fix exact package/import issues until exit 0.

- [ ] **Step 5: Commit contracts**

```powershell
git add backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/dto backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/response
git commit -m "feat(custom-builder): add metadata and record contracts"
```

---

## Task 3: Backend Metadata Validator

**Files:**
- Create: `backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomMetadataValidator.java`
- Test: `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomMetadataValidatorTest.java`

- [ ] **Step 1: Write failing validator tests**

Create `CustomMetadataValidatorTest.java`:

```java
package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import org.junit.jupiter.api.Test;

import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.fasterxml.jackson.databind.ObjectMapper;

class CustomMetadataValidatorTest {

	private final ObjectMapper mapper = new ObjectMapper();
	private final CustomMetadataValidator validator = new CustomMetadataValidator(mapper);

	@Test
	void validateDraft_rejectsDuplicateFieldKeysAndMissingListColumns() {
		var fieldA = field("name", "Tên", "text", true);
		var fieldB = field("name", "Tên trùng", "text", false);
		var view = new CustomViewRequest(mapper.createArrayNode(), mapper.createArrayNode(), "name asc",
				mapper.createArrayNode(), "desktop");

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(fieldA, fieldB), view,
				new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("bị trùng"));
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("List view"));
	}

	@Test
	void validateDraft_acceptsMinimalValidEntity() {
		var columns = mapper.createArrayNode().addObject().put("fieldKey", "name").put("label", "Tên");
		var sections = mapper.createArrayNode().addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("name"));
		var view = new CustomViewRequest(columns, mapper.createArrayNode().add("name"), "name asc", sections, "desktop");

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(field("name", "Tên", "text", true)),
				view, new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isTrue();
		assertThat(summary.errors()).isEmpty();
	}

	@Test
	void validateDraft_rejectsReferenceOutsideAllowlist() {
		var reference = mapper.createObjectNode().put("refType", "core").put("refEntityKey", "unknown_table");
		var field = new CustomFieldRequest(null, "Ref", "ref_key", "reference", true, false, false, false, 0,
				null, mapper.createArrayNode(), reference, mapper.createObjectNode(), null, false, false, "Active");
		var columns = mapper.createArrayNode().addObject().put("fieldKey", "ref_key").put("label", "Ref");
		var sections = mapper.createArrayNode().addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("ref_key"));

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(field),
				new CustomViewRequest(columns, mapper.createArrayNode(), "ref_key asc", sections, "desktop"),
				new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("reference"));
	}

	private CustomFieldRequest field(String key, String label, String type, boolean required) {
		return new CustomFieldRequest(null, label, key, type, required, true, true, true, 0, null,
				mapper.createArrayNode(), mapper.createObjectNode(), mapper.createObjectNode(), null, false, false, "Active");
	}
}
```

- [ ] **Step 2: Run validator tests to verify failure**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomMetadataValidatorTest test
```

Expected: FAIL because `CustomMetadataValidator` does not exist.

- [ ] **Step 3: Implement validator**

Create `CustomMetadataValidator.java`:

```java
package com.example.smart_erp.custominterface.service;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class CustomMetadataValidator {

	private static final Pattern KEY_PATTERN = Pattern.compile("^[a-z0-9_]+$");
	private static final Set<String> FIELD_TYPES = Set.of("text", "long_text", "number", "money", "date", "boolean",
			"single_select", "reference");
	private static final Set<String> REF_TARGETS = Set.of("products", "suppliers", "customers", "inventory_locations",
			"users");
	private static final Set<String> ROLES = Set.of("Owner", "Admin", "Manager", "Staff", "Warehouse");

	@SuppressWarnings("unused")
	private final ObjectMapper objectMapper;

	public CustomMetadataValidator(ObjectMapper objectMapper) {
		this.objectMapper = objectMapper;
	}

	public ValidationSummaryData validateDraft(String pageKey, String entityKey, List<CustomFieldRequest> fields,
			CustomViewRequest view, CustomPermissionRequest permissions) {
		List<ValidationSummaryData.Item> errors = new ArrayList<>();
		List<ValidationSummaryData.Item> warnings = new ArrayList<>();
		validateKey("menu", "pageKey", pageKey, errors);
		validateKey("data", "entityKey", entityKey, errors);
		List<CustomFieldRequest> activeFields = fields == null ? List.of()
				: fields.stream().filter(field -> !"Archived".equals(field.status())).toList();
		if (activeFields.isEmpty()) {
			errors.add(new ValidationSummaryData.Item("data", "Entity cần tối thiểu một field."));
		}
		Set<String> fieldKeys = new HashSet<>();
		for (CustomFieldRequest field : activeFields) {
			validateField(field, fieldKeys, errors, warnings);
		}
		validateView(view, fieldKeys, activeFields, errors);
		validatePermissions(permissions, errors);
		return new ValidationSummaryData(errors.isEmpty(), errors, warnings);
	}

	private void validateField(CustomFieldRequest field, Set<String> fieldKeys, List<ValidationSummaryData.Item> errors,
			List<ValidationSummaryData.Item> warnings) {
		if (!StringUtils.hasText(field.label())) {
			errors.add(new ValidationSummaryData.Item("data", "Field bắt buộc phải có tên hiển thị.", field.fieldKey()));
		}
		validateKey("data", "fieldKey", field.fieldKey(), errors);
		if (StringUtils.hasText(field.fieldKey()) && !fieldKeys.add(field.fieldKey())) {
			errors.add(new ValidationSummaryData.Item("data", "Field key " + field.fieldKey() + " bị trùng.",
					field.fieldKey()));
		}
		if (!FIELD_TYPES.contains(field.type())) {
			errors.add(new ValidationSummaryData.Item("data", field.label() + " có loại field không hỗ trợ.",
					field.fieldKey()));
		}
		if ("single_select".equals(field.type()) && (field.options() == null || !field.options().isArray()
				|| field.options().isEmpty())) {
			errors.add(new ValidationSummaryData.Item("logic", field.label() + " cần tối thiểu một option.",
					field.fieldKey()));
		}
		if ("reference".equals(field.type())) {
			JsonNode reference = field.reference();
			String refTarget = reference == null ? null : reference.path("refEntityKey").asText(null);
			if (!REF_TARGETS.contains(refTarget)) {
				errors.add(new ValidationSummaryData.Item("data", field.label() + " có reference target không hợp lệ.",
						field.fieldKey()));
			}
		}
		if ((field.filterable() || field.sortable()) && !"Archived".equals(field.status())) {
			warnings.add(new ValidationSummaryData.Item("data", field.label() + " cần index backend nếu dữ liệu lớn.",
					field.fieldKey()));
		}
	}

	private void validateView(CustomViewRequest view, Set<String> fieldKeys, List<CustomFieldRequest> activeFields,
			List<ValidationSummaryData.Item> errors) {
		if (view == null || view.listColumns() == null || !view.listColumns().isArray() || view.listColumns().isEmpty()) {
			errors.add(new ValidationSummaryData.Item("view", "List view cần tối thiểu một cột."));
		}
		if (view != null && view.listColumns() != null && view.listColumns().isArray()) {
			for (JsonNode column : view.listColumns()) {
				String fieldKey = column.path("fieldKey").asText(null);
				if (!fieldKeys.contains(fieldKey)) {
					errors.add(new ValidationSummaryData.Item("view", "Cột " + fieldKey + " đang tham chiếu field không tồn tại.",
							fieldKey));
				}
			}
		}
		Set<String> formFieldKeys = new HashSet<>();
		if (view != null && view.formSections() != null && view.formSections().isArray()) {
			for (JsonNode section : view.formSections()) {
				JsonNode keys = section.path("fieldKeys");
				if (keys.isArray()) {
					keys.forEach(key -> formFieldKeys.add(key.asText()));
				}
			}
		}
		for (CustomFieldRequest field : activeFields) {
			if (field.required() && !formFieldKeys.contains(field.fieldKey())) {
				errors.add(new ValidationSummaryData.Item("view", field.label() + " là bắt buộc nên phải có trong form.",
						field.fieldKey()));
			}
		}
	}

	private void validatePermissions(CustomPermissionRequest permissions, List<ValidationSummaryData.Item> errors) {
		if (permissions == null) {
			errors.add(new ValidationSummaryData.Item("permission", "Cần cấu hình quyền truy cập."));
			return;
		}
		validateRoles("view", permissions.view(), errors);
		validateRoles("create", permissions.create(), errors);
		validateRoles("update", permissions.update(), errors);
		validateRoles("delete", permissions.delete(), errors);
	}

	private void validateRoles(String action, List<String> roles, List<ValidationSummaryData.Item> errors) {
		if (roles == null || roles.isEmpty()) {
			errors.add(new ValidationSummaryData.Item("permission", "Action " + action + " cần tối thiểu một role."));
			return;
		}
		for (String role : roles) {
			if (!ROLES.contains(role)) {
				errors.add(new ValidationSummaryData.Item("permission", "Role " + role + " không hợp lệ."));
			}
		}
	}

	private void validateKey(String section, String label, String value, List<ValidationSummaryData.Item> errors) {
		if (!StringUtils.hasText(value) || !KEY_PATTERN.matcher(value).matches()) {
			errors.add(new ValidationSummaryData.Item(section, label + " chỉ gồm chữ thường, số và underscore.", value));
		}
	}
}
```

- [ ] **Step 4: Run validator tests to verify pass**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomMetadataValidatorTest test
```

Expected: 3 tests pass.

- [ ] **Step 5: Commit validator**

```powershell
git add backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomMetadataValidator.java backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomMetadataValidatorTest.java
git commit -m "feat(custom-builder): validate custom metadata"
```

---

## Task 4: Backend Metadata Repository And Builder Service

**Files:**
- Create: `CustomEntityJdbcRepository.java`, `CustomBuilderService.java`
- Modify: `CustomInterfaceService.java`, `CustomInterfaceJdbcRepository.java`
- Test: extend with service tests after repository implementation

- [ ] **Step 1: Write failing service test for create/save/publish flow**

Create `backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomBuilderServiceTest.java`:

```java
package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.springframework.security.oauth2.jwt.Jwt;

import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPageRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository.EntityRow;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.PageRow;
import com.fasterxml.jackson.databind.ObjectMapper;

class CustomBuilderServiceTest {

	private final CustomEntityJdbcRepository entityRepository = org.mockito.Mockito.mock(CustomEntityJdbcRepository.class);
	private final CustomInterfaceJdbcRepository menuRepository = org.mockito.Mockito.mock(CustomInterfaceJdbcRepository.class);
	private final ObjectMapper mapper = new ObjectMapper();
	private final CustomMetadataValidator validator = new CustomMetadataValidator(mapper);
	private final CustomBuilderService service = new CustomBuilderService(entityRepository, menuRepository, validator, mapper);

	@Test
	void saveBundle_validatesAndPersistsMetadata() {
		var page = new PageRow(1L, "kiem_hang_page", "kiem_hang", "Kiểm hàng", null, null,
				"/custom/kiem_hang_page", "kiem_hang_entity", "record_list", "NeedsConfig", 0, "[\"Owner\"]",
				null, null, 1, null, "page-kiem_hang_page-draft-1", null, null);
		var entity = new EntityRow(10L, "kiem_hang_entity", "Kiểm hàng", "Desc", "NeedsConfig", 1, null,
				"entity-kiem_hang_entity-draft-1");
		when(menuRepository.findPage("kiem_hang_page")).thenReturn(Optional.of(page));
		when(entityRepository.findEntity("kiem_hang_entity")).thenReturn(Optional.of(entity));
		when(entityRepository.replaceBundle(any(), any(), any(), any(), any(), any(Integer.class))).thenReturn(entity);
		when(menuRepository.findPage("kiem_hang_page")).thenReturn(Optional.of(page));

		var request = bundleRequest("page-kiem_hang_page-draft-1");
		var saved = service.saveBundle("kiem_hang_page", request, jwt());

		assertThat(saved.validationSummary().valid()).isTrue();
		verify(entityRepository).replaceBundle(any(), any(), any(), any(), any(), any(Integer.class));
	}

	private CustomBuilderBundleRequest bundleRequest(String etag) {
		var field = new CustomFieldRequest(null, "Tên", "name", "text", true, true, true, true, 0, null,
				mapper.createArrayNode(), mapper.createObjectNode(), mapper.createObjectNode(), null, false, false, "Active");
		var columns = mapper.createArrayNode().addObject().put("fieldKey", "name").put("label", "Tên");
		var sections = mapper.createArrayNode().addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("name"));
		return new CustomBuilderBundleRequest(
				new CustomPageRequest("kiem_hang", "kiem_hang_page", "Kiểm hàng", null, null,
						"/custom/kiem_hang_page", "kiem_hang_entity", "record_list", List.of("Owner"), null, null, 0, etag),
				"kiem_hang_entity", "Kiểm hàng", "Desc", List.of(field),
				new CustomViewRequest(columns, mapper.createArrayNode().add("name"), "name asc", sections, "desktop"),
				new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")), etag);
	}

	private Jwt jwt() {
		return Jwt.withTokenValue("t").header("alg", "none").subject("1").claim("role", "Owner").build();
	}
}
```

- [ ] **Step 2: Run service test to verify failure**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomBuilderServiceTest test
```

Expected: FAIL because `CustomEntityJdbcRepository` and `CustomBuilderService` do not exist.

- [ ] **Step 3: Implement `CustomEntityJdbcRepository` records and methods**

Create `CustomEntityJdbcRepository.java` with these public records and methods:

```java
package com.example.smart_erp.custominterface.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Repository
public class CustomEntityJdbcRepository {

	private final JdbcTemplate jdbcTemplate;
	private final ObjectMapper objectMapper;

	public CustomEntityJdbcRepository(JdbcTemplate jdbcTemplate, ObjectMapper objectMapper) {
		this.jdbcTemplate = jdbcTemplate;
		this.objectMapper = objectMapper;
	}

	public Optional<EntityRow> findEntity(String entityKey) {
		List<EntityRow> rows = jdbcTemplate.query("""
				SELECT id, entity_key, label, description, status, draft_version, published_version, etag
				FROM custom_entities
				WHERE entity_key = ? AND archived_at IS NULL
				""", entityMapper(), entityKey);
		return rows.stream().findFirst();
	}

	public List<FieldRow> findFields(String entityKey) {
		return jdbcTemplate.query("""
				SELECT id, entity_key, field_key, label, field_type, required, filterable, sortable,
				       searchable, order_index, helper_text, options_json::text, reference_json::text,
				       validation_json::text, default_value_json::text, status
				FROM custom_entity_fields
				WHERE entity_key = ? AND status <> 'Archived'
				ORDER BY order_index ASC, id ASC
				""", fieldMapper(objectMapper), entityKey);
	}

	public Optional<ViewRow> findView(String entityKey) {
		List<ViewRow> rows = jdbcTemplate.query("""
				SELECT entity_key, list_columns_json::text, filter_fields_json::text, default_sort,
				       form_sections_json::text
				FROM custom_entity_views
				WHERE entity_key = ?
				""", viewMapper(objectMapper), entityKey);
		return rows.stream().findFirst();
	}

	public PermissionRow findPermissions(String entityKey) {
		List<ActionRolesRow> rows = jdbcTemplate.query("""
				SELECT action, roles_json::text
				FROM custom_entity_permissions
				WHERE entity_key = ?
				ORDER BY action ASC
				""", actionRolesMapper(objectMapper), entityKey);
		return PermissionRow.from(rows);
	}

	public EntityRow replaceBundle(EntityRow current, String label, String description, List<CustomFieldRequest> fields,
			CustomViewRequest view, CustomPermissionRequest permissions, Integer userId) {
		int nextVersion = current.draftVersion() + 1;
		String etag = entityEtag(current.key(), nextVersion);
		jdbcTemplate.update("""
				UPDATE custom_entities
				SET label = ?, description = ?, draft_version = ?, etag = ?, updated_by = ?, updated_at = now()
				WHERE entity_key = ? AND archived_at IS NULL
				""", label, description, nextVersion, etag, userId, current.key());
		jdbcTemplate.update("DELETE FROM custom_entity_fields WHERE entity_key = ?", current.key());
		int order = 0;
		for (CustomFieldRequest field : fields) {
			jdbcTemplate.update("""
					INSERT INTO custom_entity_fields(
						entity_key, field_key, label, field_type, required, filterable, sortable,
						searchable, order_index, helper_text, options_json, reference_json, validation_json,
						default_value_json, status
					)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?::jsonb, ?::jsonb, ?::jsonb, ?::jsonb, ?)
					""", current.key(), field.fieldKey(), field.label(), field.type(), field.required(),
					field.filterable(), field.sortable(), field.searchable(), field.order() == null ? order : field.order(),
					field.helperText(), json(field.options(), "[]"), json(field.reference(), "{}"),
					json(field.validation(), "{}"), field.defaultValue() == null ? null : json(field.defaultValue(), null),
					field.status() == null ? "Active" : field.status());
			order += 1;
		}
		jdbcTemplate.update("DELETE FROM custom_entity_views WHERE entity_key = ?", current.key());
		jdbcTemplate.update("""
				INSERT INTO custom_entity_views(entity_key, list_columns_json, filter_fields_json, default_sort, form_sections_json)
				VALUES (?, ?::jsonb, ?::jsonb, ?, ?::jsonb)
				""", current.key(), json(view.listColumns(), "[]"), json(view.filterFields(), "[]"), view.defaultSort(),
				json(view.formSections(), "[]"));
		replacePermission(current.key(), "view", permissions.view());
		replacePermission(current.key(), "create", permissions.create());
		replacePermission(current.key(), "update", permissions.update());
		replacePermission(current.key(), "delete", permissions.delete());
		return findEntity(current.key()).orElseThrow();
	}

	public void publishSnapshot(String pageKey, EntityRow entity, int userId) {
		int version = entity.draftVersion();
		jdbcTemplate.update("""
				INSERT INTO custom_entity_versions(
					entity_key, version, page_key, entity_snapshot_json, fields_snapshot_json,
					views_snapshot_json, permissions_snapshot_json, published_by
				)
				SELECT e.entity_key, e.draft_version, ?, to_jsonb(e),
				       (SELECT jsonb_agg(to_jsonb(f) ORDER BY f.order_index, f.id)
				        FROM custom_entity_fields f WHERE f.entity_key = e.entity_key AND f.status <> 'Archived'),
				       (SELECT to_jsonb(v) FROM custom_entity_views v WHERE v.entity_key = e.entity_key),
				       (SELECT jsonb_agg(to_jsonb(p) ORDER BY p.action)
				        FROM custom_entity_permissions p WHERE p.entity_key = e.entity_key),
				       ?
				FROM custom_entities e
				WHERE e.entity_key = ?
				ON CONFLICT (entity_key, version) DO NOTHING
				""", pageKey, userId, entity.key());
		jdbcTemplate.update("""
				UPDATE custom_entities
				SET status = 'Published', published_version = draft_version, published_at = now(),
				    updated_by = ?, updated_at = now()
				WHERE entity_key = ?
				""", userId, entity.key());
	}

	private void replacePermission(String entityKey, String action, List<String> roles) {
		jdbcTemplate.update("""
				INSERT INTO custom_entity_permissions(entity_key, action, roles_json, updated_at)
				VALUES (?, ?, ?::jsonb, now())
				ON CONFLICT (entity_key, action)
				DO UPDATE SET roles_json = EXCLUDED.roles_json, updated_at = now()
				""", entityKey, action, jsonArray(roles));
	}

	private String json(JsonNode node, String fallback) {
		if (node == null || node.isNull()) {
			return fallback;
		}
		return node.toString();
	}

	private String jsonArray(List<String> values) {
		try {
			return objectMapper.writeValueAsString(values == null ? List.of() : values);
		} catch (Exception ex) {
			return "[]";
		}
	}

	public static String entityEtag(String key, int version) {
		return "entity-" + key + "-draft-" + version;
	}

	private static RowMapper<EntityRow> entityMapper() {
		return (rs, rowNum) -> new EntityRow(rs.getLong("id"), rs.getString("entity_key"), rs.getString("label"),
				rs.getString("description"), rs.getString("status"), rs.getInt("draft_version"),
				nullableInt(rs, "published_version"), rs.getString("etag"));
	}

	private static RowMapper<FieldRow> fieldMapper(ObjectMapper mapper) {
		return (rs, rowNum) -> new FieldRow(String.valueOf(rs.getLong("id")), rs.getString("entity_key"),
				rs.getString("field_key"), rs.getString("label"), rs.getString("field_type"),
				rs.getBoolean("required"), rs.getBoolean("filterable"), rs.getBoolean("sortable"),
				rs.getBoolean("searchable"), rs.getInt("order_index"), rs.getString("helper_text"),
				read(mapper, rs.getString("options_json"), "[]"), read(mapper, rs.getString("reference_json"), "{}"),
				read(mapper, rs.getString("validation_json"), "{}"), read(mapper, rs.getString("default_value_json"), null),
				rs.getString("status"));
	}

	private static RowMapper<ViewRow> viewMapper(ObjectMapper mapper) {
		return (rs, rowNum) -> new ViewRow(rs.getString("entity_key"),
				read(mapper, rs.getString("list_columns_json"), "[]"), read(mapper, rs.getString("filter_fields_json"), "[]"),
				rs.getString("default_sort"), read(mapper, rs.getString("form_sections_json"), "[]"));
	}

	private static RowMapper<ActionRolesRow> actionRolesMapper(ObjectMapper mapper) {
		return (rs, rowNum) -> new ActionRolesRow(rs.getString("action"), read(mapper, rs.getString("roles_json"), "[]"));
	}

	private static JsonNode read(ObjectMapper mapper, String raw, String fallback) {
		try {
			if (raw == null) {
				return fallback == null ? null : mapper.readTree(fallback);
			}
			return mapper.readTree(raw);
		} catch (Exception ex) {
			try {
				return fallback == null ? null : mapper.readTree(fallback);
			} catch (Exception ignored) {
				return null;
			}
		}
	}

	private static Integer nullableInt(ResultSet rs, String column) throws SQLException {
		int value = rs.getInt(column);
		return rs.wasNull() ? null : value;
	}

	public record EntityRow(long id, String key, String label, String description, String status, int draftVersion,
			Integer publishedVersion, String etag) {
	}

	public record FieldRow(String id, String entityKey, String fieldKey, String label, String type, boolean required,
			boolean filterable, boolean sortable, boolean searchable, int order, String helperText, JsonNode options,
			JsonNode reference, JsonNode validation, JsonNode defaultValue, String status) {
	}

	public record ViewRow(String entityKey, JsonNode listColumns, JsonNode filterFields, String defaultSort,
			JsonNode formSections) {
	}

	public record ActionRolesRow(String action, JsonNode roles) {
	}

	public record PermissionRow(List<String> view, List<String> create, List<String> update, List<String> delete) {
		public static PermissionRow from(List<ActionRolesRow> rows) {
			return new PermissionRow(roles(rows, "view"), roles(rows, "create"), roles(rows, "update"), roles(rows, "delete"));
		}

		private static List<String> roles(List<ActionRolesRow> rows, String action) {
			return rows.stream().filter(row -> action.equals(row.action())).findFirst()
					.map(row -> {
						List<String> out = new java.util.ArrayList<>();
						row.roles().forEach(role -> out.add(role.asText()));
						return List.copyOf(out);
					})
					.orElse(List.of("Owner", "Admin"));
		}
	}
}
```

- [ ] **Step 4: Implement `CustomBuilderService`**

Create `CustomBuilderService.java`:

```java
package com.example.smart_erp.custominterface.service;

import java.util.List;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository.EntityRow;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.PageRow;
import com.example.smart_erp.custominterface.response.CustomBuilderBundleData;
import com.example.smart_erp.custominterface.response.CustomEntityData;
import com.example.smart_erp.custominterface.response.CustomFieldData;
import com.example.smart_erp.custominterface.response.CustomPermissionData;
import com.example.smart_erp.custominterface.response.CustomViewData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.inventory.receipts.lifecycle.StockReceiptAccessPolicy;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class CustomBuilderService {

	private static final String STALE = "Cấu hình đã được cập nhật bởi người khác. Vui lòng tải lại trước khi lưu.";

	private final CustomEntityJdbcRepository entityRepository;
	private final CustomInterfaceJdbcRepository menuRepository;
	private final CustomMetadataValidator validator;
	@SuppressWarnings("unused")
	private final ObjectMapper objectMapper;

	public CustomBuilderService(CustomEntityJdbcRepository entityRepository, CustomInterfaceJdbcRepository menuRepository,
			CustomMetadataValidator validator, ObjectMapper objectMapper) {
		this.entityRepository = entityRepository;
		this.menuRepository = menuRepository;
		this.validator = validator;
		this.objectMapper = objectMapper;
	}

	@Transactional(readOnly = true)
	public CustomBuilderBundleData getBundle(String pageKey) {
		PageRow page = menuRepository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh."));
		EntityRow entity = entityRepository.findEntity(page.entityKey())
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy entity tùy chỉnh."));
		return toBundle(page, entity, validate(page, entity));
	}

	@Transactional
	public CustomBuilderBundleData saveBundle(String pageKey, CustomBuilderBundleRequest request, Jwt jwt) {
		PageRow page = menuRepository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh."));
		EntityRow entity = entityRepository.findEntity(page.entityKey())
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy entity tùy chỉnh."));
		assertEtag(page.etag(), request.etag());
		ValidationSummaryData summary = validator.validateDraft(request.menuPage().key(), request.entityKey(),
				request.fields(), request.views(), request.permissions());
		if (!summary.valid()) {
			return toBundle(page, entity, summary);
		}
		EntityRow updated = entityRepository.replaceBundle(entity, request.entityLabel(), request.entityDescription(),
				request.fields(), request.views(), request.permissions(), StockReceiptAccessPolicy.parseUserId(jwt));
		return toBundle(page, updated, validate(page, updated));
	}

	@Transactional(readOnly = true)
	public ValidationSummaryData validatePage(String pageKey) {
		PageRow page = menuRepository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh."));
		EntityRow entity = entityRepository.findEntity(page.entityKey())
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy entity tùy chỉnh."));
		return validate(page, entity);
	}

	@Transactional
	public CustomBuilderBundleData publish(String pageKey, String etag, Jwt jwt) {
		PageRow page = menuRepository.findPage(pageKey)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy giao diện tùy chỉnh."));
		EntityRow entity = entityRepository.findEntity(page.entityKey())
				.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy entity tùy chỉnh."));
		assertEtag(page.etag(), etag);
		ValidationSummaryData summary = validate(page, entity);
		if (!summary.valid()) {
			throw new BusinessException(ApiErrorCode.UNPROCESSABLE_ENTITY,
					"Cấu hình chưa hợp lệ để publish. Vui lòng kiểm tra các cảnh báo.");
		}
		int userId = StockReceiptAccessPolicy.parseUserId(jwt);
		entityRepository.publishSnapshot(page.key(), entity, userId);
		menuRepository.publishPage(page.key(), userId);
		EntityRow published = entityRepository.findEntity(entity.key()).orElseThrow();
		PageRow publishedPage = menuRepository.findPage(page.key()).orElseThrow();
		return toBundle(publishedPage, published, ValidationSummaryData.ok());
	}

	private ValidationSummaryData validate(PageRow page, EntityRow entity) {
		var fields = entityRepository.findFields(entity.key()).stream()
				.map(row -> new com.example.smart_erp.custominterface.dto.CustomFieldRequest(row.id(), row.label(),
						row.fieldKey(), row.type(), row.required(), row.filterable(), row.sortable(), row.searchable(),
						row.order(), row.helperText(), row.options(), row.reference(), row.validation(), row.defaultValue(),
						false, false, row.status()))
				.toList();
		var viewRow = entityRepository.findView(entity.key()).orElseThrow();
		var view = new com.example.smart_erp.custominterface.dto.CustomViewRequest(viewRow.listColumns(), viewRow.filterFields(),
				viewRow.defaultSort(), viewRow.formSections(), "desktop");
		var permissions = entityRepository.findPermissions(entity.key());
		return validator.validateDraft(page.key(), entity.key(), fields, view,
				new com.example.smart_erp.custominterface.dto.CustomPermissionRequest(permissions.view(), permissions.create(),
						permissions.update(), permissions.delete()));
	}

	private CustomBuilderBundleData toBundle(PageRow page, EntityRow entity, ValidationSummaryData summary) {
		var fields = entityRepository.findFields(entity.key()).stream()
				.map(row -> new CustomFieldData(row.id(), row.label(), row.fieldKey(), row.type(), row.required(),
						row.filterable(), row.sortable(), row.searchable(), row.order(), row.helperText(), row.options(),
						row.reference(), row.validation(), row.defaultValue(), false, false, row.status()))
				.toList();
		var view = entityRepository.findView(entity.key())
				.map(row -> new CustomViewData(row.listColumns(), row.filterFields(), row.defaultSort(), row.formSections(),
						"desktop"))
				.orElse(new CustomViewData(null, null, null, null, "desktop"));
		var permissions = entityRepository.findPermissions(entity.key());
		return new CustomBuilderBundleData(
				new com.example.smart_erp.custominterface.response.CustomMenuPageData("page", String.valueOf(page.id()),
						page.key(), page.label(), null, page.parentKey(), page.routePath(), page.entityKey(), page.pageType(),
						page.status(), page.sortOrder(), page.description(), List.of(), page.entityPermission(),
						page.dataPermission(), page.draftVersion(), page.draftVersion(), page.publishedVersion(),
						page.publishedVersion() == null || page.draftVersion() > page.publishedVersion(), page.publishedAt(),
						null, page.updatedAt(), null, page.etag(), summary),
				new CustomEntityData(entity.key(), entity.label(), entity.description(), entity.status(), entity.draftVersion(),
						entity.draftVersion(), entity.publishedVersion(), entity.etag()),
				fields, view, new CustomPermissionData(permissions.view(), permissions.create(), permissions.update(),
						permissions.delete()),
				summary, page.etag());
	}

	private void assertEtag(String current, String supplied) {
		if (supplied == null || !current.equals(supplied)) {
			throw new BusinessException(ApiErrorCode.CONFLICT, STALE);
		}
	}
}
```

- [ ] **Step 5: Add `publishPage` to `CustomInterfaceJdbcRepository`**

Add this method:

```java
public void publishPage(String pageKey, int userId) {
	jdbcTemplate.update("""
			UPDATE custom_menu_pages
			SET status = 'Published', published_version = draft_version, published_at = now(),
			    updated_by = ?, updated_at = now()
			WHERE page_key = ? AND archived_at IS NULL
			""", userId, pageKey);
	jdbcTemplate.update("""
			INSERT INTO custom_menu_page_versions (
				page_key, version, parent_folder_key, label, icon, description, route_path, entity_key, page_type,
				sort_order, visibility_roles, entity_permission, data_permission, published_by
			)
			SELECT page_key, draft_version, parent_folder_key, label, icon, description, route_path, entity_key,
			       page_type, sort_order, visibility_roles, entity_permission, data_permission, ?
			FROM custom_menu_pages
			WHERE page_key = ? AND archived_at IS NULL
			ON CONFLICT (page_key, version) DO NOTHING
			""", userId, pageKey);
}
```

- [ ] **Step 6: Run service test**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomBuilderServiceTest test
```

Expected: pass after compile fixes.

- [ ] **Step 7: Commit builder service**

```powershell
git add backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/repository/CustomEntityJdbcRepository.java backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomBuilderService.java backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/repository/CustomInterfaceJdbcRepository.java backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomBuilderServiceTest.java
git commit -m "feat(custom-builder): persist builder metadata"
```

---

## Task 5: Backend Builder And Runtime Bundle Controllers

**Files:**
- Create: `CustomBuilderController.java`
- Modify: `CustomInterfaceController.java`
- Test: `CustomBuilderControllerWebMvcTest.java`

- [ ] **Step 1: Write failing WebMvc tests**

Create `CustomBuilderControllerWebMvcTest.java`:

```java
package com.example.smart_erp.custominterface.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import java.util.Objects;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.smart_erp.common.exception.GlobalExceptionHandler;
import com.example.smart_erp.common.exception.MaxUploadSizeExceededAdvice;
import com.example.smart_erp.config.MethodSecurityTestConfiguration;
import com.example.smart_erp.config.PermitAllWebSecurityConfiguration;
import com.example.smart_erp.config.SecurityBeansConfiguration;
import com.example.smart_erp.custominterface.response.CustomBuilderBundleData;
import com.example.smart_erp.custominterface.response.CustomEntityData;
import com.example.smart_erp.custominterface.response.CustomMenuPageData;
import com.example.smart_erp.custominterface.response.CustomPermissionData;
import com.example.smart_erp.custominterface.response.CustomViewData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.custominterface.service.CustomBuilderService;

@WebMvcTest(controllers = CustomBuilderController.class)
@Import({ GlobalExceptionHandler.class, MaxUploadSizeExceededAdvice.class, SecurityBeansConfiguration.class,
		PermitAllWebSecurityConfiguration.class, MethodSecurityTestConfiguration.class })
class CustomBuilderControllerWebMvcTest {

	@Autowired
	private MockMvc mockMvc;

	@MockitoBean
	private CustomBuilderService service;

	@Test
	void getBundle_requiresBuilderAuthority() throws Exception {
		mockMvc.perform(get("/api/v1/custom/builder/pages/phieu_kiem_hang_hong/bundle")
				.with(Objects.requireNonNull(jwt().authorities(new SimpleGrantedAuthority("can_view_dashboard")))))
				.andExpect(status().isForbidden());
	}

	@Test
	void getBundle_returnsEnvelopeForAuthorizedUser() throws Exception {
		when(service.getBundle("phieu_kiem_hang_hong")).thenReturn(bundle());

		mockMvc.perform(get("/api/v1/custom/builder/pages/phieu_kiem_hang_hong/bundle")
				.with(Objects.requireNonNull(jwt()
						.authorities(new SimpleGrantedAuthority("can_manage_custom_builder"))
						.jwt(j -> j.subject("1").claim("role", "Owner")))))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.success").value(true))
				.andExpect(jsonPath("$.data.entityDefinition.key").value("damaged_stock_report"));
	}

	@Test
	void patchBundle_delegatesSave() throws Exception {
		when(service.saveBundle(eq("phieu_kiem_hang_hong"), any(), any())).thenReturn(bundle());
		mockMvc.perform(patch("/api/v1/custom/builder/pages/phieu_kiem_hang_hong/bundle")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"etag\":\"page-phieu_kiem_hang_hong-draft-1\",\"fields\":[],\"permissions\":{\"view\":[\"Owner\"],\"create\":[\"Owner\"],\"update\":[\"Owner\"],\"delete\":[\"Owner\"]}}")
				.with(Objects.requireNonNull(jwt()
						.authorities(new SimpleGrantedAuthority("can_manage_custom_builder"))
						.jwt(j -> j.subject("1").claim("role", "Owner")))))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.data.etag").value("page-phieu_kiem_hang_hong-draft-1"));
	}

	@Test
	void publish_returnsBundle() throws Exception {
		when(service.publish(eq("phieu_kiem_hang_hong"), eq("page-phieu_kiem_hang_hong-draft-1"), any())).thenReturn(bundle());
		mockMvc.perform(post("/api/v1/custom/builder/pages/phieu_kiem_hang_hong/publish")
				.contentType(MediaType.APPLICATION_JSON)
				.content("{\"etag\":\"page-phieu_kiem_hang_hong-draft-1\"}")
				.with(Objects.requireNonNull(jwt()
						.authorities(new SimpleGrantedAuthority("can_manage_custom_builder"))
						.jwt(j -> j.subject("1").claim("role", "Owner")))))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.data.menuPage.key").value("phieu_kiem_hang_hong"));
	}

	private CustomBuilderBundleData bundle() {
		var page = new CustomMenuPageData("page", "1", "phieu_kiem_hang_hong", "Phiếu kiểm hàng hỏng", null,
				"kiem_hang", "/custom/phieu_kiem_hang_hong", "damaged_stock_report", "table_detail", "Published", 0,
				null, List.of("Owner"), "can_manage_inventory", "can_manage_inventory", 1, 1, 1, false, null, null,
				null, null, "page-phieu_kiem_hang_hong-draft-1", ValidationSummaryData.ok());
		return new CustomBuilderBundleData(page,
				new CustomEntityData("damaged_stock_report", "Phiếu kiểm hàng hỏng", null, "Published", 1, 1, 1,
						"entity-damaged_stock_report-draft-1"),
				List.of(), new CustomViewData(null, null, null, null, "desktop"),
				new CustomPermissionData(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")),
				ValidationSummaryData.ok(), "page-phieu_kiem_hang_hong-draft-1");
	}
}
```

- [ ] **Step 2: Run WebMvc tests to verify failure**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomBuilderControllerWebMvcTest test
```

Expected: FAIL because `CustomBuilderController` does not exist.

- [ ] **Step 3: Implement `CustomBuilderController`**

Create:

```java
package com.example.smart_erp.custominterface.controller;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.api.ApiSuccessResponse;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.response.CustomBuilderBundleData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.custominterface.service.CustomBuilderService;

@RestController
@RequestMapping("/api/v1/custom/builder")
public class CustomBuilderController {

	private static final String UNAUTHORIZED = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";

	private final CustomBuilderService service;

	public CustomBuilderController(CustomBuilderService service) {
		this.service = service;
	}

	@GetMapping("/pages/{pageKey}/bundle")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> bundle(@PathVariable String pageKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.getBundle(pageKey), "Thành công"));
	}

	@PatchMapping("/pages/{pageKey}/bundle")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> save(Authentication authentication,
			@PathVariable String pageKey, @RequestBody CustomBuilderBundleRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.saveBundle(pageKey, request, requireJwt(authentication)),
				"Đã lưu bản nháp cấu hình giao diện"));
	}

	@PostMapping("/pages/{pageKey}/validate")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<ValidationSummaryData>> validate(@PathVariable String pageKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.validatePage(pageKey), "Thành công"));
	}

	@PostMapping("/pages/{pageKey}/publish")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> publish(Authentication authentication,
			@PathVariable String pageKey, @RequestBody(required = false) Map<String, String> body) {
		String etag = body == null ? null : body.get("etag");
		return ResponseEntity.ok(ApiSuccessResponse.of(service.publish(pageKey, etag, requireJwt(authentication)),
				"Đã publish cấu hình giao diện"));
	}

	private static Jwt requireJwt(Authentication authentication) {
		if (authentication == null || authentication instanceof AnonymousAuthenticationToken
				|| !(authentication.getPrincipal() instanceof Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED);
		}
		return jwt;
	}
}
```

- [ ] **Step 4: Add runtime bundle method and modify runtime page endpoint**

Add this method to `CustomBuilderService`:

```java
@Transactional(readOnly = true)
public CustomBuilderBundleData runtimeBundle(String pageKey, Authentication authentication, Jwt jwt) {
	PageRow page = menuRepository.findPublishedPage(pageKey)
			.orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND,
					"Không tìm thấy giao diện tùy chỉnh hoặc giao diện chưa được publish."));
	String role = jwt.getClaimAsString("role");
	boolean roleAllowed = role == null || page.rolesJson() == null || page.rolesJson().contains("\"" + role + "\"");
	boolean entityAllowed = page.entityPermission() == null || authentication.getAuthorities().stream()
			.anyMatch(authority -> page.entityPermission().equals(authority.getAuthority()));
	boolean dataAllowed = page.dataPermission() == null || authentication.getAuthorities().stream()
			.anyMatch(authority -> page.dataPermission().equals(authority.getAuthority()));
	if (!roleAllowed || !entityAllowed || !dataAllowed) {
		throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền thực hiện thao tác này.");
	}
	return getBundle(page.key());
}
```

In `CustomInterfaceController`, change `runtimePage` response type from `CustomMenuTreeData` to `CustomBuilderBundleData` and delegate to `CustomBuilderService.runtimeBundle`. Use this endpoint shape:

```java
@GetMapping("/pages/{pageKey}/runtime")
public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> runtimePage(Authentication authentication,
		@PathVariable String pageKey) {
	return ResponseEntity.ok(ApiSuccessResponse.of(builderService.runtimeBundle(pageKey, authentication, requireJwt(authentication)),
			"Thành công"));
}
```

Constructor-inject `CustomBuilderService builderService` into `CustomInterfaceController`. `runtimeBundle` uses `findPublishedPage`, role checks, and authority checks before returning the bundle.

- [ ] **Step 5: Run builder controller tests**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomBuilderControllerWebMvcTest test
```

Expected: pass.

- [ ] **Step 6: Commit controller API**

```powershell
git add backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/controller/CustomBuilderController.java backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/controller/CustomInterfaceController.java backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/controller/CustomBuilderControllerWebMvcTest.java
git commit -m "feat(custom-builder): expose builder bundle api"
```

---

## Task 6: Backend Runtime Record Repository, Service, And Controller

**Files:**
- Create: `CustomRecordJdbcRepository.java`, `CustomRecordService.java`, `CustomRecordController.java`
- Test: `CustomRecordServiceTest.java`, `CustomRecordControllerWebMvcTest.java`

- [ ] **Step 1: Write failing record service tests**

Create `CustomRecordServiceTest.java`:

```java
package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;

import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomRecordRequest;
import com.example.smart_erp.custominterface.repository.CustomEntityJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomRecordJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomRecordJdbcRepository.RecordRow;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository;
import com.example.smart_erp.custominterface.repository.CustomInterfaceJdbcRepository.PageRow;
import com.fasterxml.jackson.databind.ObjectMapper;

class CustomRecordServiceTest {

	private final CustomRecordJdbcRepository recordRepository = org.mockito.Mockito.mock(CustomRecordJdbcRepository.class);
	private final CustomEntityJdbcRepository entityRepository = org.mockito.Mockito.mock(CustomEntityJdbcRepository.class);
	private final CustomInterfaceJdbcRepository menuRepository = org.mockito.Mockito.mock(CustomInterfaceJdbcRepository.class);
	private final ObjectMapper mapper = new ObjectMapper();
	private final CustomRecordService service = new CustomRecordService(recordRepository, entityRepository, menuRepository, mapper);

	@Test
	void create_rejectsMissingRequiredField() {
		when(menuRepository.findPublishedPage("page")).thenReturn(java.util.Optional.of(page()));
		when(entityRepository.findFields("entity")).thenReturn(List.of(new CustomEntityJdbcRepository.FieldRow("1", "entity",
				"name", "Tên", "text", true, false, false, false, 0, null, mapper.createArrayNode(),
				mapper.createObjectNode(), mapper.createObjectNode(), null, "Active")));
		when(entityRepository.findPermissions("entity")).thenReturn(new CustomEntityJdbcRepository.PermissionRow(
				List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThatThrownBy(() -> service.create("page", new CustomRecordRequest(mapper.createObjectNode()), auth()))
				.isInstanceOf(BusinessException.class)
				.hasMessageContaining("Tên");
	}

	@Test
	void create_persistsValidRecord() {
		when(menuRepository.findPublishedPage("page")).thenReturn(java.util.Optional.of(page()));
		when(entityRepository.findFields("entity")).thenReturn(List.of(new CustomEntityJdbcRepository.FieldRow("1", "entity",
				"name", "Tên", "text", true, false, false, false, 0, null, mapper.createArrayNode(),
				mapper.createObjectNode(), mapper.createObjectNode(), null, "Active")));
		when(entityRepository.findPermissions("entity")).thenReturn(new CustomEntityJdbcRepository.PermissionRow(
				List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));
		when(recordRepository.insert(eqString("entity"), any(), any(Integer.class), any(Integer.class)))
				.thenReturn(new RecordRow(99L, "entity", 1, mapper.createObjectNode().put("name", "A"), "Active", null, null));

		var result = service.create("page", new CustomRecordRequest(mapper.createObjectNode().put("name", "A")), auth());

		assertThat(result.id()).isEqualTo(99L);
	}

	private String eqString(String value) {
		return org.mockito.ArgumentMatchers.eq(value);
	}

	private PageRow page() {
		return new PageRow(1L, "page", "folder", "Page", null, null, "/custom/page", "entity", "record_list",
				"Published", 0, "[\"Owner\"]", null, null, 1, 1, "page-page-draft-1", null, null);
	}

	private Authentication auth() {
		Jwt jwt = Jwt.withTokenValue("t").header("alg", "none").subject("1").claim("role", "Owner").build();
		return new JwtAuthenticationToken(jwt, List.of(new SimpleGrantedAuthority("can_use_custom_entities")));
	}
}
```

- [ ] **Step 2: Run record service tests to verify failure**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomRecordServiceTest test
```

Expected: FAIL because record repository/service do not exist.

- [ ] **Step 3: Implement `CustomRecordJdbcRepository`**

Create methods:

```java
public CustomRecordPageData list(String entityKey, int page, int size, String search)
public RecordRow insert(String entityKey, JsonNode values, int publishedVersion, int userId)
public Optional<RecordRow> find(String entityKey, long id)
public RecordRow update(String entityKey, long id, JsonNode values, int userId)
public void softDelete(String entityKey, long id, int userId)
```

Use parameterized SQL only. For search, use:

```sql
AND (:search IS NULL OR values_json::text ILIKE '%' || :search || '%')
```

Map rows into:

```java
public record RecordRow(long id, String entityKey, int publishedVersion, JsonNode values, String state,
		Instant createdAt, Instant updatedAt) {
}
```

- [ ] **Step 4: Implement `CustomRecordService`**

Service rules:

```java
private void validateValues(List<FieldRow> fields, JsonNode values) {
	for (FieldRow field : fields) {
		JsonNode value = values == null ? null : values.get(field.fieldKey());
		if (field.required() && (value == null || value.isNull() || (value.isTextual() && !StringUtils.hasText(value.asText())))) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, field.label() + " là bắt buộc.");
		}
		if (value == null || value.isNull()) {
			continue;
		}
		if (("number".equals(field.type()) || "money".equals(field.type())) && !value.isNumber()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, field.label() + " phải là số.");
		}
		if ("boolean".equals(field.type()) && !value.isBoolean()) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, field.label() + " phải là đúng/sai.");
		}
	}
}
```

Action permission check:

```java
private void requireAction(PermissionRow permissions, String action, String role) {
	List<String> roles = switch (action) {
		case "view" -> permissions.view();
		case "create" -> permissions.create();
		case "update" -> permissions.update();
		case "delete" -> permissions.delete();
		default -> List.of();
	};
	if (role == null || roles.stream().noneMatch(role::equalsIgnoreCase)) {
		throw new BusinessException(ApiErrorCode.FORBIDDEN, "Bạn không có quyền thực hiện thao tác này.");
	}
}
```

Return `CustomRecordData` and `CustomRecordPageData`.

- [ ] **Step 5: Write and implement `CustomRecordControllerWebMvcTest`**

Test these endpoints:

```java
GET /api/v1/custom/pages/phieu_kiem_hang_hong/records
POST /api/v1/custom/pages/phieu_kiem_hang_hong/records
PATCH /api/v1/custom/pages/phieu_kiem_hang_hong/records/1
DELETE /api/v1/custom/pages/phieu_kiem_hang_hong/records/1
```

Use authorities:

```java
jwt().authorities(new SimpleGrantedAuthority("can_use_custom_entities")).jwt(j -> j.subject("1").claim("role", "Owner"))
```

- [ ] **Step 6: Implement `CustomRecordController`**

Create controller at `@RequestMapping("/api/v1/custom/pages/{pageKey}/records")` with list/create/get/patch/delete. Return envelopes for all non-delete responses. Delete returns envelope with deleted id:

```java
return ResponseEntity.ok(ApiSuccessResponse.of(Map.of("id", recordId, "deleted", true), "Đã xóa bản ghi"));
```

- [ ] **Step 7: Run record tests**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomRecordServiceTest,CustomRecordControllerWebMvcTest test
```

Expected: pass.

- [ ] **Step 8: Commit runtime records**

```powershell
git add backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/repository/CustomRecordJdbcRepository.java backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/service/CustomRecordService.java backend/smart-erp/src/main/java/com/example/smart_erp/custominterface/controller/CustomRecordController.java backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/service/CustomRecordServiceTest.java backend/smart-erp/src/test/java/com/example/smart_erp/custominterface/controller/CustomRecordControllerWebMvcTest.java
git commit -m "feat(custom-builder): add runtime record api"
```

---

## Task 7: Frontend API Types And Client

**Files:**
- Create: `frontend/mini-erp/src/features/custom-builder/api/customBuilderTypes.ts`
- Modify: `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts`
- Test: `frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.test.ts`

- [ ] **Step 1: Create frontend types**

Create `customBuilderTypes.ts`:

```ts
import type { UserRole } from "@/features/auth/store/useAuthStore"
import type { RuntimeCustomPage } from "@/features/custom-builder/runtime/customMenuRuntime"

export type BuilderFieldType =
  | "text"
  | "long_text"
  | "number"
  | "money"
  | "date"
  | "boolean"
  | "single_select"
  | "reference"

export type BuilderFieldDefinition = {
  id?: string
  label: string
  fieldKey: string
  type: BuilderFieldType
  required: boolean
  filterable: boolean
  sortable: boolean
  searchable: boolean
  order: number
  helperText?: string
  options?: string[]
  reference?: { refType?: "core" | "custom"; refEntityKey?: string }
  validation?: Record<string, string>
  defaultValue?: string | number | boolean | null
  readOnly?: boolean
  hidden?: boolean
  status: "Active" | "Draft" | "Archived"
}

export type BuilderViewColumn = {
  fieldKey: string
  label: string
  width: number
  align: "left" | "right" | "center"
  format: "text" | "number" | "currency" | "date" | "badge"
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

export type CustomEntityDefinition = {
  key: string
  label: string
  description?: string
  status: string
  version: number
  draftVersion?: number
  publishedVersion?: number
  etag: string
}

export type ValidationSummary = {
  valid: boolean
  errors: { section: string; message: string; fieldKey?: string }[]
  warnings: { section: string; message: string; fieldKey?: string }[]
}

export type BuilderPageBundle = {
  menuPage: RuntimeCustomPage
  entityDefinition: CustomEntityDefinition
  fields: BuilderFieldDefinition[]
  views: BuilderViewDefinition
  permissions: BuilderPermissionDraft
  validationSummary: ValidationSummary
  etag: string
}

export type RuntimeRecord = {
  id: number
  entityKey: string
  publishedVersion: number
  values: Record<string, string | number | boolean | null>
  state: string
  createdAt?: string
  updatedAt?: string
}

export type RuntimeRecordPage = {
  items: RuntimeRecord[]
  page: number
  size: number
  total: number
}
```

- [ ] **Step 2: Write API tests**

Create `customInterfaceApi.test.ts` with fetch mock verifying paths:

```ts
import { afterEach, describe, expect, it, vi } from "vitest"
import { getBuilderPageBundle, listCustomRecords, createCustomRecord, publishBuilderPage } from "./customInterfaceApi"

describe("customInterfaceApi", () => {
  afterEach(() => vi.restoreAllMocks())

  it("loads builder bundle from production endpoint", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      success: true,
      data: { fields: [], views: { listColumns: [], filterFields: [], formSections: [] }, permissions: {}, validationSummary: { valid: true, errors: [], warnings: [] } },
    }), { status: 200 }))

    await getBuilderPageBundle("abc")

    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/custom/builder/pages/abc/bundle"), expect.any(Object))
  })

  it("publishes with etag body", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ success: true, data: {} }), { status: 200 }))

    await publishBuilderPage("abc", "etag-1")

    const [, init] = vi.mocked(fetch).mock.calls[0]
    expect(String(init?.body)).toContain("etag-1")
  })

  it("lists records with query params", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ success: true, data: { items: [], page: 1, size: 20, total: 0 } }), { status: 200 }))

    await listCustomRecords("abc", { page: 2, size: 10, search: "KH" })

    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/custom/pages/abc/records?page=2&size=10&search=KH"), expect.any(Object))
  })

  it("creates records through runtime endpoint", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ success: true, data: { id: 1, values: { name: "A" } } }), { status: 200 }))

    await createCustomRecord("abc", { name: "A" })

    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/custom/pages/abc/records"), expect.objectContaining({ method: "POST" }))
  })
})
```

- [ ] **Step 3: Implement API client**

Update `customInterfaceApi.ts` to export:

```ts
import { apiJson } from "@/lib/api/http"
import type { BuilderPageBundle, RuntimeRecord, RuntimeRecordPage } from "./customBuilderTypes"
import type { RuntimeCustomMenuFolder } from "@/features/custom-builder/runtime/customMenuRuntime"

export type BuilderMenuTree = {
  treeEtag: string
  folders: RuntimeCustomMenuFolder[]
}

export function getBuilderMenuTree() {
  return apiJson<BuilderMenuTree>("/api/v1/custom/menu-tree", { method: "GET", auth: true })
}

export function getBuilderPageBundle(pageKey: string) {
  return apiJson<BuilderPageBundle>(`/api/v1/custom/builder/pages/${encodeURIComponent(pageKey)}/bundle`, {
    method: "GET",
    auth: true,
  })
}

export function saveBuilderPageBundle(pageKey: string, bundle: BuilderPageBundle) {
  return apiJson<BuilderPageBundle>(`/api/v1/custom/builder/pages/${encodeURIComponent(pageKey)}/bundle`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(bundle),
  })
}

export function publishBuilderPage(pageKey: string, etag: string) {
  return apiJson<BuilderPageBundle>(`/api/v1/custom/builder/pages/${encodeURIComponent(pageKey)}/publish`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({ etag }),
  })
}

export function getRuntimeCustomMenu() {
  return apiJson<BuilderMenuTree>("/api/v1/custom/runtime-menu", { method: "GET", auth: true })
}

export function getRuntimeCustomPageBundle(pageKey: string) {
  return apiJson<BuilderPageBundle>(`/api/v1/custom/pages/${encodeURIComponent(pageKey)}/runtime`, {
    method: "GET",
    auth: true,
  })
}

export function listCustomRecords(pageKey: string, params: { page: number; size: number; search?: string }) {
  const qs = new URLSearchParams({ page: String(params.page), size: String(params.size) })
  if (params.search?.trim()) qs.set("search", params.search.trim())
  return apiJson<RuntimeRecordPage>(`/api/v1/custom/pages/${encodeURIComponent(pageKey)}/records?${qs}`, {
    method: "GET",
    auth: true,
  })
}

export function createCustomRecord(pageKey: string, values: RuntimeRecord["values"]) {
  return apiJson<RuntimeRecord>(`/api/v1/custom/pages/${encodeURIComponent(pageKey)}/records`, {
    method: "POST",
    auth: true,
    body: JSON.stringify({ values }),
  })
}

export function updateCustomRecord(pageKey: string, recordId: number, values: RuntimeRecord["values"]) {
  return apiJson<RuntimeRecord>(`/api/v1/custom/pages/${encodeURIComponent(pageKey)}/records/${recordId}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify({ values }),
  })
}

export function deleteCustomRecord(pageKey: string, recordId: number) {
  return apiJson<{ id: number; deleted: boolean }>(`/api/v1/custom/pages/${encodeURIComponent(pageKey)}/records/${recordId}`, {
    method: "DELETE",
    auth: true,
  })
}
```

- [ ] **Step 4: Run API tests**

Run:

```powershell
cd frontend/mini-erp
npm test -- --run src/features/custom-builder/api/customInterfaceApi.test.ts
```

Expected: pass.

- [ ] **Step 5: Commit frontend API**

```powershell
git add frontend/mini-erp/src/features/custom-builder/api/customBuilderTypes.ts frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.ts frontend/mini-erp/src/features/custom-builder/api/customInterfaceApi.test.ts
git commit -m "feat(custom-builder): add production frontend api"
```

---

## Task 8: Frontend Runtime Page Uses Real Records

**Files:**
- Modify: `CustomRuntimePage.tsx`
- Test: `CustomRuntimePage.test.tsx`

- [ ] **Step 1: Write runtime page test**

Create `CustomRuntimePage.test.tsx` mocking `customInterfaceApi`:

```tsx
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { describe, expect, it, vi } from "vitest"
import { CustomRuntimePage } from "./CustomRuntimePage"

vi.mock("@/context/PageTitleContext", () => ({ usePageTitle: () => ({ setTitle: vi.fn() }) }))
vi.mock("@/features/auth/store/useAuthStore", () => ({
  useAuthStore: (selector: any) => selector({
    menuPermissions: { can_manage_inventory: true, can_use_custom_entities: true },
    user: { role: "Owner" },
  }),
}))
vi.mock("@/features/custom-builder/api/customInterfaceApi", () => ({
  getRuntimeCustomPageBundle: vi.fn(async () => ({
    menuPage: {
      key: "abc",
      label: "Custom Page",
      pageType: "record_list",
      status: "Published",
      roles: ["Owner"],
      routePath: "/custom/abc",
      entityKey: "entity",
      publishedVersion: 1,
      hasDraft: false,
      validationSummary: { valid: true, errors: [], warnings: [] },
    },
    fields: [{ label: "Tên", fieldKey: "name", type: "text", required: true, status: "Active" }],
    views: { listColumns: [{ fieldKey: "name", label: "Tên", width: 160, align: "left", format: "text" }], filterFields: [], defaultSort: "name asc", formSections: [{ id: "main", title: "Thông tin", fieldKeys: ["name"] }] },
    permissions: { view: ["Owner"], create: ["Owner"], update: ["Owner"], delete: ["Owner"] },
    validationSummary: { valid: true, errors: [], warnings: [] },
    etag: "etag",
  })),
  listCustomRecords: vi.fn(async () => ({ items: [{ id: 1, entityKey: "entity", publishedVersion: 1, values: { name: "Bản ghi A" }, state: "Active" }], page: 1, size: 20, total: 1 })),
  createCustomRecord: vi.fn(async (_pageKey, values) => ({ id: 2, entityKey: "entity", publishedVersion: 1, values, state: "Active" })),
}))

describe("CustomRuntimePage", () => {
  it("renders records from api and creates a record", async () => {
    const api = await import("@/features/custom-builder/api/customInterfaceApi")
    render(
      <MemoryRouter initialEntries={["/custom/abc"]}>
        <Routes>
          <Route path="/custom/:pageKey" element={<CustomRuntimePage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText("Bản ghi A")).toBeTruthy()
    await userEvent.click(screen.getByRole("button", { name: /Tạo bản ghi/ }))
    await userEvent.type(screen.getByLabelText(/Tên/), "Bản ghi B")
    await userEvent.click(screen.getByRole("button", { name: /Lưu bản nháp/ }))

    await waitFor(() => expect(api.createCustomRecord).toHaveBeenCalledWith("abc", { name: "Bản ghi B" }))
  })
})
```

- [ ] **Step 2: Run runtime test to verify failure**

Run:

```powershell
cd frontend/mini-erp
npm test -- --run src/features/custom-builder/pages/CustomRuntimePage.test.tsx
```

Expected: FAIL because current page imports mock adapter and save button has no create handler.

- [ ] **Step 3: Replace runtime mock usage**

In `CustomRuntimePage.tsx`:

- Replace imports from `customBuilderMockAdapter` with:

```ts
import {
  createCustomRecord,
  getRuntimeCustomPageBundle,
  listCustomRecords,
  updateCustomRecord,
  deleteCustomRecord,
} from "@/features/custom-builder/api/customInterfaceApi"
import type { BuilderPageBundle, RuntimeRecord } from "@/features/custom-builder/api/customBuilderTypes"
```

- Replace `sampleRecords` state with:

```ts
const [recordsPage, setRecordsPage] = useState<{ items: RuntimeRecord[]; page: number; size: number; total: number }>({
  items: [],
  page: 1,
  size: 20,
  total: 0,
})
```

- Add `loadRecords`:

```ts
const loadRecords = async (nextPage = 1) => {
  if (!pageKey) return
  const data = await listCustomRecords(pageKey, { page: nextPage, size: recordsPage.size, search: query })
  setRecordsPage(data)
}
```

- After loading bundle, call `await loadRecords(1)`.
- Set `records = recordsPage.items`.
- Add save handler:

```ts
const saveRecord = async () => {
  if (!pageKey || mode === "detail") return
  if (mode === "create") {
    await createCustomRecord(pageKey, draftValues)
  } else if (selectedRecord) {
    await updateCustomRecord(pageKey, selectedRecord.id, draftValues)
  }
  setMode("detail")
  await loadRecords(recordsPage.page)
}
```

- Wire button:

```tsx
<Button type="button" className="bg-slate-900 text-white hover:bg-slate-800" disabled={mode === "detail" || !canMutate} onClick={() => void saveRecord()}>
```

- [ ] **Step 4: Run runtime test**

Run:

```powershell
cd frontend/mini-erp
npm test -- --run src/features/custom-builder/pages/CustomRuntimePage.test.tsx
```

Expected: pass.

- [ ] **Step 5: Commit runtime page**

```powershell
git add frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.tsx frontend/mini-erp/src/features/custom-builder/pages/CustomRuntimePage.test.tsx
git commit -m "feat(custom-builder): render runtime records from api"
```

---

## Task 9: Frontend Builder Page Uses Real Builder API

**Files:**
- Modify: `CustomBuilderPage.tsx`
- Test: `npx tsc --noEmit`

- [ ] **Step 1: Replace builder imports**

In `CustomBuilderPage.tsx`, remove imports from `customBuilderMockAdapter` for runtime app flow. Replace with:

```ts
import {
  getBuilderMenuTree,
  getBuilderPageBundle,
  saveBuilderPageBundle,
  publishBuilderPage,
} from "@/features/custom-builder/api/customInterfaceApi"
import type {
  BuilderFieldDefinition,
  BuilderFieldType,
  BuilderPageBundle,
  BuilderViewColumn,
  BuilderPermissionDraft,
  ValidationSummary,
} from "@/features/custom-builder/api/customBuilderTypes"
```

- [ ] **Step 2: Update list loading**

Replace:

```ts
const tree = await getMockBuilderMenuTree()
```

with:

```ts
const tree = await getBuilderMenuTree()
```

Replace bundle loading map with:

```ts
const bundleEntries = await Promise.all(
  tree.folders.flatMap((folder) =>
    folder.children.map(async (page) => [page.key, await getBuilderPageBundle(page.key)] as const),
  ),
)
```

- [ ] **Step 3: Update editor open/save/publish**

Replace:

```ts
const bundle = bundleCache[pageKey] ?? await getMockBuilderPageBundle(pageKey)
```

with:

```ts
const bundle = bundleCache[pageKey] ?? await getBuilderPageBundle(pageKey)
```

Replace save:

```ts
const saved = await saveBuilderPageBundle(selectedBundle.menuPage.key, selectedBundle)
```

Replace publish:

```ts
const publish = async () => {
  if (!selectedBundle) return
  setPublishing(true)
  try {
    const published = await publishBuilderPage(selectedBundle.menuPage.key, selectedBundle.etag)
    setSelectedBundle(published)
    setBundleCache((current) => ({ ...current, [published.menuPage.key]: published }))
    setDirty(false)
    setConflict(false)
    toast.success("Đã publish cấu hình giao diện")
  } catch (error) {
    setConflict(true)
    toast.error(error instanceof Error ? error.message : "Không publish được cấu hình")
  } finally {
    setPublishing(false)
  }
}
```

Update prop:

```tsx
onPublish={() => void publish()}
```

- [ ] **Step 4: Remove misleading mock copy**

Replace UI text:

- `"Dữ liệu hiện tại đến từ fixture frontend."` -> `"Dữ liệu cấu hình được lưu trên backend."`
- `"Preview dùng sample data trong fixture, không phải runtime thật."` -> `"Preview dùng dữ liệu nhập thử trong cấu hình hiện tại."`
- `"Backend: không sửa. ai_python: không sửa. Mock adapter frontend đang dùng."` -> `"Backend là nguồn dữ liệu chính cho cấu hình và runtime."`
- `"Mock 409"` copy is deleted.

- [ ] **Step 5: Typecheck frontend**

Run:

```powershell
cd frontend/mini-erp
npx tsc --noEmit
```

Expected: pass. Fix type drift from `customBuilderMockAdapter` removal by moving local-only helper types into `customBuilderTypes.ts`.

- [ ] **Step 6: Commit builder migration**

```powershell
git add frontend/mini-erp/src/features/custom-builder/pages/CustomBuilderPage.tsx frontend/mini-erp/src/features/custom-builder/api/customBuilderTypes.ts
git commit -m "feat(custom-builder): connect builder ui to api"
```

---

## Task 10: Sidebar And Runtime Helper Cleanup

**Files:**
- Modify: `Sidebar.tsx`, `customMenuRuntime.ts`

- [ ] **Step 1: Remove production mock fallback from Sidebar**

In `Sidebar.tsx`, remove:

```ts
import { getMockRuntimeCustomMenu } from "@/features/custom-builder/api/customBuilderMockAdapter"
```

Replace catch block with development-only fallback:

```ts
.catch(() => {
  if (import.meta.env.DEV && import.meta.env.VITE_USE_CUSTOM_BUILDER_FIXTURE === "true") {
    import("@/features/custom-builder/api/customBuilderMockAdapter").then(({ getMockRuntimeCustomMenu }) => {
      getMockRuntimeCustomMenu().then((data) => {
        if (alive) setRuntimeFolders(data.folders ?? [])
      })
    })
    return
  }
  if (alive) setRuntimeFolders([])
})
```

- [ ] **Step 2: Remove default mock catalog source from runtime helper**

In `customMenuRuntime.ts`, remove:

```ts
import { customRuntimeCatalog } from "@/features/custom-builder/api/customBuilderMockAdapter"
```

Change defaults:

```ts
export function getRuntimeCustomMenuForUser(
  permissions: MenuPermissions,
  role: UserRole | null,
  source: RuntimeCustomFolder[],
): RuntimeCustomMenuFolder[] {
```

and:

```ts
export function findRuntimeCustomPage(pageKey: string, source: RuntimeCustomFolder[]) {
```

Update callers to pass `runtimeFolders`.

- [ ] **Step 3: Verify no production imports remain**

Run:

```powershell
cd frontend/mini-erp
rg -n "customBuilderMockAdapter|getMockBuilder|getMockRuntime|fixture frontend|Mock 409" src
```

Expected: no hits in app runtime files. Hits in tests are acceptable only if the path includes `.test.`.

- [ ] **Step 4: Typecheck**

Run:

```powershell
cd frontend/mini-erp
npx tsc --noEmit
```

Expected: pass.

- [ ] **Step 5: Commit cleanup**

```powershell
git add frontend/mini-erp/src/components/shared/layout/Sidebar.tsx frontend/mini-erp/src/features/custom-builder/runtime/customMenuRuntime.ts
git commit -m "feat(custom-builder): remove production fixture fallback"
```

---

## Task 11: End-To-End Happy Path

**Files:**
- Create: `frontend/mini-erp/e2e/custom-builder-mvp.spec.ts`
- May require backend and frontend dev servers running against a migrated local database

- [ ] **Step 1: Write E2E test**

Create:

```ts
import { test, expect } from "@playwright/test"

test("custom builder mvp publish and runtime record flow", async ({ page }) => {
  await page.goto("/login")
  await page.getByLabel(/Tên đăng nhập|Email|Username/i).fill("admin")
  await page.getByLabel(/Mật khẩu|Password/i).fill("admin123")
  await page.getByRole("button", { name: /Đăng nhập|Login/i }).click()

  await page.goto("/settings/custom-builder")
  await expect(page.getByRole("heading", { name: /Trình thiết kế giao diện/ })).toBeVisible()
  await page.getByRole("button", { name: /Sửa/ }).first().click()
  await expect(page.getByText(/Backend là nguồn dữ liệu chính/)).toBeVisible()
  await page.getByRole("button", { name: /^Publish$/ }).click()
  await expect(page.getByText(/Đã publish cấu hình giao diện|Đã publish/)).toBeVisible()

  await page.goto("/custom/phieu_kiem_hang_hong")
  await expect(page.getByRole("heading", { name: /Phiếu kiểm hàng hỏng/ })).toBeVisible()
  await page.getByRole("button", { name: /Tạo bản ghi/ }).click()
  await page.getByLabel(/Mã phiếu/).fill("KH-2026-0099")
  await page.getByLabel(/Sản phẩm/).fill("Sản phẩm test")
  await page.getByLabel(/Vị trí kho/).fill("Kho test")
  await page.getByLabel(/Số lượng hỏng/).fill("3")
  await page.getByRole("button", { name: /Lưu bản nháp/ }).click()

  await page.reload()
  await expect(page.getByText("KH-2026-0099")).toBeVisible()
})
```

- [ ] **Step 2: Run targeted E2E**

Run with backend and frontend dev servers running:

```powershell
cd frontend/mini-erp
npm run test:e2e -- custom-builder-mvp.spec.ts
```

Expected: pass. If local auth seed differs, update only credentials in this spec and document the actual seed user in the commit message.

- [ ] **Step 3: Commit E2E**

```powershell
git add frontend/mini-erp/e2e/custom-builder-mvp.spec.ts
git commit -m "test(custom-builder): cover mvp runtime flow"
```

---

## Task 12: Final Verification And Regression Sweep

**Files:**
- No planned code files

- [ ] **Step 1: Backend targeted tests**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -Dtest=CustomMetadataValidatorTest,CustomBuilderServiceTest,CustomBuilderControllerWebMvcTest,CustomRecordServiceTest,CustomRecordControllerWebMvcTest test
```

Expected: all targeted custom-builder tests pass.

- [ ] **Step 2: Backend compile**

Run:

```powershell
cd backend/smart-erp
./mvnw -q -DskipTests compile
```

Expected: exit 0.

- [ ] **Step 3: Frontend targeted tests**

Run:

```powershell
cd frontend/mini-erp
npm test -- --run src/features/custom-builder/api/customInterfaceApi.test.ts src/features/custom-builder/pages/CustomRuntimePage.test.tsx
```

Expected: all targeted custom-builder tests pass.

- [ ] **Step 4: Frontend typecheck**

Run:

```powershell
cd frontend/mini-erp
npx tsc --noEmit
```

Expected: exit 0.

- [ ] **Step 5: Fixture import gate**

Run:

```powershell
cd frontend/mini-erp
rg -n "customBuilderMockAdapter|getMockBuilder|getMockRuntime|Mock 409|fixture frontend" src
```

Expected: no production runtime imports or user-facing mock strings.

- [ ] **Step 6: Full frontend suite status**

Run:

```powershell
cd frontend/mini-erp
npm test -- --run
```

Expected: existing suite status is recorded. If unrelated legacy tests still fail, list exact failing files in the final report and do not claim the full suite is green.

- [ ] **Step 7: Final git status**

Run:

```powershell
git status --short
```

Expected: clean worktree after all commits, or only explicitly documented uncommitted artifacts.

---

## Self-Review

Spec coverage:

- Metadata persistence: Tasks 1, 2, 4, 5.
- Publish snapshots: Tasks 1, 4, 5.
- Runtime menu/page from backend: Tasks 5, 10.
- Runtime records CRUD: Task 6 and Task 8.
- Frontend removal of mock runtime path: Tasks 7, 8, 9, 10.
- Security and permission checks: Tasks 5 and 6.
- Verification and rollout criteria: Task 12.

Type consistency:

- Backend uses `CustomBuilderBundleData` for builder and runtime bundle responses.
- Frontend uses `BuilderPageBundle` as the matching type.
- Runtime records use `{ values }` request envelope on both backend and frontend.

Scope check:

- Workflow, logic connector, inventory effect, and AI remain outside MVP.
- JSONB record storage is used; no generated physical tables are introduced.
