package com.example.smart_erp.ai.catalogdraft.dto;

import java.util.List;

public record CatalogDraftReferenceValidationResult(boolean ok, List<String> issues) {

	public static CatalogDraftReferenceValidationResult success() {
		return new CatalogDraftReferenceValidationResult(true, List.of());
	}

	public static CatalogDraftReferenceValidationResult failure(List<String> issues) {
		return new CatalogDraftReferenceValidationResult(false, List.copyOf(issues));
	}
}
