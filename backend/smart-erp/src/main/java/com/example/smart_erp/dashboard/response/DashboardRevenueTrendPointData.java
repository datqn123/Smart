package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;

public record DashboardRevenueTrendPointData(String date, String label, BigDecimal revenue, long orders) {
}
