package com.example.smart_erp.catalog.repository;

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

import com.example.smart_erp.catalog.response.SupplierDetailData;
import com.example.smart_erp.catalog.response.SupplierListItemData;

@SuppressWarnings("null")
@Repository
public class SupplierJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public SupplierJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public static String resolveListOrderBy(String sortRaw) {
		String s = sortRaw == null || sortRaw.isBlank() ? "updatedAt:desc" : sortRaw.trim();
		return switch (s) {
			case "name:asc" -> "s.name ASC";
			case "name:desc" -> "s.name DESC";
			case "supplierCode:asc" -> "s.supplier_code ASC";
			case "supplierCode:desc" -> "s.supplier_code DESC";
			case "updatedAt:asc" -> "s.updated_at ASC";
			case "updatedAt:desc" -> "s.updated_at DESC";
			case "createdAt:asc" -> "s.created_at ASC";
			case "createdAt:desc" -> "s.created_at DESC";
			default -> throw new IllegalArgumentException("sort");
		};
	}

	public long countList(String search, String status) {
		StringBuilder sql = new StringBuilder("""
				SELECT COUNT(*)::bigint FROM suppliers s WHERE 1 = 1
				""");
		MapSqlParameterSource p = new MapSqlParameterSource();
		appendListFilters(sql, p, search, status);
		Long n = namedJdbc.queryForObject(sql.toString(), p, Long.class);
		return n == null ? 0L : n;
	}

	public List<SupplierListItemData> findListPage(String search, String status, String orderBySql, int limit,
			int offset) {
		String sql = """
				SELECT s.id, s.supplier_code, s.name, s.contact_person, s.phone, s.email, s.address, s.tax_code, s.status,
				       s.created_at, s.updated_at,
				       (SELECT COUNT(*)::bigint FROM stockreceipts sr WHERE sr.supplier_id = s.id) AS receipt_count
				FROM suppliers s
				WHERE 1 = 1
				""" + appendListFiltersSuffix(search, status);
		MapSqlParameterSource p = listFilterParams(search, status);
		p.addValue("lim", limit).addValue("off", offset);
		String ordered = sql + " ORDER BY " + orderBySql + " LIMIT :lim OFFSET :off";
		return namedJdbc.query(ordered, p, LIST_ITEM_MAPPER);
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
		if (search != null && !search.isBlank()) {
			sql.append(" AND (s.name ILIKE :s OR s.supplier_code ILIKE :s OR s.phone ILIKE :s)");
			p.addValue("s", "%" + search.trim() + "%");
		}
		if (status != null && !status.isBlank() && !"all".equalsIgnoreCase(status)) {
			sql.append(" AND s.status = :st");
			p.addValue("st", status);
		}
	}

	private static final RowMapper<SupplierListItemData> LIST_ITEM_MAPPER = (rs, rn) -> mapListItem(rs);

	private static SupplierListItemData mapListItem(ResultSet rs) throws SQLException {
		return new SupplierListItemData(rs.getInt("id"), rs.getString("supplier_code"), rs.getString("name"),
				rs.getString("contact_person"), rs.getString("phone"), rs.getString("email"), rs.getString("address"),
				rs.getString("tax_code"), rs.getString("status"), rs.getLong("receipt_count"),
				toInstant(rs.getTimestamp("created_at")), toInstant(rs.getTimestamp("updated_at")));
	}

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	private static Instant toInstantNullable(Timestamp ts) {
		return ts != null ? ts.toInstant() : null;
	}

	public boolean existsSupplierCode(String supplierCode) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM suppliers WHERE supplier_code = :c LIMIT 1",
				Map.of("c", supplierCode), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public Optional<Integer> findIdBySupplierCode(String supplierCode) {
		List<Integer> hit = namedJdbc.query("SELECT id FROM suppliers WHERE supplier_code = :c LIMIT 1",
				Map.of("c", supplierCode), (rs, rn) -> rs.getInt("id"));
		return hit.isEmpty() ? Optional.empty() : Optional.of(hit.getFirst());
	}

	public boolean existsOtherSupplierCode(int excludeId, String supplierCode) {
		List<Integer> hit = namedJdbc.query(
				"SELECT 1 FROM suppliers WHERE supplier_code = :c AND id <> :id LIMIT 1",
				Map.of("c", supplierCode, "id", excludeId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int insertSupplier(String supplierCode, String name, String contactPerson, String phone, String email,
			String address, String taxCode, String status) {
		KeyHolder kh = new GeneratedKeyHolder();
		MapSqlParameterSource p = new MapSqlParameterSource();
		p.addValue("supplier_code", supplierCode);
		p.addValue("name", name);
		p.addValue("contact_person", contactPerson);
		p.addValue("phone", phone);
		p.addValue("email", email);
		p.addValue("address", address);
		p.addValue("tax_code", taxCode);
		p.addValue("status", status);
		namedJdbc.update("""
				INSERT INTO suppliers (supplier_code, name, contact_person, phone, email, address, tax_code, status)
				VALUES (:supplier_code, :name, :contact_person, :phone, :email, :address, :tax_code, :status)
				""", p, kh, new String[] { "id" });
		Number key = kh.getKey();
		return key != null ? key.intValue() : 0;
	}

	public Optional<SupplierDetailData> findDetailById(int id) {
		String sql = """
				SELECT s.id, s.supplier_code, s.name, s.contact_person, s.phone, s.email, s.address, s.tax_code, s.status,
				       s.created_at, s.updated_at,
				       (SELECT COUNT(*)::bigint FROM stockreceipts sr WHERE sr.supplier_id = s.id) AS receipt_count,
				       (SELECT MAX(sr.created_at) FROM stockreceipts sr WHERE sr.supplier_id = s.id) AS last_receipt_at
				FROM suppliers s WHERE s.id = :id
				""";
		List<SupplierDetailData> rows = namedJdbc.query(sql, Map.of("id", id), (rs, rn) -> mapDetail(rs));
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	private static SupplierDetailData mapDetail(ResultSet rs) throws SQLException {
		Timestamp lastTs = rs.getTimestamp("last_receipt_at");
		return new SupplierDetailData(rs.getInt("id"), rs.getString("supplier_code"), rs.getString("name"),
				rs.getString("contact_person"), rs.getString("phone"), rs.getString("email"), rs.getString("address"),
				rs.getString("tax_code"), rs.getString("status"), rs.getLong("receipt_count"),
				toInstantNullable(lastTs), toInstant(rs.getTimestamp("created_at")),
				toInstant(rs.getTimestamp("updated_at")));
	}

	public Optional<SupplierLockRow> lockSupplierForUpdate(int id) {
		String sql = """
				SELECT id, supplier_code, name, contact_person, phone, email, address, tax_code, status
				FROM suppliers WHERE id = :id FOR UPDATE
				""";
		List<SupplierLockRow> rows = namedJdbc.query(sql, Map.of("id", id),
				(rs, rn) -> new SupplierLockRow(rs.getInt("id"), rs.getString("supplier_code"), rs.getString("name"),
						rs.getString("contact_person"), rs.getString("phone"), rs.getString("email"),
						rs.getString("address"), rs.getString("tax_code"), rs.getString("status")));
		return rows.isEmpty() ? Optional.empty() : Optional.of(rows.getFirst());
	}

	public record SupplierLockRow(int id, String supplierCode, String name, String contactPerson, String phone,
			String email, String address, String taxCode, String status) {
	}

	public void updateSupplier(int id, String supplierCode, String name, String contactPerson, String phone,
			String email, String address, String taxCode, String status) {
		namedJdbc.update("""
				UPDATE suppliers SET supplier_code = :supplier_code, name = :name, contact_person = :contact_person,
				    phone = :phone, email = :email, address = :address, tax_code = :tax_code, status = :status,
				    updated_at = CURRENT_TIMESTAMP
				WHERE id = :id
				""", new MapSqlParameterSource().addValue("id", id).addValue("supplier_code", supplierCode)
				.addValue("name", name).addValue("contact_person", contactPerson).addValue("phone", phone)
				.addValue("email", email).addValue("address", address).addValue("tax_code", taxCode)
				.addValue("status", status));
	}

	public boolean existsSupplierId(int id) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM suppliers WHERE id = :id LIMIT 1", Map.of("id", id),
				(rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public boolean existsStockReceiptForSupplier(int supplierId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM stockreceipts WHERE supplier_id = :id LIMIT 1",
				Map.of("id", supplierId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public boolean existsPartnerDebtForSupplier(int supplierId) {
		List<Integer> hit = namedJdbc.query("SELECT 1 FROM partnerdebts WHERE supplier_id = :id LIMIT 1",
				Map.of("id", supplierId), (rs, rn) -> 1);
		return !hit.isEmpty();
	}

	public int deleteSupplier(int id) {
		return namedJdbc.update("DELETE FROM suppliers WHERE id = :id", Map.of("id", id));
	}

	public int deleteSuppliers(List<Integer> ids) {
		return namedJdbc.update("DELETE FROM suppliers WHERE id IN (:ids)", Map.of("ids", ids));
	}

	public void lockSuppliersForUpdate(List<Integer> ids) {
		List<Integer> sorted = new ArrayList<>(new HashSet<>(ids));
		Collections.sort(sorted);
		for (int sid : sorted) {
			lockSupplierForUpdate(sid).orElseThrow(() -> new IllegalStateException("supplier missing id=" + sid));
		}
	}

}
