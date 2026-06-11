package com.example.smart_erp.custominterface.response;

import com.fasterxml.jackson.databind.JsonNode;

public record CustomViewData(
		JsonNode listColumns,
		JsonNode filterFields,
		String defaultSort,
		JsonNode formSections,
		String previewMode) {
}
