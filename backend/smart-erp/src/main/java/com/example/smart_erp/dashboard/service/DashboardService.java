package com.example.smart_erp.dashboard.service;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.dashboard.repository.DashboardJdbcRepository;
import com.example.smart_erp.dashboard.response.DashboardChannelBreakdownData;
import com.example.smart_erp.dashboard.response.DashboardData;
import com.example.smart_erp.dashboard.response.DashboardFinancialData;
import com.example.smart_erp.dashboard.response.DashboardKpiData;
import com.example.smart_erp.dashboard.response.DashboardRevenueTrendPointData;
import com.example.smart_erp.inventory.response.InventorySummaryData;

@Service
public class DashboardService {

	private static final Set<String> FINANCIAL_ROLES = Set.of("Owner", "Admin", "Manager");
	private static final int DEFAULT_TREND_DAYS = 7;
	private static final int DEFAULT_LIMIT = 5;
	private static final int MAX_LIMIT = 20;

	private final DashboardJdbcRepository repository;

	public DashboardService(DashboardJdbcRepository repository) {
		this.repository = repository;
	}

	@Transactional(readOnly = true)
	public DashboardData getDashboard(Jwt jwt, String trendDaysRaw, String recentLimitRaw, String topCustomerLimitRaw,
			String alertLimitRaw, String includeRaw) {
		DashboardQuery query = parseQuery(trendDaysRaw, recentLimitRaw, topCustomerLimitRaw, alertLimitRaw, includeRaw);
		boolean canSeeFinancials = canSeeFinancials(jwt);
		LocalDate today = LocalDate.now(ZoneId.systemDefault());
		LocalDate yesterday = today.minusDays(1);
		LocalDate trendFrom = today.minusDays(query.trendDays() - 1L);
		LocalDate monthStart = today.withDayOfMonth(1);

		DashboardFinancialData financial = null;
		List<DashboardRevenueTrendPointData> revenueTrend = null;
		DashboardChannelBreakdownData channelBreakdown = null;
		if (canSeeFinancials) {
			if (query.includes(Section.FINANCIAL)) {
				financial = repository.loadFinancial(today, yesterday);
			}
			if (query.includes(Section.TREND)) {
				revenueTrend = repository.loadRevenueTrend(trendFrom, today);
			}
			if (query.includes(Section.CHANNEL)) {
				channelBreakdown = repository.loadChannelBreakdown(trendFrom, today);
			}
		}

		DashboardKpiData kpis = null;
		if (query.includes(Section.KPIS)) {
			InventorySummaryData inventory = repository.loadInventorySummary();
			var orderCounts = repository.countOrdersTotalAndPending();
			long pendingOrders = orderCounts.get("pending");
			long allOrdersTotal = orderCounts.get("total");
			long pendingApprovals = repository.countPendingApprovals();
			Map<String, Long> approvalByType = new LinkedHashMap<>();
			approvalByType.put("Inbound", pendingApprovals);
			approvalByType.put("Outbound", 0L);
			approvalByType.put("Return", 0L);
			approvalByType.put("Debt", 0L);
			kpis = new DashboardKpiData(inventory.totalSkus(), inventory.totalValue(), inventory.lowStockCount(),
					inventory.expiringSoonCount(), pendingOrders, allOrdersTotal, pendingApprovals, approvalByType);
		}

		return new DashboardData(
				financial,
				revenueTrend,
				channelBreakdown,
				kpis,
				query.includes(Section.ORDERS) ? repository.loadRecentOrders(query.recentLimit()) : null,
				query.includes(Section.APPROVALS) ? repository.loadPendingApprovals(DEFAULT_LIMIT) : null,
				query.includes(Section.CUSTOMERS) ? repository.loadTopCustomers(query.topCustomerLimit()) : null,
				canSeeFinancials && query.includes(Section.CASHFLOW) ? repository.loadCashflow(monthStart, today) : null,
				query.includes(Section.ALERTS) ? repository.loadLowStockAlerts(query.alertLimit()) : null);
	}

	static DashboardQuery parseQuery(String trendDaysRaw, String recentLimitRaw, String topCustomerLimitRaw,
			String alertLimitRaw, String includeRaw) {
		int trendDays = parseTrendDays(trendDaysRaw);
		int recentLimit = parseLimit(recentLimitRaw);
		int topCustomerLimit = parseLimit(topCustomerLimitRaw);
		int alertLimit = parseLimit(alertLimitRaw);
		EnumSet<Section> includes = parseInclude(includeRaw);
		return new DashboardQuery(trendDays, recentLimit, topCustomerLimit, alertLimit, includes);
	}

	static boolean canSeeFinancials(Jwt jwt) {
		if (jwt == null) {
			return false;
		}
		String role = jwt.getClaimAsString("role");
		return StringUtils.hasText(role) && FINANCIAL_ROLES.contains(role.trim());
	}

	private static int parseTrendDays(String raw) {
		if (!StringUtils.hasText(raw)) {
			return DEFAULT_TREND_DAYS;
		}
		try {
			int value = Integer.parseInt(raw.trim());
			if (value == 7 || value == 30) {
				return value;
			}
		}
		catch (NumberFormatException ignored) {
			// handled below
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "trendDays chỉ được là 7 hoặc 30.",
				Map.of("trendDays", "Giá trị hợp lệ: 7 hoặc 30"));
	}

	private static int parseLimit(String raw) {
		if (!StringUtils.hasText(raw)) {
			return DEFAULT_LIMIT;
		}
		try {
			int value = Integer.parseInt(raw.trim());
			if (value >= 1) {
				return Math.min(value, MAX_LIMIT);
			}
		}
		catch (NumberFormatException ignored) {
			// handled below
		}
		throw new BusinessException(ApiErrorCode.BAD_REQUEST, "limit phải là số nguyên dương.",
				Map.of("limit", "Giá trị hợp lệ: 1-20"));
	}

	private static EnumSet<Section> parseInclude(String raw) {
		if (!StringUtils.hasText(raw)) {
			return EnumSet.allOf(Section.class);
		}
		EnumSet<Section> out = EnumSet.noneOf(Section.class);
		for (String token : raw.split(",")) {
			String value = token.trim();
			if (!StringUtils.hasText(value)) {
				continue;
			}
			out.add(Section.fromParam(value));
		}
		return out;
	}

	enum Section {
		FINANCIAL("financial"),
		TREND("trend"),
		CHANNEL("channel"),
		KPIS("kpis"),
		ORDERS("orders"),
		APPROVALS("approvals"),
		CUSTOMERS("customers"),
		CASHFLOW("cashflow"),
		ALERTS("alerts");

		private final String param;

		Section(String param) {
			this.param = param;
		}

		static Section fromParam(String raw) {
			for (Section section : values()) {
				if (section.param.equals(raw)) {
					return section;
				}
			}
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "include không hợp lệ.",
					Map.of("include", "Giá trị hợp lệ: financial, trend, channel, kpis, orders, approvals, customers, cashflow, alerts"));
		}
	}

	record DashboardQuery(int trendDays, int recentLimit, int topCustomerLimit, int alertLimit, EnumSet<Section> includes) {
		boolean includes(Section section) {
			return includes.contains(section);
		}
	}
}
