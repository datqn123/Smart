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
				: fields.stream().filter(field -> field != null && !"Archived".equals(field.status())).toList();
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
				validateListColumn(column, fieldKeys, errors);
			}
		}
		Set<String> formFieldKeys = new HashSet<>();
		if (view == null || view.formSections() == null || !view.formSections().isArray()) {
			errors.add(new ValidationSummaryData.Item("view", "Form view cần cấu hình sections dạng array."));
		}
		if (view != null && view.formSections() != null && view.formSections().isArray()) {
			for (JsonNode section : view.formSections()) {
				collectFormFieldKeys(section, formFieldKeys);
			}
		}
		for (CustomFieldRequest field : activeFields) {
			if (field.required() && !formFieldKeys.contains(field.fieldKey())) {
				errors.add(new ValidationSummaryData.Item("view", field.label() + " là bắt buộc nên phải có trong form.",
						field.fieldKey()));
			}
		}
	}

	private void validateListColumn(JsonNode column, Set<String> fieldKeys, List<ValidationSummaryData.Item> errors) {
		String fieldKey = column.path("fieldKey").asText(null);
		if (!fieldKeys.contains(fieldKey)) {
			errors.add(new ValidationSummaryData.Item("view",
					"Cột " + fieldKey + " đang tham chiếu field không tồn tại.", fieldKey));
		}
	}

	private void collectFormFieldKeys(JsonNode section, Set<String> formFieldKeys) {
		JsonNode keys = section.path("fieldKeys");
		if (keys.isArray()) {
			keys.forEach(key -> formFieldKeys.add(key.asText()));
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
