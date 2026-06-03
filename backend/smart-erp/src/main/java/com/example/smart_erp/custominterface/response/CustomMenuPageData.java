package com.example.smart_erp.custominterface.response;

import java.time.Instant;
import java.util.List;

public record CustomMenuPageData(
		String nodeType,
		String id,
		String key,
		String label,
		String icon,
		String parentKey,
		String routePath,
		String entityKey,
		String pageType,
		String status,
		int sortOrder,
		String description,
		List<String> roles,
		String entityPermission,
		String dataPermission,
		int version,
		Integer draftVersion,
		Integer publishedVersion,
		boolean hasDraft,
		Instant publishedAt,
		String publishedByName,
		Instant updatedAt,
		String updatedByName,
		String etag,
		ValidationSummaryData validationSummary) {
}
