package com.example.smart_erp.dashboard.repository;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.dashboard.response.DashboardCashflowData;
import com.example.smart_erp.dashboard.response.DashboardChannelBreakdownData;
import com.example.smart_erp.dashboard.response.DashboardFinancialData;
import com.example.smart_erp.dashboard.response.DashboardLowStockAlertData;
import com.example.smart_erp.dashboard.response.DashboardPendingApprovalData;
import com.example.smart_erp.dashboard.response.DashboardRecentOrderData;
import com.example.smart_erp.dashboard.response.DashboardRevenueTrendPointData;
import com.example.smart_erp.dashboard.response.DashboardTopCustomerData;
import com.example.smart_erp.inventory.response.InventorySummaryData;

@Repository
public class DashboardJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public DashboardJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public DashboardFinancialData loadFinancial(LocalDate today, LocalDate yesterday) {
		ZoneId zone = ZoneId.systemDefault();
		MapSqlParameterSource src = new MapSqlParameterSource()
				.addValue("todayStart", Timestamp.from(today.atStartOfDay(zone).toInstant()))
				.addValue("todayEnd", Timestamp.from(today.plusDays(1).atStartOfDay(zone).toInstant()))
				.addValue("yesterdayStart", Timestamp.from(yesterday.atStartOfDay(zone).toInstant()))
				.addValue("yesterdayEnd", Timestamp.from(today.atStartOfDay(zone).toInstant()));
		return namedJdbc.queryForObject("""
				SELECT
				  COALESCE(SUM(CASE WHEN created_at >= :todayStart AND created_at < :todayEnd THEN final_amount ELSE 0 END), 0) AS today_revenue,
				  COALESCE(SUM(CASE WHEN created_at >= :yesterdayStart AND created_at < :yesterdayEnd THEN final_amount ELSE 0 END), 0) AS yesterday_revenue,
				  COUNT(CASE WHEN created_at >= :todayStart AND created_at < :todayEnd THEN 1 END)::bigint AS today_orders
				FROM salesorders
				WHERE status <> 'Cancelled'
				  AND created_at >= :yesterdayStart AND created_at < :todayEnd
				""", src, (rs, rowNum) -> {
			BigDecimal todayRevenue = money(rs, "today_revenue");
			BigDecimal yesterdayRevenue = money(rs, "yesterday_revenue");
			long todayOrders = rs.getLong("today_orders");
			BigDecimal pctChange = BigDecimal.ZERO.compareTo(yesterdayRevenue) == 0
					? null
					: todayRevenue.subtract(yesterdayRevenue)
							.multiply(BigDecimal.valueOf(100))
							.divide(yesterdayRevenue, 2, java.math.RoundingMode.HALF_UP);
			BigDecimal avgOrderValue = todayOrders == 0
					? BigDecimal.ZERO
					: todayRevenue.divide(BigDecimal.valueOf(todayOrders), 2, java.math.RoundingMode.HALF_UP);
			return new DashboardFinancialData(todayRevenue, yesterdayRevenue, todayOrders, pctChange, avgOrderValue);
		});
	}

	public List<DashboardRevenueTrendPointData> loadRevenueTrend(LocalDate from, LocalDate to) {
		ZoneId zone = ZoneId.systemDefault();
		MapSqlParameterSource src = new MapSqlParameterSource()
				.addValue("from", java.sql.Date.valueOf(from))
				.addValue("to", java.sql.Date.valueOf(to))
				.addValue("fromStart", Timestamp.from(from.atStartOfDay(zone).toInstant()))
				.addValue("toEnd", Timestamp.from(to.plusDays(1).atStartOfDay(zone).toInstant()));
		return namedJdbc.query("""
				WITH days AS (
				  SELECT generate_series(CAST(:from AS date), CAST(:to AS date), interval '1 day')::date AS day
				),
				orders AS (
				  SELECT created_at::date AS day, COALESCE(SUM(final_amount), 0) AS revenue, COUNT(*)::bigint AS orders
				  FROM salesorders
				  WHERE created_at >= :fromStart AND created_at < :toEnd AND status <> 'Cancelled'
				  GROUP BY created_at::date
				)
				SELECT d.day, COALESCE(o.revenue, 0) AS revenue, COALESCE(o.orders, 0) AS orders
				FROM days d
				LEFT JOIN orders o ON o.day = d.day
				ORDER BY d.day ASC
				""", src, (rs, rowNum) -> {
			LocalDate day = rs.getObject("day", LocalDate.class);
			return new DashboardRevenueTrendPointData(day.toString(), label(day), money(rs, "revenue"),
					rs.getLong("orders"));
		});
	}

	public DashboardChannelBreakdownData loadChannelBreakdown(LocalDate from, LocalDate to) {
		ZoneId zone = ZoneId.systemDefault();
		MapSqlParameterSource src = new MapSqlParameterSource()
				.addValue("fromStart", Timestamp.from(from.atStartOfDay(zone).toInstant()))
				.addValue("toEnd", Timestamp.from(to.plusDays(1).atStartOfDay(zone).toInstant()));
		return namedJdbc.queryForObject("""
				SELECT
				  COALESCE(SUM(CASE WHEN order_channel = 'Retail' THEN final_amount ELSE 0 END), 0) AS retail,
				  COALESCE(SUM(CASE WHEN order_channel = 'Wholesale' THEN final_amount ELSE 0 END), 0) AS wholesale
				FROM salesorders
				WHERE created_at >= :fromStart AND created_at < :toEnd
				  AND status <> 'Cancelled'
				""", src, (rs, rowNum) -> {
			BigDecimal retail = money(rs, "retail");
			BigDecimal wholesale = money(rs, "wholesale");
			return new DashboardChannelBreakdownData(retail, wholesale, retail.add(wholesale));
		});
	}

	public InventorySummaryData loadInventorySummary() {
		return namedJdbc.queryForObject("""
				SELECT
				  COUNT(*)::bigint AS total_skus,
				  COALESCE(SUM(i.quantity::numeric * COALESCE(pph.latest_cost::numeric, 0)), 0) AS total_value,
				  COALESCE(SUM(CASE WHEN i.quantity > 0 AND i.quantity <= i.min_quantity THEN 1 ELSE 0 END), 0)::bigint AS low_stock_count,
				  COALESCE(SUM(CASE WHEN i.expiry_date IS NOT NULL AND i.expiry_date <= (CURRENT_DATE + interval '30 day') AND i.quantity > 0 THEN 1 ELSE 0 END), 0)::bigint AS expiring_soon_count
				FROM inventory i
				INNER JOIN products p ON p.id = i.product_id
				INNER JOIN productunits pub ON pub.product_id = p.id AND pub.is_base_unit = true
				LEFT JOIN productunits pud ON pud.id = i.unit_id
				LEFT JOIN LATERAL (
				  SELECT pph1.cost_price AS latest_cost
				  FROM productpricehistory pph1
				  WHERE pph1.product_id = p.id AND pph1.unit_id = COALESCE(i.unit_id, pub.id)
				  ORDER BY pph1.effective_date DESC, pph1.id DESC
				  LIMIT 1
				) pph ON true
				""", new MapSqlParameterSource(), (rs, rowNum) -> new InventorySummaryData(
				rs.getLong("total_skus"), money(rs, "total_value"), rs.getLong("low_stock_count"),
				rs.getLong("expiring_soon_count")));
	}

	public long countOrdersByStatus(String status) {
		String filter = status == null ? "" : " WHERE status = :status";
		MapSqlParameterSource src = new MapSqlParameterSource();
		if (status != null) {
			src.addValue("status", status);
		}
		Long value = namedJdbc.queryForObject("SELECT COUNT(*)::bigint FROM salesorders" + filter, src, Long.class);
		return value == null ? 0L : value;
	}

	public java.util.Map<String, Long> countOrdersTotalAndPending() {
		MapSqlParameterSource src = new MapSqlParameterSource();
		return namedJdbc.queryForObject("""
				SELECT COUNT(*)::bigint AS total,
				       COUNT(*) FILTER (WHERE status = 'Pending')::bigint AS pending
				FROM salesorders
				""", src, (rs, rowNum) -> java.util.Map.of("total", rs.getLong("total"), "pending", rs.getLong("pending")));
	}

	public long countPendingApprovals() {
		Long value = namedJdbc.queryForObject("SELECT COUNT(*)::bigint FROM stockreceipts WHERE status = 'Pending'",
				Map.of(), Long.class);
		return value == null ? 0L : value;
	}

	public List<DashboardPendingApprovalData> loadPendingApprovals(int limit) {
		return namedJdbc.query("""
				SELECT sr.id, sr.receipt_code, u.full_name AS creator_name, sr.receipt_date, sr.total_amount
				FROM stockreceipts sr
				INNER JOIN users u ON u.id = sr.staff_id
				WHERE sr.status = 'Pending'
				ORDER BY sr.created_at DESC, sr.id DESC
				LIMIT :limit
				""", new MapSqlParameterSource("limit", limit), (rs, rowNum) -> new DashboardPendingApprovalData(
				"stock_receipt", rs.getLong("id"), rs.getString("receipt_code"), "Inbound",
				rs.getString("creator_name"), money(rs, "total_amount"), dateToInstant(rs, "receipt_date")));
	}

	public List<DashboardRecentOrderData> loadRecentOrders(int limit) {
		return namedJdbc.query("""
				SELECT so.id, so.order_code, so.order_channel, c.name AS customer_name,
				       so.final_amount, so.status, so.created_at
				FROM salesorders so
				INNER JOIN customers c ON c.id = so.customer_id
				ORDER BY so.created_at DESC, so.id DESC
				LIMIT :limit
				""", new MapSqlParameterSource("limit", limit), RECENT_ORDER_ROW);
	}

	public List<DashboardTopCustomerData> loadTopCustomers(int limit) {
		return namedJdbc.query("""
				SELECT c.id, c.name, COUNT(DISTINCT so.id)::bigint AS order_count,
				       COALESCE(SUM(so.final_amount), 0) AS total_spent
				FROM customers c
				INNER JOIN salesorders so ON so.customer_id = c.id AND so.status <> 'Cancelled'
				GROUP BY c.id, c.name
				HAVING COALESCE(SUM(so.final_amount), 0) > 0
				ORDER BY total_spent DESC, c.id ASC
				LIMIT :limit
				""", new MapSqlParameterSource("limit", limit), (rs, rowNum) -> new DashboardTopCustomerData(
				rs.getInt("id"), rs.getString("name"), rs.getLong("order_count"), money(rs, "total_spent")));
	}

	public DashboardCashflowData loadCashflow(LocalDate from, LocalDate to) {
		ZoneId zone = ZoneId.systemDefault();
		MapSqlParameterSource src = new MapSqlParameterSource()
				.addValue("fromStart", Timestamp.from(from.atStartOfDay(zone).toInstant()))
				.addValue("toEnd", Timestamp.from(to.plusDays(1).atStartOfDay(zone).toInstant()));
		return namedJdbc.queryForObject("""
				SELECT
				  COALESCE(SUM(CASE WHEN direction = 'Income' THEN amount ELSE 0 END), 0) AS income,
				  COALESCE(SUM(CASE WHEN direction = 'Expense' THEN amount ELSE 0 END), 0) AS expense
				FROM cashtransactions
				WHERE transaction_date >= :fromStart AND transaction_date < :toEnd
				  AND status = 'Completed'
				""", src, (rs, rowNum) -> {
			BigDecimal income = money(rs, "income");
			BigDecimal expense = money(rs, "expense");
			return new DashboardCashflowData(income, expense, income.subtract(expense));
		});
	}

	public List<DashboardLowStockAlertData> loadLowStockAlerts(int limit) {
		return namedJdbc.query("""
				SELECT i.id, p.name AS product_name, p.sku_code, i.quantity, i.min_quantity,
				       COALESCE(pud.unit_name, pub.unit_name) AS unit_name
				FROM inventory i
				INNER JOIN products p ON p.id = i.product_id
				INNER JOIN productunits pub ON pub.product_id = p.id AND pub.is_base_unit = true
				LEFT JOIN productunits pud ON pud.id = i.unit_id
				WHERE i.quantity > 0 AND i.quantity <= i.min_quantity
				ORDER BY i.quantity ASC, i.id ASC
				LIMIT :limit
				""", new MapSqlParameterSource("limit", limit), (rs, rowNum) -> new DashboardLowStockAlertData(
				rs.getLong("id"), rs.getString("product_name"), rs.getString("sku_code"),
				rs.getInt("quantity"), rs.getInt("min_quantity"), rs.getString("unit_name")));
	}

	private static final RowMapper<DashboardRecentOrderData> RECENT_ORDER_ROW = (rs, rowNum) -> new DashboardRecentOrderData(
			rs.getInt("id"), rs.getString("order_code"), rs.getString("order_channel"), rs.getString("customer_name"),
			money(rs, "final_amount"), rs.getString("status"), toInstant(rs.getTimestamp("created_at")));

	private static BigDecimal money(ResultSet rs, String column) throws SQLException {
		BigDecimal value = rs.getBigDecimal(column);
		return value == null ? BigDecimal.ZERO : value;
	}

	private static Instant toInstant(Timestamp ts) {
		return ts == null ? Instant.EPOCH : ts.toInstant();
	}

	private static Instant dateToInstant(ResultSet rs, String column) throws SQLException {
		LocalDate value = rs.getObject(column, LocalDate.class);
		return value == null ? Instant.EPOCH : value.atStartOfDay(java.time.ZoneOffset.UTC).toInstant();
	}

	private static String label(LocalDate date) {
		return "%02d/%02d".formatted(date.getDayOfMonth(), date.getMonthValue());
	}
}
