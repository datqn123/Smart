package com.example.smart_erp.dashboard.response;

public record DashboardLowStockAlertData(
		long id,
		String productName,
		String skuCode,
		int quantity,
		int minQuantity,
		String unitName) {
}
