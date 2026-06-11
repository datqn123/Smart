package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomBuilderBundleData(
		CustomMenuPageData menuPage,
		CustomEntityData entityDefinition,
		List<CustomFieldData> fields,
		CustomViewData views,
		CustomPermissionData permissions,
		ValidationSummaryData validationSummary,
		String etag) {
}
