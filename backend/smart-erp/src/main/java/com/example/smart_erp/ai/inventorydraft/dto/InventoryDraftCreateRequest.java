package com.example.smart_erp.ai.inventorydraft.dto;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record InventoryDraftCreateRequest(
		@NotBlank @Size(max = 32) String entityType,
		@NotNull JsonNode header,
		@NotNull JsonNode lineColumns,
		@NotNull JsonNode lines,
		JsonNode meta,
		@Size(max = 128) String conversationId) {
}
