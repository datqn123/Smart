package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomReorderRequest(String etag, List<FolderOrder> folders) {
	public record FolderOrder(String key, Integer sortOrder, List<PageOrder> pages) {
	}

	public record PageOrder(String key, Integer sortOrder) {
	}
}
