package com.example.smart_erp.ai.inventorydraft.dto;

import java.util.List;

public record DraftReferenceValidationResult(boolean ok, List<String> issues) {

	public static DraftReferenceValidationResult success() {
		return new DraftReferenceValidationResult(true, List.of());
	}

	public static DraftReferenceValidationResult failure(List<String> issues) {
		return new DraftReferenceValidationResult(false, List.copyOf(issues));
	}
}
