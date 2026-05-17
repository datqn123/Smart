package com.example.smart_erp.sales.repository;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.sql.Types;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.sales.response.SalesOrderDetailData;
import com.example.smart_erp.sales.response.SalesOrderLineDetailData;
import com.example.smart_erp.sales.response.SalesOrderListItemData;

@SuppressWarnings("null")
@Repository
public class SalesOrderJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public SalesOrderJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	/** Task102 — whitelist sort cho lịch sử bán lẻ. */
	public static String resolveRetailHistoryOrderBy(String sortRaw) {
		String s = sortRaw == null || sortRaw.isBlank() ? "createdAt:desc" : sortRaw.trim();
		return switch (s) {
			case "createdAt:asc" -> "so.created_at ASC";
			case "createdAt:desc" -> "so.created_at DESC";
			case "finalAmount:asc" -> "so.final_amount ASC";
			case "finalAmount:desc" -> "so.final_amount DESC";
			default -> throw new IllegalArgumentException("sort");
		};
	}

	public static String resolveListOrderBy(String sortRaw) {
		String s = sortRaw == null || sortRaw.isBlank() ? "createdAt:desc" : sortRaw.trim();
		return switch (s) {
			case "orderCode:asc" -> "so.order_code ASC";
			case "orderCode:desc" -> "so.order_code DESC";
			case "totalAmount:asc" -> "so.total_amount ASC";
			case "totalAmount:desc" -> "so.total_amount DESC";
			case "updatedAt:asc" -> "so.updated_at ASC";
			case "updatedAt:desc" -> "so.updated_at DESC";
			case "createdAt:asc" -> "so.created_at ASC";
			case "createdAt:desc" -> "so.created_at DESC";
			default -> throw new IllegalArgumentException("sort");
		};
	}

	public long countList(String orderChannel, String search, String status, String paymentStatus) {
		StringBuilder sql = new StringBuilder("""
				SELECT COUNT(*)::bigint FROM salesorders so
				JOIN customers c ON c.id = so.customer_id
				WHERE 1 = 1
				""");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(sql, p, orderChannel, search, status, paymentStatus);
		Long n = namedJdbc.queryForObject(sql.toString(), p, Long.class);
		return n == null ? 0L : n;
	}

	public List<SalesOrderListItemData> findListPage(String orderChannel, String search, String status,
			String paymentStatus, String orderBySql, int limit, int offset) {
		String sql = """
				SELECT so.id, so.order_code, so.customer_id, c.name AS customer_name,
				       so.total_amount, so.discount_amount, so.final_amount, so.status, so.order_channel,
				       so.payment_status, so.notes, so.created_at, so.updated_at,
				       (SELECT COUNT(*)::int FROM orderdetails od WHERE od.order_id = so.id) AS items_count
				FROM salesorders so
				JOIN customers c ON c.id = so.customer_id
				WHERE 1 = 1
				""" + appendListFiltersSuffix(orderChannel, search, status, paymentStatus);
		MapSqlParameterSource p = listFilterParams(orderChannel, search, status, paymentStatus);
		p.addValue("lim", limit).addValue("off", offset);
		String ordered = sql + " ORDER BY " + orderBySql + " LIMIT :lim OFFSET :off";
		return namedJdbc.query(ordered, p, (rs, rn) -> new SalesOrderListItemData(rs.getInt("id"),
				rs.getString("order_code"), rs.getInt("customer_id"), rs.getString("customer_name"),
				rs.getBigDecimal("total_amount"), rs.getBigDecimal("discount_amount"), rs.getBigDecimal("final_amount"),
				rs.getString("status"), rs.getString("order_channel"), rs.getString("payment_status"),
				rs.getInt("items_count"), rs.getString("notes"), toInstant(rs.getTimestamp("created_at")),
				toInstant(rs.getTimestamp("updated_at"))));
	}

	private String appendListFiltersSuffix(String orderChannel, String search, String status, String paymentStatus) {
		StringBuilder sb = new StringBuilder();
		MapSqlParameterSource tmp = new MapSqlParameterSource();
		appendListFilters(sb, tmp, orderChannel, search, status, paymentStatus);
		return sb.toString();
	}

	private MapSqlParameterSource listFilterParams(String orderChannel, String search, String status,
			String paymentStatus) {
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(new StringBuilder(), p, orderChannel, search, status, paymentStatus);
		return p;
	}

	public long countRetailHistory(String search, Instant createdFrom, Instant createdToExclusive) {
		StringBuilder sql = new StringBuilder("""
				SELECT COUNT(*)::bigint FROM salesorders so
				JOIN customers c ON c.id = so.customer_id
				WHERE 1 = 1
				""");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendRetailHistoryFilters(sql, p, search, createdFrom, createdToExclusive);
		Long n = namedJdbc.queryForObject(sql.toString(), p, Long.class);
		return n == null ? 0L : n;
	}

	public List<SalesOrderListItemData> findRetailHistoryPage(String search, Instant createdFrom,
			Instant createdToExclusive, String orderBySql, int limit, int offset) {
		String sql = """
				SELECT so.id, so.order_code, so.customer_id, c.name AS customer_name,
				       so.total_amount, so.discount_amount, so.final_amount, so.status, so.order_channel,
				       so.payment_status, so.notes, so.created_at, so.updated_at,
				       (SELECT COUNT(*)::int FROM orderdetails od WHERE od.order_id = so.id) AS items_count
				FROM salesorders so
				JOIN customers c ON c.id = so.customer_id
				WHERE 1 = 1
				""";
		StringBuilder sb = new StringBuilder(sql);
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendRetailHistoryFilters(sb, p, search, createdFrom, createdToExclusive);
		p.addValue("lim", limit).addValue("off", offset);
		String ordered = sb + " ORDER BY " + orderBySql + " LIMIT :lim OFFSET :off";
		return namedJdbc.query(ordered, p, (rs, rn) -> new SalesOrderListItemData(rs.getInt("id"),
				rs.getString("order_code"), rs.getInt("customer_id"), rs.getString("customer_name"),
				rs.getBigDecimal("total_amount"), rs.getBigDecimal("discount_amount"), rs.getBigDecimal("final_amount"),
				rs.getString("status"), rs.getString("order_channel"), rs.getString("payment_status"),
				rs.getInt("items_count"), rs.getString("notes"), toInstant(rs.getTimestamp("created_at")),
				toInstant(rs.getTimestamp("updated_at"))));
	}

	private static void appendRetailHistoryFilters(StringBuilder sql, MapSqlParameterSource p, String search,
			Instant createdFrom, Instant createdToExclusive) {
		sql.append(" AND so.order_channel = 'Retail' AND so.status IN ('Delivered', 'Cancelled') ");
		if (search != null && !search.isBlank()) {
			sql.append(" AND (so.order_code ILIKE :s OR c.name ILIKE :s)");
			p.addValue("s", "%" + search.trim() + "%");
		}
		if (createdFrom != null) {
			sql.append(" AND so.created_at >= :createdFrom");
			p.addValue("createdFrom", Timestamp.from(createdFrom));
		}
		if (createdToExclusive != null) {
			sql.append(" AND so.created_at < :createdToExclusive");
			p.addValue("createdToExclusive", Timestamp.from(createdToExclusive));
		}
	}

	private static void appendListFilters(StringBuilder sql, MapSqlParameterSource p, String orderChannel,
			String search, String status, String paymentStatus) {
		if (orderChannel != null && !orderChannel.isBlank()) {
			sql.append(" AND so.order_channel = :oc");
			p.addValue("oc", orderChannel.trim());
		}
		if (search != null && !search.isBlank()) {
			sql.append(" AND (so.order_code ILIKE :s OR c.name ILIKE :s)");
			p.addValue("s", "%" + search.trim() + "%");
		}
		if (status != null && !status.isBlank() && !"all".equalsIgnoreCase(status)) {
			sql.append(" AND so.status = :st");
			p.addValue("st", status.trim());
		}
		if (paymentStatus != null && !paymentStatus.isBlank() && !"all".equalsIgnoreCase(paymentStatus)) {
			sql.append(" AND so.payment_status = :ps");
			p.addValue("ps", paymentStatus.trim());
		}
	}

	public Optional<SalesOrderDetailData> findDetailById(int id) {
		String headerSql = """
				SELECT so.id, so.order_code, so.customer_id, c.name AS customer_name,
				       so.total_amount, so.discount_amount, so.final_amount, so.status, so.order_channel,
				       so.payment_status, so.parent_order_id, so.ref_sales_order_id, so.shipping_address, so.notes,
				       so.pos_shift_ref, so.voucher_id, v.code AS voucher_code,
				       so.cancelled_at, so.cancelled_by, so.created_at, so.updated_at
				FROM salesorders so
				JOIN customers c ON c.id = so.customer_id
				LEFT JOIN vouchers v ON v.id = so.voucher_id
				WHERE so.id = :id
				""";
		List<SalesOrderDetailData> headers = namedJdbc.query(headerSql, Map.of("id", id), (rs, rn) -> {
			Integer parentId = (Integer) rs.getObject("parent_order_id");
			Integer refId = (Integer) rs.getObject("ref_sales_order_id");
			Integer voucherId = (Integer) rs.getObject("voucher_id");
			Integer cancelledBy = (Integer) rs.getObject("cancelled_by");
			return new SalesOrderDetailData(rs.getInt("id"), rs.getString("order_code"), rs.getInt("customer_id"),
					rs.getString("customer_name"), rs.getBigDecimal("total_amount"), rs.getBigDecimal("discount_amount"),
					rs.getBigDecimal("final_amount"), rs.getString("status"), rs.getString("order_channel"),
					rs.getString("payment_status"), parentId, refId, rs.getString("shipping_address"),
					rs.getString("notes"), rs.getString("pos_shift_ref"), voucherId, rs.getString("voucher_code"),
					tsToInstant(rs.getTimestamp("cancelled_at")), cancelledBy,
					toInstant(rs.getTimestamp("created_at")), toInstant(rs.getTimestamp("updated_at")), List.of());
		});
		if (headers.isEmpty()) {
			return Optional.empty();
		}
		SalesOrderDetailData h = headers.getFirst();
		List<SalesOrderLineDetailData> lines = findLinesByOrderId(id);
		return Optional.of(new SalesOrderDetailData(h.id(), h.orderCode(), h.customerId(), h.customerName(),
				h.totalAmount(), h.discountAmount(), h.finalAmount(), h.status(), h.orderChannel(), h.paymentStatus(),
				h.parentOrderId(), h.refSalesOrderId(), h.shippingAddress(), h.notes(), h.posShiftRef(),
				h.voucherId(), h.voucherCode(), h.cancelledAt(), h.cancelledBy(), h.createdAt(), h.updatedAt(), lines));
	}

	public List<SalesOrderLineDetailData> findLinesByOrderId(int orderId) {
		String sql = """
				SELECT od.id, od.product_id, p.name AS product_name, p.sku_code, od.unit_id, pu.unit_name,
				       od.quantity, od.price_at_time, od.line_total, od.dispatched_qty
				FROM orderdetails od
				JOIN products p ON p.id = od.product_id
				JOIN productunits pu ON pu.id = od.unit_id
				WHERE od.order_id = :oid
				ORDER BY od.id
				""";
		return namedJdbc.query(sql, Map.of("oid", orderId), (rs, rn) -> new SalesOrderLineDetailData(rs.getInt("id"),
				rs.getInt("product_id"), rs.getString("product_name"), rs.getString("sku_code"), rs.getInt("unit_id"),
				rs.getString("unit_name"), rs.getInt("quantity"), rs.getBigDecimal("price_at_time"),
				rs.getBigDecimal("line_total"), rs.getInt("dispatched_qty")));
	}

	public Optional<Integer> findWalkinCustomerId() {
		List<Integer> ids = namedJdbc.query(
				"SELECT id FROM customers WHERE customer_code = 'WALKIN' AND deleted_at IS NULL ORDER BY id LIMIT 1",
				Map.of(), (rs, rn) -> rs.getInt("id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public Optional<Integer> findCustomerIdOfOrder(int salesOrderId) {
		List<Integer> ids = namedJdbc.query("SELECT customer_id FROM salesorders WHERE id = :id LIMIT 1",
				Map.of("id", salesOrderId), (rs, rn) -> rs.getInt("customer_id"));
		return ids.isEmpty() ? Optional.empty() : Optional.of(ids.getFirst());
	}

	public boolean existsProductUnitForProduct(int productId, int unitId) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM productunits WHERE id = :uid AND product_id = :pid LIMIT 1",
				Map.of("uid", unitId, "pid", productId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int insertOrderHeader(String orderCode, int customerId, int userId, BigDecimal totalAmount,
			BigDecimal discountAmount, String status, String orderChannel, String paymentStatus, String shippingAddress,
			String notes, Integer parentOrderId, Integer refSalesOrderId, Integer voucherId, String posShiftRef) {
		KeyHolder kh = new GeneratedKeyHolder();
		String sql = """
				INSERT INTO salesorders (
				  order_code, customer_id, user_id, total_amount, discount_amount, status, order_channel,
				  payment_status, shipping_address, notes, parent_order_id, ref_sales_order_id, voucher_id, pos_shift_ref
				) VALUES (
				  :order_code, :customer_id, :user_id, :total_amount, :discount_amount, :status, :order_channel,
				  :payment_status, :shipping_address, :notes, :parent_order_id, :ref_sales_order_id, :voucher_id, :pos_shift_ref
				)
				""";
		MapSqlParameterSource p = new MapSqlParameterSource().addValue("order_code", orderCode)
				.addValue("customer_id", customerId).addValue("user_id", userId).addValue("total_amount", totalAmount)
				.addValue("discount_amount", discountAmount).addValue("status", status)
				.addValue("order_channel", orderChannel).addValue("payment_status", paymentStatus)
				.addValue("shipping_address", shippingAddress).addValue("notes", notes)
				.addValue("parent_order_id", parentOrderId).addValue("ref_sales_order_id", refSalesOrderId)
				.addValue("voucher_id", voucherId).addValue("pos_shift_ref", posShiftRef);
		namedJdbc.update(sql, p, kh, new String[] { "id" });
		Number key = kh.getKey();
		return key == null ? 0 : key.intValue();
	}

	public void updateOrderCode(int orderId, String orderCode) {
		namedJdbc.update("UPDATE salesorders SET order_code = :code WHERE id = :id",
				Map.of("code", orderCode, "id", orderId));
	}

	public Optional<String> findOrderCode(int orderId) {
		String code = namedJdbc.queryForObject("SELECT order_code FROM salesorders WHERE id = :id LIMIT 1",
				Map.of("id", orderId), String.class);
		return Optional.ofNullable(code);
	}

	public void insertOrderLine(int orderId, int productId, int unitId, int quantity, BigDecimal unitPrice) {
		namedJdbc.update("""
				INSERT INTO orderdetails (order_id, product_id, unit_id, quantity, price_at_time)
				VALUES (:oid, :pid, :uid, :qty, :price)
				""", Map.of("oid", orderId, "pid", productId, "uid", unitId, "qty", quantity, "price", unitPrice));
	}

	public Optional<OrderLockRow> lockOrderForUpdate(int id) {
		String sql = """
				SELECT id, status, order_channel, order_code, payment_status, total_amount, discount_amount,
				  cancelled_at, cancelled_by, voucher_id
				FROM salesorders WHERE id = :id FOR UPDATE
				""";
		List<OrderLockRow> rows = namedJdbc.query(sql, Map.of("id", id), (rs, rn) -> new OrderLockRow(rs.getInt("id"),
				rs.getString("status"), rs.getString("order_channel"), rs.getString("order_code"),
				rs.getString("payment_status"), rs.getBigDecimal("total_amount"), rs.getBigDecimal("discount_amount"),
				tsToInstant(rs.getTimestamp("cancelled_at")), (Integer) rs.getObject("cancelled_by"),
				(Integer) rs.getObject("voucher_id")));
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	/** Sau PATCH — lấy số tiều và kênh để ghi sổ cái khớp DB. */
	public Optional<OrderFinancialRow> loadOrderFinancialForLedger(int id) {
		String sql = """
				SELECT id, order_channel, order_code, status, payment_status, total_amount, discount_amount
				FROM salesorders WHERE id = :id
				""";
		List<OrderFinancialRow> rows = namedJdbc.query(sql, Map.of("id", id), (rs, rn) -> new OrderFinancialRow(
				rs.getInt("id"), rs.getString("order_channel"), rs.getString("order_code"), rs.getString("status"),
				rs.getString("payment_status"), rs.getBigDecimal("total_amount"), rs.getBigDecimal("discount_amount")));
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	/**
	 * Ghi {@code financeledger} cho đơn hàng (đa quỹ: quỹ mặc định). {@code amount} có dấu: dương = thu, âm = chi.
	 * {@code transactionType} ∈ CHECK bảng: SalesRevenue, Refund, …
	 */
	public void insertFinanceLedgerForSalesOrder(LocalDate transactionDate, String transactionType, int salesOrderId,
			BigDecimal amount, String description, int createdBy) {
		String sql = """
				INSERT INTO financeledger (transaction_date, transaction_type, reference_type, reference_id, amount, description, created_by, fund_id)
				VALUES (:td, :ttype, 'SalesOrder', :rid, :amt, :desc, :cb,
				  (SELECT cf.id FROM cash_funds cf WHERE cf.is_default = TRUE ORDER BY cf.id LIMIT 1))
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("td", java.sql.Date.valueOf(transactionDate)).addValue("ttype", transactionType)
						.addValue("rid", salesOrderId).addValue("amt", amount).addValue("desc", description, Types.VARCHAR)
						.addValue("cb", createdBy));
	}

	public boolean existsSalesRevenueLedgerForSalesOrder(int salesOrderId) {
		Integer n = namedJdbc.queryForObject("""
				SELECT COUNT(*)::int FROM financeledger
				WHERE reference_type = 'SalesOrder' AND reference_id = :id AND transaction_type = 'SalesRevenue'
				""", Map.of("id", salesOrderId), Integer.class);
		return n != null && n > 0;
	}

	public boolean existsRefundLedgerForSalesOrder(int salesOrderId) {
		Integer n = namedJdbc.queryForObject("""
				SELECT COUNT(*)::int FROM financeledger
				WHERE reference_type = 'SalesOrder' AND reference_id = :id AND transaction_type = 'Refund'
				""", Map.of("id", salesOrderId), Integer.class);
		return n != null && n > 0;
	}

	public void patchOrder(int id, String status, String paymentStatus, boolean includeShippingAddress,
			String shippingAddress, boolean includeNotes, String notes, BigDecimal discountAmount) {
		MapSqlParameterSource p = new MapSqlParameterSource("id", id);
		StringBuilder sql = new StringBuilder("UPDATE salesorders SET ");
		boolean first = true;
		if (status != null) {
			sql.append(first ? "" : ", ").append("status = :status");
			p.addValue("status", status);
			first = false;
		}
		if (paymentStatus != null) {
			sql.append(first ? "" : ", ").append("payment_status = :payment_status");
			p.addValue("payment_status", paymentStatus);
			first = false;
		}
		if (includeShippingAddress) {
			sql.append(first ? "" : ", ").append("shipping_address = :shipping_address");
			p.addValue("shipping_address", shippingAddress);
			first = false;
		}
		if (includeNotes) {
			sql.append(first ? "" : ", ").append("notes = :notes");
			p.addValue("notes", notes);
			first = false;
		}
		if (discountAmount != null) {
			sql.append(first ? "" : ", ").append("discount_amount = :discount_amount");
			p.addValue("discount_amount", discountAmount);
			first = false;
		}
		if (first) {
			return;
		}
		sql.append(" WHERE id = :id");
		namedJdbc.update(sql.toString(), p);
	}

	public void cancelOrder(int id, int cancelledByUserId) {
		namedJdbc.update("""
				UPDATE salesorders
				SET status = 'Cancelled', cancelled_at = CURRENT_TIMESTAMP, cancelled_by = :uid
				WHERE id = :id
				""", Map.of("id", id, "uid", cancelledByUserId));
	}

	public long countStockDispatchesForOrder(int orderId) {
		Long n = namedJdbc.queryForObject("SELECT COUNT(*)::bigint FROM stockdispatches WHERE order_id = :id",
				Map.of("id", orderId), Long.class);
		return n == null ? 0L : n;
	}

	public boolean existsDispatchedLines(int orderId) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM orderdetails WHERE order_id = :id AND dispatched_qty > 0 LIMIT 1",
				Map.of("id", orderId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public record OrderLockRow(int id, String status, String orderChannel, String orderCode, String paymentStatus,
			BigDecimal totalAmount, BigDecimal discountAmount, Instant cancelledAt, Integer cancelledBy, Integer voucherId) {
	}

	public record OrderFinancialRow(int id, String orderChannel, String orderCode, String status, String paymentStatus,
			BigDecimal totalAmount, BigDecimal discountAmount) {
	}

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	private static Instant tsToInstant(Timestamp ts) {
		return ts == null ? null : ts.toInstant();
	}
}
