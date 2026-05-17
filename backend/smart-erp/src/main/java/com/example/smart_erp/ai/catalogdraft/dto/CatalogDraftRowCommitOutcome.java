package com.example.smart_erp.ai.catalogdraft.dto;

import com.fasterxml.jackson.databind.JsonNode;

public record CatalogDraftRowCommitOutcome(
		String rowId,
		boolean success,
		Integer createdEntityId,
		String message,
		JsonNode fieldErrors) {
}
