package com.example.smart_erp.settings.tablecolumns.response;

import java.time.Instant;
import java.util.List;

public record TableColumnSettingsData(List<ItemData> items) {

	public record ItemData(
			String tableKey,
			String tableLabel,
			List<ColumnData> columns,
			Instant updatedAt,
			String updatedByName) {
	}

	public record ColumnData(
			String key,
			String label,
			boolean required,
			boolean visible,
			int order) {
	}
}

