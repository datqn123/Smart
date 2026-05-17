package com.example.smart_erp.ai.catalogdraft.dto;

import java.time.Instant;

import com.fasterxml.jackson.databind.JsonNode;

public record CatalogDraftResponse(
		String id,
		String entityType,
		String status,
		JsonNode columns,
		JsonNode rows,
		JsonNode meta,
		JsonNode commitResult,
		String conversationId,
		Instant createdAt,
		Instant updatedAt,
		Instant expiresAt) {
}
