package com.example.smart_erp.ai.inventorydraft.dto;

import java.time.Instant;

import com.fasterxml.jackson.databind.JsonNode;

public record InventoryDraftResponse(
		String id,
		String entityType,
		String status,
		JsonNode header,
		JsonNode lineColumns,
		JsonNode lines,
		JsonNode meta,
		JsonNode commitResult,
		String conversationId,
		Instant createdAt,
		Instant updatedAt,
		Instant expiresAt) {
}
