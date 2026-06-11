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
