package com.example.smart_erp.ai.catalogdraft.dto;

import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;

public record CatalogDraftCommitResult(
		int committedCount,
		int failedCount,
		int skippedCount,
		List<CatalogDraftRowCommitOutcome> outcomes,
		JsonNode draft) {
}
