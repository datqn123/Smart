package com.example.smart_erp.inventory.receipts.repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository;
import com.example.smart_erp.inventory.receipts.query.StockReceiptListQuery;
import com.example.smart_erp.inventory.receipts.query.StockReceiptStatusFilter;
import com.example.smart_erp.inventory.receipts.response.StockReceiptListItemData;

/**
 * Đọc list phiếu nhập — SRS Task013 / Flyway V1 + V9.
 */
@SuppressWarnings("null")
@Repository
public class StockReceiptListJdbcRepository {

	private static final String BASE_FROM = """
			FROM stockreceipts sr
			INNER JOIN suppliers s ON s.id = sr.supplier_id
			INNER JOIN users u_staff ON u_staff.id = sr.staff_id
			LEFT JOIN users u_appr ON u_appr.id = sr.approved_by
			LEFT JOIN users u_rev ON u_rev.id = sr.reviewed_by
			LEFT JOIN LATERAL (
			  SELECT COUNT(*)::int AS line_count
			  FROM stockreceiptdetails d
			  WHERE d.receipt_id = sr.id
			) line_agg ON true
			""";

	private static final String SELECT_LIST = """
			SELECT
			  sr.id,
			  sr.receipt_code,
			  sr.supplier_id,
			  s.name AS supplier_name,
			  sr.staff_id,
			  u_staff.full_name AS staff_name,
			  sr.receipt_date,
			  sr.status,
			  sr.invoice_number,
			  sr.total_amount,
			  sr.notes,
			  sr.approved_by,
			  u_appr.full_name AS approved_by_name,
			  sr.approved_at,
			  sr.reviewed_by,
			  u_rev.full_name AS reviewed_by_name,
			  sr.reviewed_at,
			  sr.rejection_reason,
			  sr.created_at,
			  sr.updated_at,
			  line_agg.line_count
			""";

	private final NamedParameterJdbcTemplate namedJdbc;

	public StockReceiptListJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public long countRows(StockReceiptListQuery q) {
		Filter f = buildFilter(q);
		String sql = "SELECT COUNT(*) " + BASE_FROM + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	public List<StockReceiptListItemData> loadPage(StockReceiptListQuery q) {
		Filter f = buildFilter(q);
		int offset = (q.page() - 1) * q.limit();
		String sql = SELECT_LIST + BASE_FROM + f.where + " ORDER BY " + q.sort().orderByFragment() + " LIMIT " + q.limit()
				+ " OFFSET " + offset;
		return namedJdbc.query(sql, f.source, ROW);
	}

	private static final RowMapper<StockReceiptListItemData> ROW = StockReceiptListJdbcRepository::mapRow;

	private static StockReceiptListItemData mapRow(ResultSet rs, int i) throws SQLException {
		return new StockReceiptListItemData(
				rs.getLong("id"),
				rs.getString("receipt_code"),
				rs.getLong("supplier_id"),
				rs.getString("supplier_name"),
				rs.getInt("staff_id"),
				rs.getString("staff_name"),
				rs.getObject("receipt_date", LocalDate.class),
				rs.getString("status"),
				rs.getString("invoice_number"),
				rs.getBigDecimal("total_amount"),
				rs.getInt("line_count"),
				rs.getString("notes"),
				(Integer) rs.getObject("approved_by", Integer.class),
				rs.getString("approved_by_name"),
				toInstant(rs.getTimestamp("approved_at")),
				(Integer) rs.getObject("reviewed_by", Integer.class),
				rs.getString("reviewed_by_name"),
				toInstant(rs.getTimestamp("reviewed_at")),
				rs.getString("rejection_reason"),
				toInstantNonNull(rs.getTimestamp("created_at")),
				toInstantNonNull(rs.getTimestamp("updated_at")));
	}

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : null;
	}

	private static Instant toInstantNonNull(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	private Filter buildFilter(StockReceiptListQuery q) {
		StringBuilder sb = new StringBuilder(" WHERE 1=1");
		var src = new MapSqlParameterSource();
		appendStatus(q.status(), sb, src);
		if (q.search() != null) {
			sb.append(" AND (sr.receipt_code ILIKE :_search OR sr.invoice_number ILIKE :_search)");
			src.addValue("_search", InventoryListJdbcRepository.buildSearchPattern(q.search()));
		}
		if (q.dateFrom() != null) {
			sb.append(" AND sr.receipt_date >= :_date_from");
			src.addValue("_date_from", q.dateFrom());
		}
		if (q.dateTo() != null) {
			sb.append(" AND sr.receipt_date <= :_date_to");
			src.addValue("_date_to", q.dateTo());
		}
		if (q.supplierId() != null) {
			sb.append(" AND sr.supplier_id = :_supplier_id");
			src.addValue("_supplier_id", q.supplierId());
		}
		if (q.mineStaffId() != null) {
			sb.append(" AND sr.staff_id = :_mine_staff_id");
			src.addValue("_mine_staff_id", q.mineStaffId());
		}
		return new Filter(sb.toString(), src);
	}

	private static void appendStatus(StockReceiptStatusFilter st, StringBuilder sb, MapSqlParameterSource src) {
		if (st == null || st == StockReceiptStatusFilter.ALL) {
			return;
		}
		sb.append(" AND sr.status = :_status");
		src.addValue("_status", statusSqlLiteral(st));
	}

	private static String statusSqlLiteral(StockReceiptStatusFilter st) {
		return switch (st) {
		case ALL -> throw new IllegalStateException("status filter ALL must not reach SQL literal");
		case DRAFT -> "Draft";
		case PENDING -> "Pending";
		case APPROVED -> "Approved";
		case REJECTED -> "Rejected";
		};
	}

	private static final class Filter {
		final String where;
		final MapSqlParameterSource source;

		Filter(String w, MapSqlParameterSource s) {
			this.where = w;
			this.source = s;
		}
	}
}
