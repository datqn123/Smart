package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;
import java.time.Instant;

public record DashboardRecentOrderData(
		int id,
		String orderCode,
		String orderChannel,
		String customerName,
		BigDecimal finalAmount,
		String status,
		Instant createdAt) {
}
