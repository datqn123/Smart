package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;

public record DashboardFinancialData(
		BigDecimal todayRevenue,
		BigDecimal yesterdayRevenue,
		long todayOrders,
		BigDecimal pctChange,
		BigDecimal avgOrderValue) {
}
