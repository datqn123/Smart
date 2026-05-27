package com.example.smart_erp.catalog.repository;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.catalog.response.CustomerData;

@SuppressWarnings("null")
@Repository
public class CustomerJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public CustomerJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public static String resolveListOrderBy(String sortRaw) {
		String s = sortRaw == null || sortRaw.isBlank() ? "updatedAt:desc" : sortRaw.trim();
		return switch (s) {
			case "name:asc" -> "c.name ASC";
			case "name:desc" -> "c.name DESC";
			case "customerCode:asc" -> "c.customer_code ASC";
			case "customerCode:desc" -> "c.customer_code DESC";
			case "updatedAt:asc" -> "c.updated_at ASC";
			case "updatedAt:desc" -> "c.updated_at DESC";
			case "createdAt:asc" -> "c.created_at ASC";
			case "createdAt:desc" -> "c.created_at DESC";
			case "loyaltyPoints:asc" -> "c.loyalty_points ASC";
			case "loyaltyPoints:desc" -> "c.loyalty_points DESC";
			default -> throw new IllegalArgumentException("sort");
		};
	}

	private static final String FROM_CUSTOMER_AGG = """
			FROM customers c
			LEFT JOIN (
			  SELECT customer_id,
			    COALESCE(SUM(total_amount) FILTER (WHERE status IS DISTINCT FROM 'Cancelled'), 0) AS total_spent,
			    COUNT(*) FILTER (WHERE status IS DISTINCT FROM 'Cancelled')::bigint AS order_cnt
			  FROM salesorders
			  GROUP BY customer_id
			) agg ON agg.customer_id = c.id
			""";

	public long countList(String search, String status) {
		StringBuilder sql = new StringBuilder("SELECT COUNT(*)::bigint ").append(FROM_CUSTOMER_AGG).append(" WHERE 1 = 1");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(sql, p, search, status);
		Long n = namedJdbc.queryForObject(sql.toString(), p, Long.class);
		return n == null ? 0L : n;
	}

	public List<CustomerData> findListPage(String search, String status, String orderBySql, int limit, int offset) {
		String sql = """
				SELECT c.id, c.customer_code, c.name, c.phone, c.email, c.address, c.loyalty_points, c.status,
				       c.created_at, c.updated_at,
				       COALESCE(agg.total_spent, 0) AS total_spent,
				       COALESCE(agg.order_cnt, 0) AS order_cnt
				""" + FROM_CUSTOMER_AGG + """
				WHERE 1 = 1
				""" + appendListFiltersSuffix(search, status);
		MapSqlParameterSource p = listFilterParams(search, status);
		p.addValue("lim", limit).addValue("off", offset);
		String ordered = sql + " ORDER BY " + orderBySql + ", c.id ASC LIMIT :lim OFFSET :off";
		return namedJdbc.query(ordered, p, CUSTOMER_MAPPER);
	}

	private static String appendListFiltersSuffix(String search, String status) {
		StringBuilder sb = new StringBuilder();
		MapSqlParameterSource tmp = new MapSqlParameterSource();
		appendListFilters(sb, tmp, search, status);
		return sb.toString();
	}

	private MapSqlParameterSource listFilterParams(String search, String status) {
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(new StringBuilder(), p, search, status);
		return p;
	}

	private static void appendListFilters(StringBuilder sql, MapSqlParameterSource p, String search, String status) {
		sql.append(" AND c.deleted_at IS NULL");
		if (search != null && !search.isBlank()) {
			sql.append(
					" AND (c.name ILIKE :s OR c.customer_code ILIKE :s OR c.phone ILIKE :s OR c.email ILIKE :s)");
			p.addValue("s", "%" + search.trim() + "%");
		}
		if (status != null && !status.isBlank() && !"all".equalsIgnoreCase(status)) {
			sql.append(" AND c.status = :st");
			p.addValue("st", status);
		}
	}

	private static final RowMapper<CustomerData> CUSTOMER_MAPPER = (rs, rn) -> mapCustomer(rs);

	private static CustomerData mapCustomer(ResultSet rs) throws SQLException {
		BigDecimal spent = rs.getBigDecimal("total_spent");
		if (spent == null) {
			spent = BigDecimal.ZERO;
		}
		long oc = rs.getLong("order_cnt");
		return new CustomerData(rs.getInt("id"), rs.getString("customer_code"), rs.getString("name"),
				rs.getString("phone"), rs.getString("email"), rs.getString("address"), rs.getInt("loyalty_points"),
				spent, oc, rs.getString("status"), toInstant(rs.getTimestamp("created_at")),
				toInstant(rs.getTimestamp("updated_at")));
	}

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	public boolean existsCustomerCode(String customerCode) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM customers WHERE customer_code = :c AND deleted_at IS NULL LIMIT 1",
				Map.of("c", customerCode), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public Optional<Integer> findIdByCustomerCode(String customerCode) {
		List<Integer> hit = namedJdbc.query(
				"SELECT id FROM customers WHERE customer_code = :c AND deleted_at IS NULL LIMIT 1",
				Map.of("c", customerCode), (rs, rn) -> rs.getInt("id"));
		return hit.isEmpty() ? Optional.empty() : Optional.of(hit.getFirst());
	}

	public boolean existsOtherCustomerCode(int excludeId, String customerCode) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM customers WHERE customer_code = :c AND id <> :id AND deleted_at IS NULL LIMIT 1",
				Map.of("c", customerCode, "id", excludeId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int insertCustomer(String customerCode, String name, String phone, String email, String address,
			String status) {
		KeyHolder kh = new GeneratedKeyHolder();
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("customer_code", customerCode);
		p.addValue("name", name);
		p.addValue("phone", phone);
		p.addValue("email", email);
		p.addValue("address", address);
		p.addValue("status", status);
		namedJdbc.update("""
				INSERT INTO customers (customer_code, name, phone, email, address, loyalty_points, status)
				VALUES (:customer_code, :name, :phone, NULLIF(TRIM(:email), ''), :address, 0, :status)
				""", p, kh, new String[] { "id" });
		Number key = kh.getKey();
		return key != null ? key.intValue() : 0;
	}

	public Optional<CustomerData> findDetailById(int id) {
		String sql = """
				SELECT c.id, c.customer_code, c.name, c.phone, c.email, c.address, c.loyalty_points, c.status,
				       c.created_at, c.updated_at,
				       COALESCE(agg.total_spent, 0) AS total_spent,
				       COALESCE(agg.order_cnt, 0) AS order_cnt
				""" + FROM_CUSTOMER_AGG + " WHERE c.id = :id AND c.deleted_at IS NULL";
		List<CustomerData> rows = namedJdbc.query(sql, Map.of("id", id), CUSTOMER_MAPPER);
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public Optional<CustomerLockRow> lockCustomerForUpdate(int id) {
		String sql = """
				SELECT id, customer_code, name, phone, email, address, loyalty_points, status
				FROM customers WHERE id = :id AND deleted_at IS NULL FOR UPDATE
				""";
		List<CustomerLockRow> rows = namedJdbc.query(sql, Map.of("id", id),
				(rs, rn) -> new CustomerLockRow(rs.getInt("id"), rs.getString("customer_code"), rs.getString("name"),
						rs.getString("phone"), rs.getString("email"), rs.getString("address"), rs.getInt("loyalty_points"),
						rs.getString("status")));
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public record CustomerLockRow(int id, String customerCode, String name, String phone, String email, String address,
			int loyaltyPoints, String status) {
	}

	public void updateCustomer(int id, String customerCode, String name, String phone, String email, String address,
			Integer loyaltyPoints, String status) {
		MapSqlParameterSource p = new MapSqlParameterSource().addValue("id", id).addValue("customer_code", customerCode)
				.addValue("name", name).addValue("phone", phone).addValue("email", email).addValue("address", address)
				.addValue("loyalty_points", loyaltyPoints).addValue("status", status);
		namedJdbc.update("""
				UPDATE customers SET customer_code = :customer_code, name = :name, phone = :phone,
				    email = NULLIF(TRIM(:email), ''), address = :address, loyalty_points = :loyalty_points,
				    status = :status, updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""", p);
	}

	public boolean existsCustomerId(int id) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM customers WHERE id = :id AND deleted_at IS NULL LIMIT 1", Map.of("id", id),
				(rs, rn) -> 1);
		return !hit.isEmpty();
	}

	/** Bulk / legacy guard: any sales order row for customer. */
	public boolean existsSalesOrderForCustomer(int customerId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM salesorders WHERE customer_id = :id LIMIT 1",
				Map.of("id", customerId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	/** Single soft-delete: block if any order is not in a terminal status. */
	public boolean existsOpenSalesOrderForCustomer(int customerId) {
		List<Integer> hit = namedJdbc.query("""
				SELECT 1 FROM salesorders so
				WHERE so.customer_id = :id
				  AND LOWER(so.status) NOT IN ('delivered', 'cancelled')
				LIMIT 1
				""", Map.of("id", customerId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public boolean existsPartnerDebtForCustomer(int customerId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM partnerdebts WHERE customer_id = :id LIMIT 1",
				Map.of("id", customerId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int softDeleteCustomer(int id) {
		return namedJdbc.update(
				"UPDATE customers SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND deleted_at IS NULL",
				Map.of("id", id));
	}

	/** Owner bulk hard-delete (Task053). */
	public int deleteCustomerHard(int id) {
		return namedJdbc.update("DELETE FROM customers WHERE id = :id", Map.of("id", id));
	}

	public int deleteCustomersHard(List<Integer> ids) {
		return namedJdbc.update("DELETE FROM customers WHERE id IN (:ids)", Map.of("ids", ids));
	}

	public void lockCustomersForUpdate(List<Integer> ids) {
		List<Integer> sorted = new ArrayList<>(new HashSet<>(ids));
		Collections.sort(sorted);
		for (int cid : sorted) {
			lockCustomerForUpdate(cid).orElseThrow(() -> new IllegalStateException("customer missing id=" + cid));
		}
	}
}
