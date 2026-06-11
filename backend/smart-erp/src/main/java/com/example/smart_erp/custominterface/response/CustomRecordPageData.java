package com.example.smart_erp.custominterface.response;

import java.util.List;

public record CustomRecordPageData(
		List<CustomRecordData> items,
		int page,
		int size,
		long total) {
}
