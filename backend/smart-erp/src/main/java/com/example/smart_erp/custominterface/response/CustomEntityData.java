package com.example.smart_erp.custominterface.response;

public record CustomEntityData(
		String key,
		String label,
		String description,
		String status,
		int version,
		Integer draftVersion,
		Integer publishedVersion,
		String etag) {
}
