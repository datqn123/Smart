package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;

public record DashboardCashflowData(BigDecimal income, BigDecimal expense, BigDecimal net) {
}
