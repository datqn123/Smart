package com.example.smart_erp.inventory.approvals;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.inventory.approvals.response.ApprovalsHistoryItemData;
import com.example.smart_erp.inventory.approvals.response.ApprovalsPendingItemData;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository;

/**
 * Đọc approvals — SRS Task061–062, bảng {@code stockreceipts}.
 */
@SuppressWarnings("null")
@Repository
public class ApprovalsJdbcRepository {

	private static final String PENDING_BASE_FROM = """
			FROM stockreceipts sr
			INNER JOIN users u ON u.id = sr.staff_id
			""";

	private static final String HISTORY_BASE_FROM = """
			FROM stockreceipts sr
			INNER JOIN users u_creator ON u_creator.id = sr.staff_id
			LEFT JOIN users u_rev ON u_rev.id = sr.reviewed_by
			""";

	private final NamedParameterJdbcTemplate namedJdbc;

	public ApprovalsJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public long countPending(String searchPattern, LocalDate fromDate, LocalDate toDate) {
		Filter f = buildPendingWhere(searchPattern, fromDate, toDate);
		String sql = "SELECT COUNT(*) " + PENDING_BASE_FROM + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	public List<ApprovalsPendingItemData> loadPendingPage(String searchPattern, LocalDate fromDate, LocalDate toDate,
			int limit, int offset) {
		Filter f = buildPendingWhere(searchPattern, fromDate, toDate);
		// Note: composite index (status, created_at) recommended for pending list ordering
		String sql = """
				SELECT
				  sr.id,
				  sr.receipt_code,
				  u.full_name AS creator_name,
				  sr.receipt_date,
				  sr.total_amount,
				  sr.status,
				  sr.notes
				""" + PENDING_BASE_FROM + f.where + " ORDER BY sr.created_at ASC LIMIT " + limit + " OFFSET " + offset;
		return namedJdbc.query(sql, f.source, PENDING_ROW);
	}

	public long countHistory(String searchPattern, LocalDate fromDate, LocalDate toDate, String resolution) {
		Filter f = buildHistoryWhere(searchPattern, fromDate, toDate, resolution);
		String sql = "SELECT COUNT(*) " + HISTORY_BASE_FROM + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	public List<ApprovalsHistoryItemData> loadHistoryPage(String searchPattern, LocalDate fromDate, LocalDate toDate,
			String resolution, int limit, int offset) {
		Filter f = buildHistoryWhere(searchPattern, fromDate, toDate, resolution);
		String sql = """
				SELECT
				  sr.id,
				  sr.receipt_code,
				  u_creator.full_name AS creator_name,
				  sr.created_at,
				  sr.reviewed_at,
				  sr.total_amount,
				  sr.status AS resolution,
				  sr.rejection_reason,
				  sr.notes,
				  sr.reviewed_by,
				  u_rev.full_name AS reviewer_name,
				  sr.approved_by,
				  sr.approved_at
				""" + HISTORY_BASE_FROM + f.where + " ORDER BY sr.reviewed_at DESC LIMIT " + limit + " OFFSET " + offset;
		return namedJdbc.query(sql, f.source, HISTORY_ROW);
	}

	private static Filter buildPendingWhere(String searchPattern, LocalDate fromDate, LocalDate toDate) {
		StringBuilder sb = new StringBuilder(" WHERE sr.status = 'Pending'");
		MapSqlParameterSource src = new MapSqlParameterSource();
		if (searchPattern != null) {
			sb.append(" AND (sr.receipt_code ILIKE :_sp OR u.full_name ILIKE :_sp)");
			src.addValue("_sp", searchPattern);
		}
		if (fromDate != null) {
			sb.append(" AND sr.receipt_date >= :_from");
			src.addValue("_from", fromDate);
		}
		if (toDate != null) {
			sb.append(" AND sr.receipt_date <= :_to");
			src.addValue("_to", toDate);
		}
		return new Filter(sb.toString(), src);
	}

	private static Filter buildHistoryWhere(String searchPattern, LocalDate fromDate, LocalDate toDate,
			String resolution) {
		StringBuilder sb = new StringBuilder(
				" WHERE sr.status IN ('Approved', 'Rejected') AND sr.reviewed_at IS NOT NULL");
		MapSqlParameterSource src = new MapSqlParameterSource();
		if ("Approved".equalsIgnoreCase(resolution)) {
			sb.append(" AND sr.status = 'Approved'");
		}
		else if ("Rejected".equalsIgnoreCase(resolution)) {
			sb.append(" AND sr.status = 'Rejected'");
		}
		if (searchPattern != null) {
			sb.append(
					" AND (sr.receipt_code ILIKE :_sp OR u_creator.full_name ILIKE :_sp OR u_rev.full_name ILIKE :_sp)");
			src.addValue("_sp", searchPattern);
		}
		if (fromDate != null) {
			sb.append(" AND sr.reviewed_at >= :_from::timestamptz");
			src.addValue("_from", fromDate);
		}
		if (toDate != null) {
			sb.append(" AND sr.reviewed_at < (:_to::timestamptz + interval '1 day')");
			src.addValue("_to", toDate);
		}
		return new Filter(sb.toString(), src);
	}

	private static final RowMapper<ApprovalsPendingItemData> PENDING_ROW = (rs, i) -> mapPending(rs);

	private static ApprovalsPendingItemData mapPending(ResultSet rs) throws SQLException {
		LocalDate rd = rs.getObject("receipt_date", LocalDate.class);
		Instant dateInstant = rd != null ? rd.atStartOfDay(ZoneOffset.UTC).toInstant() : null;
		return new ApprovalsPendingItemData("stock_receipt", rs.getLong("id"), rs.getString("receipt_code"), "Inbound",
				rs.getString("creator_name"), dateInstant, rs.getBigDecimal("total_amount"), rs.getString("status"),
				rs.getString("notes"));
	}

	private static final RowMapper<ApprovalsHistoryItemData> HISTORY_ROW = (rs, i) -> mapHistory(rs);

	private static ApprovalsHistoryItemData mapHistory(ResultSet rs) throws SQLException {
		return new ApprovalsHistoryItemData("stock_receipt", rs.getLong("id"), rs.getString("receipt_code"), "Inbound",
				rs.getString("creator_name"), toInstant(rs.getTimestamp("created_at")),
				toInstantNonNull(rs.getTimestamp("reviewed_at")), rs.getBigDecimal("total_amount"),
				rs.getString("resolution"), rs.getString("rejection_reason"), rs.getString("notes"),
				(Integer) rs.getObject("reviewed_by", Integer.class), rs.getString("reviewer_name"),
				(Integer) rs.getObject("approved_by", Integer.class), toInstant(rs.getTimestamp("approved_at")));
	}

	private static Instant toInstant(Timestamp ts) {
		return ts != null ? ts.toInstant() : null;
	}

	private static Instant toInstantNonNull(Timestamp ts) {
		return ts != null ? ts.toInstant() : Instant.EPOCH;
	}

	/** Dùng khi cần pattern ILIKE an toàn (trim + escape wildcard). */
	public static String toSearchPatternOrNull(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		return InventoryListJdbcRepository.buildSearchPattern(raw);
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
