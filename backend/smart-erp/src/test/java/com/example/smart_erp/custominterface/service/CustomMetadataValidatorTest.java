package com.example.smart_erp.custominterface.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Arrays;
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

	private CustomFieldRequest field(String key, String label, String type, boolean required) {
		return new CustomFieldRequest(null, label, key, type, required, true, true, true, 0, null,
				mapper.createArrayNode(), mapper.createObjectNode(), mapper.createObjectNode(), null, false, false, "Active");
	}
}
