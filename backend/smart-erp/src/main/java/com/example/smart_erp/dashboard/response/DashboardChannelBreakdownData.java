package com.example.smart_erp.dashboard.response;

import java.math.BigDecimal;

public record DashboardChannelBreakdownData(BigDecimal retail, BigDecimal wholesale, BigDecimal total) {
}
