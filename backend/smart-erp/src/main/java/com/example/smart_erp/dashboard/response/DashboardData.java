package com.example.smart_erp.dashboard.response;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.ALWAYS)
public record DashboardData(
		DashboardFinancialData financial,
		List<DashboardRevenueTrendPointData> revenueTrend,
		DashboardChannelBreakdownData channelBreakdown,
		DashboardKpiData kpis,
		List<DashboardRecentOrderData> recentOrders,
		List<DashboardPendingApprovalData> pendingApprovals,
		List<DashboardTopCustomerData> topCustomers,
		DashboardCashflowData cashflow,
		List<DashboardLowStockAlertData> lowStockAlerts) {
}
