package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomFolderRequest(
		String key,
		String label,
		String icon,
		String description,
		List<String> visibilityRoles,
		Integer sortOrder,
		String etag) {
}
