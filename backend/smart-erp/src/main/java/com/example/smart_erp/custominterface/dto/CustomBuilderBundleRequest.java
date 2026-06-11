package com.example.smart_erp.custominterface.dto;

import java.util.List;

public record CustomBuilderBundleRequest(
		CustomPageRequest menuPage,
		String entityKey,
		String entityLabel,
		String entityDescription,
		List<CustomFieldRequest> fields,
		CustomViewRequest views,
		CustomPermissionRequest permissions,
		String etag) {
}
