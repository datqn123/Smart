package com.example.smart_erp.custominterface.response;

import java.time.Instant;
import java.util.List;

public record CustomMenuFolderData(
		String nodeType,
		String id,
		String key,
		String label,
		String icon,
		String description,
		String status,
		int sortOrder,
		List<String> roles,
		int version,
		Integer draftVersion,
		Integer publishedVersion,
		boolean hasDraft,
		Instant publishedAt,
		String publishedByName,
		Instant updatedAt,
		String updatedByName,
		String etag,
		ValidationSummaryData validationSummary,
		List<CustomMenuPageData> children) {
}
