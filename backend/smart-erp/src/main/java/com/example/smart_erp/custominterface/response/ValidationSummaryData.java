package com.example.smart_erp.custominterface.response;

import java.util.List;

public record ValidationSummaryData(boolean valid, List<Item> errors, List<Item> warnings) {
	public static ValidationSummaryData ok() {
		return new ValidationSummaryData(true, List.of(), List.of());
	}

	public record Item(String section, String message, String fieldKey) {
		public Item(String section, String message) {
			this(section, message, null);
		}
	}
}
