package com.example.smart_erp.ai.inventorydraft;

import java.util.Locale;
import java.util.Optional;

public enum InventoryEntityType {
	STOCK_RECEIPT("stock_receipt");

	private final String wireValue;

	InventoryEntityType(String wireValue) {
		this.wireValue = wireValue;
	}

	public String wireValue() {
		return wireValue;
	}

	public static Optional<InventoryEntityType> parse(String raw) {
		if (raw == null || raw.isBlank()) {
			return Optional.empty();
		}
		String n = raw.trim().toLowerCase(Locale.ROOT);
		for (InventoryEntityType t : values()) {
			if (t.wireValue.equals(n)) {
				return Optional.of(t);
			}
		}
		return Optional.empty();
	}
}
