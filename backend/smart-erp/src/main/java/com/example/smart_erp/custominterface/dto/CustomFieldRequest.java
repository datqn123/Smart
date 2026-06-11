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
