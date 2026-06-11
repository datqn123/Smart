package com.example.smart_erp.custominterface.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomViewRequest(
		JsonNode listColumns,
		JsonNode filterFields,
		String defaultSort,
		JsonNode formSections,
		String previewMode) {
}
