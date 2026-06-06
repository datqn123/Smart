package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;
import java.time.Instant;

public record DashboardPendingApprovalData(
		String entityType,
		long entityId,
		String transactionCode,
		String type,
		String creatorName,
		BigDecimal totalAmount,
		Instant date) {
}
