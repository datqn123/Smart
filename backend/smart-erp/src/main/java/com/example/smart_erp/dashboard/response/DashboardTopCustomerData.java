package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;

public record DashboardTopCustomerData(int id, String name, long orderCount, BigDecimal totalSpent) {
}
