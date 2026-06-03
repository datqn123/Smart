package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomPageRequest(
		String parentKey,
		String key,
		String label,
		String icon,
		String description,
		String routePath,
		String entityKey,
		String pageType,
		List<String> visibilityRoles,
		String entityPermission,
		String dataPermission,
		Integer sortOrder,
		String etag) {
}
