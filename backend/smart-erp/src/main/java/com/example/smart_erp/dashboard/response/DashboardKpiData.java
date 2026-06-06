package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;
import java.util.Map;

public record DashboardKpiData(
		long totalSkus,
		BigDecimal totalValue,
		long lowStockCount,
		long expiringSoonCount,
		long pendingOrders,
		long allOrdersTotal,
		long pendingApprovals,
		Map<String, Long> approvalByType) {
}
