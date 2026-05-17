package com.example.smart_erp.ai.catalogdraft;

import java.util.Locale;
import java.util.Optional;

public enum CatalogEntityType {
	PRODUCT("product"),
	CATEGORY("category"),
	SUPPLIER("supplier"),
	CUSTOMER("customer");

	private final String wireValue;

	CatalogEntityType(String wireValue) {
		this.wireValue = wireValue;
	}

	public String wireValue() {
		return wireValue;
	}

	public static Optional<CatalogEntityType> parse(String raw) {
		if (raw == null || raw.isBlank()) {
			return Optional.empty();
		}
		String n = raw.trim().toLowerCase(Locale.ROOT);
		for (CatalogEntityType t : values()) {
			if (t.wireValue.equals(n)) {
				return Optional.of(t);
			}
		}
		return Optional.empty();
	}

	public boolean requiresManageProducts() {
		return this == PRODUCT || this == CATEGORY || this == SUPPLIER;
	}

	public boolean requiresManageCustomers() {
		return this == CUSTOMER;
	}
}
