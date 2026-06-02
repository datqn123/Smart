package com.example.smart_erp.settings.tablecolumns.dto;

import java.util.List;

public record SaveTableColumnSettingsRequest(String scope, List<Item> items) {
	public record Item(String tableKey, List<String> hiddenColumns, List<String> columnOrder) {
	}
}
