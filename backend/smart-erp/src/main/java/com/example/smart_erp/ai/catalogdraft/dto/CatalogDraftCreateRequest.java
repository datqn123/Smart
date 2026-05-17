package com.example.smart_erp.ai.catalogdraft.dto;

import com.fasterxml.jackson.databind.JsonNode;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CatalogDraftCreateRequest(
		@NotBlank @Size(max = 32) String entityType,
		@NotNull JsonNode columns,
		@NotNull JsonNode rows,
		JsonNode meta,
		@Size(max = 128) String conversationId) {
}
