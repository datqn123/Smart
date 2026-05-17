package com.example.smart_erp.ai.inventorydraft.dto;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.validation.constraints.NotNull;

public record InventoryDraftPatchRequest(
		JsonNode header,
		JsonNode lineColumns,
		@NotNull JsonNode lines) {
}
