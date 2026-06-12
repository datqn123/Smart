package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Arrays;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.example.smart_erp.custominterface.dto.CustomFieldRequest;
import com.example.smart_erp.custominterface.dto.CustomPermissionRequest;
import com.example.smart_erp.custominterface.dto.CustomViewRequest;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.fasterxml.jackson.databind.JsonNode;
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
		var columns = mapper.createArrayNode();
		columns.addObject().put("fieldKey", "name").put("label", "Tên");
		var sections = mapper.createArrayNode();
		sections.addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("name"));
		var view = new CustomViewRequest(columns, mapper.createArrayNode().add("name"), "name asc", sections, "desktop");

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(field("name", "Tên", "text", true)),
				view, new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isTrue();
		assertThat(summary.errors()).isEmpty();
	}

	@Test
	void validateDraft_ignoresNullFieldEntries() {
		var columns = mapper.createArrayNode();
		columns.addObject().put("fieldKey", "name").put("label", "Tên");
		var sections = mapper.createArrayNode();
		sections.addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("name"));
		var view = new CustomViewRequest(columns, mapper.createArrayNode().add("name"), "name asc", sections, "desktop");

		var summary = validator.validateDraft("custom_page", "custom_entity",
				Arrays.asList(field("name", "Tên", "text", true), null), view,
				new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isTrue();
		assertThat(summary.errors()).isEmpty();
	}

	@Test
	void validateDraft_rejectsReferenceOutsideAllowlist() {
		var reference = mapper.createObjectNode().put("refType", "core").put("refEntityKey", "unknown_table");
		var field = new CustomFieldRequest(null, "Ref", "ref_key", "reference", true, false, false, false, 0,
				null, mapper.createArrayNode(), reference, mapper.createObjectNode(), null, false, false, "Active");
		var columns = mapper.createArrayNode();
		columns.addObject().put("fieldKey", "ref_key").put("label", "Ref");
		var sections = mapper.createArrayNode();
		sections.addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("ref_key"));

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(field),
				new CustomViewRequest(columns, mapper.createArrayNode(), "ref_key asc", sections, "desktop"),
				new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("reference"));
	}

	@Test
	void validateDraft_acceptsAllowedCoreReference() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(referenceField(mapper.createObjectNode().put("refType", "core").put("refEntityKey", "products"))),
				validView("ref_key"), permissions());

		assertThat(summary.valid()).isTrue();
		assertThat(summary.errors()).isEmpty();
	}

	@Test
	void validateDraft_rejectsReferenceMissingRefType() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(referenceField(mapper.createObjectNode().put("refEntityKey", "products"))), validView("ref_key"),
				permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("refType"));
	}

	@Test
	void validateDraft_rejectsReferenceWrongRefType() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(referenceField(mapper.createObjectNode().put("refType", "custom").put("refEntityKey", "products"))),
				validView("ref_key"), permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("refType"));
	}

	@Test
	void validateDraft_rejectsNonObjectReference() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(referenceField(mapper.getNodeFactory().textNode("products"))), validView("ref_key"),
				permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("object"));
	}

	@Test
	void validateDraft_rejectsObjectShapedListColumns() {
		var columns = mapper.createObjectNode().put("fieldKey", "name").put("label", "Tên");
		var sections = mapper.createArrayNode();
		sections.addObject().put("id", "main").put("title", "Thông tin")
				.set("fieldKeys", mapper.createArrayNode().add("name"));
		var view = new CustomViewRequest(columns, mapper.createArrayNode().add("name"), "name asc", sections, "desktop");

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(field("name", "Tên", "text", true)),
				view, new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("List view"));
	}

	@Test
	void validateDraft_rejectsInvalidPageEntityAndFieldKeyPatterns() {
		var summary = validator.validateDraft("Custom Page", "custom-entity",
				List.of(field("Bad-Key", "Tên", "text", true)), validView("Bad-Key"), permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("pageKey"));
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("entityKey"));
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("fieldKey"));
	}

	@Test
	void validateDraft_rejectsEmptyActiveFieldsAndSkipsArchivedFieldValidation() {
		var archivedField = field("Archived-Key", "", "unsupported", true, mapper.createArrayNode(),
				mapper.createObjectNode(), false, false, "Archived");

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(archivedField),
				viewWith(List.of(), List.of()), permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("tối thiểu một field"));
		assertThat(summary.errors()).noneSatisfy(error -> assertThat(error.message()).contains("tên hiển thị"));
		assertThat(summary.errors()).noneSatisfy(error -> assertThat(error.message()).contains("loại field không hỗ trợ"));
		assertThat(summary.errors()).noneSatisfy(error -> assertThat(error.message()).contains("fieldKey"));
		assertThat(summary.errors()).noneSatisfy(error -> assertThat(error.message()).contains("bắt buộc nên phải có"));
	}

	@Test
	void validateDraft_rejectsMissingFieldLabelAndUnsupportedFieldType() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("metadata", " ", "json", false)), validView("metadata"), permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("tên hiển thị"));
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("loại field không hỗ trợ"));
	}

	@Test
	void validateDraft_rejectsSingleSelectWithoutNonEmptyArrayOptions() {
		var objectOptionsField = field("status_object", "Trạng thái object", "single_select", false,
				mapper.createObjectNode().put("value", "draft"), mapper.createObjectNode(), false, false, "Active");
		var emptyOptionsField = field("status_empty", "Trạng thái rỗng", "single_select", false,
				mapper.createArrayNode(), mapper.createObjectNode(), false, false, "Active");

		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(objectOptionsField, emptyOptionsField), validView("status_object", "status_empty"), permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("Trạng thái object")
				.contains("tối thiểu một option"));
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("Trạng thái rỗng")
				.contains("tối thiểu một option"));
	}

	@Test
	void validateDraft_rejectsListColumnsReferencingUnknownFieldsAndObjectShapedFormSections() {
		var columns = mapper.createArrayNode();
		columns.addObject().put("fieldKey", "missing_field").put("label", "Thiếu");

		var unknownColumnSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)),
				new CustomViewRequest(columns, mapper.createArrayNode(), "name asc", formSections("name"), "desktop"),
				permissions());
		var objectFormSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)),
				new CustomViewRequest(listColumns("name"), mapper.createArrayNode(), "name asc",
						mapper.createObjectNode().put("id", "main"), "desktop"),
				permissions());

		assertThat(unknownColumnSummary.valid()).isFalse();
		assertThat(unknownColumnSummary.errors())
				.anySatisfy(error -> assertThat(error.message()).contains("missing_field").contains("không tồn tại"));
		assertThat(objectFormSummary.valid()).isFalse();
		assertThat(objectFormSummary.errors()).anySatisfy(error -> assertThat(error.message()).contains("sections dạng array"));
	}

	@Test
	void validateDraft_rejectsMalformedListColumnEntry() {
		var columns = mapper.createArrayNode();
		columns.add("name");

		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)),
				new CustomViewRequest(columns, mapper.createArrayNode(), "name asc", formSections("name"), "desktop"),
				permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("list view").contains("object"));
	}

	@Test
	void validateDraft_rejectsMalformedFormSectionAndNonArrayFieldKeys() {
		var malformedSections = mapper.createArrayNode();
		malformedSections.add("main");
		var malformedSectionSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)),
				new CustomViewRequest(listColumns("name"), mapper.createArrayNode(), "name asc", malformedSections,
						"desktop"),
				permissions());

		var nonArrayFieldKeysSections = mapper.createArrayNode();
		nonArrayFieldKeysSections.addObject().put("id", "main").put("fieldKeys", "name");
		var nonArrayFieldKeysSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)),
				new CustomViewRequest(listColumns("name"), mapper.createArrayNode(), "name asc", nonArrayFieldKeysSections,
						"desktop"),
				permissions());

		assertThat(malformedSectionSummary.valid()).isFalse();
		assertThat(malformedSectionSummary.errors())
				.anySatisfy(error -> assertThat(error.message()).contains("Form section").contains("object"));
		assertThat(nonArrayFieldKeysSummary.valid()).isFalse();
		assertThat(nonArrayFieldKeysSummary.errors())
				.anySatisfy(error -> assertThat(error.message()).contains("fieldKeys").contains("array"));
	}

	@Test
	void validateDraft_rejectsUnknownFormFieldKey() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)),
				new CustomViewRequest(listColumns("name"), mapper.createArrayNode(), "name asc",
						formSections("missing_field"), "desktop"),
				permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors())
				.anySatisfy(error -> assertThat(error.message()).contains("missing_field").contains("form"));
	}

	@Test
	void validateDraft_rejectsRequiredActiveFieldMissingFromForm() {
		var summary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", true), field("note", "Ghi chú", "text", false)),
				viewWith(List.of("name"), List.of("note")), permissions());

		assertThat(summary.valid()).isFalse();
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.fieldKey()).isEqualTo("name"));
		assertThat(summary.errors()).anySatisfy(error -> assertThat(error.message()).contains("bắt buộc nên phải có"));
	}

	@Test
	void validateDraft_rejectsMissingEmptyAndUnknownPermissionRoles() {
		var missingSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)), validView("name"), null);
		var emptyActionSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)), validView("name"),
				new CustomPermissionRequest(List.of("Owner"), List.of(), List.of("Owner"), List.of("Owner")));
		var invalidRoleSummary = validator.validateDraft("custom_page", "custom_entity",
				List.of(field("name", "Tên", "text", false)), validView("name"),
				new CustomPermissionRequest(List.of("Guest"), List.of("Owner"), List.of("Owner"), List.of("Owner")));

		assertThat(missingSummary.valid()).isFalse();
		assertThat(missingSummary.errors()).anySatisfy(error -> assertThat(error.message()).contains("quyền truy cập"));
		assertThat(emptyActionSummary.valid()).isFalse();
		assertThat(emptyActionSummary.errors()).anySatisfy(error -> assertThat(error.message()).contains("Action create"));
		assertThat(invalidRoleSummary.valid()).isFalse();
		assertThat(invalidRoleSummary.errors()).anySatisfy(error -> assertThat(error.message()).contains("Role Guest"));
	}

	@Test
	void validateDraft_warnsWhenFilterableOrSortableFieldsNeedBackendIndexes() {
		var filterableField = field("customer_name", "Khách hàng", "text", false, mapper.createArrayNode(),
				mapper.createObjectNode(), true, false, "Active");
		var sortableField = field("due_date", "Ngày hạn", "date", false, mapper.createArrayNode(),
				mapper.createObjectNode(), false, true, "Active");

		var summary = validator.validateDraft("custom_page", "custom_entity", List.of(filterableField, sortableField),
				validView("customer_name", "due_date"), permissions());

		assertThat(summary.valid()).isTrue();
		assertThat(summary.errors()).isEmpty();
		assertThat(summary.warnings()).extracting(ValidationSummaryData.Item::fieldKey)
				.containsExactlyInAnyOrder("customer_name", "due_date");
		assertThat(summary.warnings()).allSatisfy(
				warning -> assertThat(warning.message()).contains("cần index backend"));
	}

	private CustomFieldRequest field(String key, String label, String type, boolean required) {
		return field(key, label, type, required, mapper.createArrayNode(), mapper.createObjectNode(), false, false, "Active");
	}

	private CustomFieldRequest field(String key, String label, String type, boolean required, JsonNode options,
			JsonNode reference, boolean filterable, boolean sortable, String status) {
		return new CustomFieldRequest(null, label, key, type, required, filterable, sortable, true, 0, null, options,
				reference, mapper.createObjectNode(), null, false, false, status);
	}

	private CustomFieldRequest referenceField(JsonNode reference) {
		return field("ref_key", "Ref", "reference", false, mapper.createArrayNode(), reference, false, false, "Active");
	}

	private CustomViewRequest validView(String... fieldKeys) {
		return viewWith(List.of(fieldKeys), List.of(fieldKeys));
	}

	private CustomViewRequest viewWith(List<String> listFieldKeys, List<String> formFieldKeys) {
		return new CustomViewRequest(listColumns(listFieldKeys), mapper.createArrayNode(), "name asc",
				formSections(formFieldKeys), "desktop");
	}

	private JsonNode listColumns(String... fieldKeys) {
		return listColumns(List.of(fieldKeys));
	}

	private JsonNode listColumns(List<String> fieldKeys) {
		var columns = mapper.createArrayNode();
		for (String fieldKey : fieldKeys) {
			columns.addObject().put("fieldKey", fieldKey).put("label", fieldKey);
		}
		return columns;
	}

	private JsonNode formSections(String... fieldKeys) {
		return formSections(List.of(fieldKeys));
	}

	private JsonNode formSections(List<String> fieldKeys) {
		var fields = mapper.createArrayNode();
		fieldKeys.forEach(fields::add);
		var sections = mapper.createArrayNode();
		sections.addObject().put("id", "main").put("title", "Thông tin").set("fieldKeys", fields);
		return sections;
	}

	private CustomPermissionRequest permissions() {
		return new CustomPermissionRequest(List.of("Owner"), List.of("Owner"), List.of("Owner"), List.of("Owner"));
	}
}
