package com.example.smart_erp.finance.cashtx;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.sql.Types;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.finance.cashtx.response.CashTransactionItemData;
import com.example.smart_erp.finance.ledger.FinanceLedgerJdbcRepository;

/**
 * SRS Task064–068 — persistence {@code cashtransactions} + {@code financeledger}.
 */
@SuppressWarnings("null")
@Repository
public class CashTransactionJdbcRepository {

	public record CashLockRow(long id, String transactionCode, String direction, BigDecimal amount, String category,
			String description, String paymentMethod, String status, LocalDate transactionDate, Integer financeLedgerId,
			int createdBy, int performedBy, int fundId) {
	}

	private static final String ITEM_SELECT = """
			SELECT ct.id, ct.transaction_code, ct.direction, ct.amount, ct.category, ct.description,
			  ct.payment_method, ct.status, ct.transaction_date, ct.finance_ledger_id,
			  ct.created_by, COALESCE(uc.full_name, '') AS created_by_name,
			  ct.performed_by, COALESCE(up.full_name, '') AS performed_by_name,
			  ct.created_at, ct.updated_at, ct.fund_id, cf.code AS fund_code
			FROM cashtransactions ct
			LEFT JOIN users uc ON uc.id = ct.created_by
			LEFT JOIN users up ON up.id = ct.performed_by
			LEFT JOIN cash_funds cf ON cf.id = ct.fund_id
			""";

	private static final RowMapper<CashTransactionItemData> ITEM_ROW = (rs, i) -> mapItem(rs);

	private static CashTransactionItemData mapItem(java.sql.ResultSet rs) throws java.sql.SQLException {
		Object fldObj = rs.getObject("finance_ledger_id");
		Long fld = null;
		if (fldObj instanceof Number n) {
			fld = n.longValue();
		}
		Timestamp ca = rs.getTimestamp("created_at");
		Timestamp ua = rs.getTimestamp("updated_at");
		Integer fundId = (Integer) rs.getObject("fund_id", Integer.class);
		String fundCode = rs.getString("fund_code");
		return new CashTransactionItemData(rs.getLong("id"), rs.getString("transaction_code"), rs.getString("direction"),
				rs.getBigDecimal("amount"), rs.getString("category"), rs.getString("description"), rs.getString("payment_method"),
				rs.getString("status"), rs.getObject("transaction_date", LocalDate.class).toString(), fld, rs.getInt("created_by"),
				rs.getString("created_by_name"), rs.getInt("performed_by"), rs.getString("performed_by_name"),
				ca != null ? ca.toInstant() : null, ua != null ? ua.toInstant() : null, fundId, fundCode);
	}

	private static final RowMapper<CashLockRow> LOCK_ROW = (rs, i) -> {
		Object fld = rs.getObject("finance_ledger_id");
		Integer fldInt = fld instanceof Number n ? n.intValue() : null;
		return new CashLockRow(rs.getLong("id"), rs.getString("transaction_code"), rs.getString("direction"), rs.getBigDecimal("amount"),
				rs.getString("category"), rs.getString("description"), rs.getString("payment_method"), rs.getString("status"),
				rs.getObject("transaction_date", LocalDate.class), fldInt, rs.getInt("created_by"), rs.getInt("performed_by"),
				rs.getInt("fund_id"));
	};

	private final NamedParameterJdbcTemplate namedJdbc;

	public CashTransactionJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public Optional<CashTransactionItemData> findItemById(long id) {
		String sql = ITEM_SELECT + " WHERE ct.id = :id";
		var list = namedJdbc.query(sql, new MapSqlParameterSource("id", id), ITEM_ROW);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public long countList(String direction, String status, LocalDate dateFrom, LocalDate dateTo, Integer fundId,
			String searchPattern) {
		StringBuilder where = new StringBuilder(" WHERE 1=1 ");
		var src = new MapSqlParameterSource();
		appendFilters(where, src, direction, status, dateFrom, dateTo, fundId, searchPattern, false);
		String sql = "SELECT COUNT(*) FROM cashtransactions ct" + where;
		Long c = namedJdbc.queryForObject(sql, src, Long.class);
		return c != null ? c : 0L;
	}

	public List<CashTransactionItemData> loadPage(String direction, String status, LocalDate dateFrom, LocalDate dateTo,
			Integer fundId, String searchPattern, int limit, int offset, boolean sortByCreatedAt) {
		StringBuilder where = new StringBuilder(" WHERE 1=1 ");
		var src = new MapSqlParameterSource();
		appendFilters(where, src, direction, status, dateFrom, dateTo, fundId, searchPattern, true);
		String orderBy = sortByCreatedAt ? "ct.created_at DESC, ct.id DESC" : "ct.transaction_date DESC, ct.id DESC";
		String sql = ITEM_SELECT + where + " ORDER BY " + orderBy + " LIMIT :lim OFFSET :off";
		src.addValue("lim", limit).addValue("off", offset);
		return namedJdbc.query(sql, src, ITEM_ROW);
	}

	private static void appendFilters(StringBuilder where, MapSqlParameterSource src, String direction, String status,
			LocalDate dateFrom, LocalDate dateTo, Integer fundId, String searchPattern, boolean includeUserSearch) {
		if (direction != null && !direction.isBlank()) {
			where.append(" AND ct.direction = :dir ");
			src.addValue("dir", direction.trim());
		}
		if (status != null && !status.isBlank()) {
			where.append(" AND ct.status = :st ");
			src.addValue("st", status.trim());
		}
		boolean noDate = dateFrom == null && dateTo == null;
		if (!noDate) {
			where.append(" AND (:df IS NULL OR ct.transaction_date >= :df) ");
			where.append(" AND (:dt IS NULL OR ct.transaction_date <= :dt) ");
			src.addValue("df", dateFrom != null ? java.sql.Date.valueOf(dateFrom) : null, Types.DATE);
			src.addValue("dt", dateTo != null ? java.sql.Date.valueOf(dateTo) : null, Types.DATE);
		}
		if (fundId != null) {
			where.append(" AND ct.fund_id = :fundId ");
			src.addValue("fundId", fundId);
		}
		if (searchPattern != null) {
			if (includeUserSearch) {
				where.append(
						" AND (ct.transaction_code ILIKE :sp OR ct.category ILIKE :sp OR ct.description ILIKE :sp OR uc.full_name ILIKE :sp OR up.full_name ILIKE :sp) ");
			}
			else {
				where.append(
						" AND (ct.transaction_code ILIKE :sp OR ct.category ILIKE :sp OR ct.description ILIKE :sp) ");
			}
			src.addValue("sp", searchPattern);
		}
	}

	public int nextCodeSequenceSuffix(int year, String prefix) {
		String sql = """
				SELECT COALESCE(MAX(split_part(ct.transaction_code, '-', 3)::int), 0)
				FROM cashtransactions ct
				WHERE ct.transaction_code LIKE :pfx || '-' || CAST(:y AS text) || '-%'
				""";
		Integer n = namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("pfx", prefix).addValue("y", year), Integer.class);
		return n != null ? n : 0;
	}

	public long insert(String transactionCode, String direction, BigDecimal amount, String category, String description,
			String paymentMethod, LocalDate transactionDate, int fundId, int createdBy) {
		String sql = """
				INSERT INTO cashtransactions (transaction_code, direction, amount, category, description, payment_method,
				  status, transaction_date, finance_ledger_id, fund_id, created_by, performed_by)
				VALUES (:code, :dir, :amt, :cat, :desc, :pm, 'Pending', :td, NULL, :fid, :cb, :pb)
				RETURNING id
				""";
		Long id = namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("code", transactionCode).addValue("dir", direction).addValue("amt", amount)
						.addValue("cat", category).addValue("desc", description, Types.VARCHAR).addValue("pm", paymentMethod)
						.addValue("td", java.sql.Date.valueOf(transactionDate)).addValue("fid", fundId).addValue("cb", createdBy)
						.addValue("pb", createdBy),
				Long.class);
		if (id == null) {
			throw new IllegalStateException("INSERT cashtransactions không trả id");
		}
		return id;
	}

	public Optional<CashLockRow> lockForUpdate(long id) {
		String sql = """
				SELECT ct.id, ct.transaction_code, ct.direction, ct.amount, ct.category, ct.description, ct.payment_method,
				  ct.status, ct.transaction_date, ct.finance_ledger_id, ct.created_by, ct.performed_by, ct.fund_id
				FROM cashtransactions ct WHERE ct.id = :id FOR UPDATE
				""";
		var list = namedJdbc.query(sql, new MapSqlParameterSource("id", id), LOCK_ROW);
		return list.isEmpty() ? Optional.empty() : Optional.of(list.getFirst());
	}

	public int insertFinanceLedgerAndReturnId(LocalDate transactionDate, String transactionType, int cashTxId,
			BigDecimal signedAmount, String description, int fundId, int createdBy) {
		String sql = """
				INSERT INTO financeledger (transaction_date, transaction_type, reference_type, reference_id, amount, description, created_by, fund_id)
				VALUES (:td, :ttype, 'CashTransaction', :rid, :amt, :desc, :cb, :fid)
				RETURNING id
				""";
		Integer id = namedJdbc.queryForObject(sql,
				new MapSqlParameterSource("td", java.sql.Date.valueOf(transactionDate)).addValue("ttype", transactionType)
						.addValue("rid", cashTxId).addValue("amt", signedAmount).addValue("desc", description, Types.VARCHAR)
						.addValue("cb", createdBy).addValue("fid", fundId),
				Integer.class);
		if (id == null) {
			throw new IllegalStateException("INSERT financeledger không trả id");
		}
		return id;
	}

	public void updateRowAfterPatch(long id, BigDecimal amount, String category, String description, String paymentMethod,
			LocalDate transactionDate, String status, Integer financeLedgerId, int performedBy) {
		String sql = """
				UPDATE cashtransactions SET amount = :amt, category = :cat, description = :desc, payment_method = :pm,
				  transaction_date = :td, status = :st, finance_ledger_id = :fld, performed_by = :pb, updated_at = NOW()
				WHERE id = :id
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("id", id).addValue("amt", amount).addValue("cat", category)
						.addValue("desc", description, Types.VARCHAR).addValue("pm", paymentMethod)
						.addValue("td", java.sql.Date.valueOf(transactionDate)).addValue("st", status)
						.addValue("fld", financeLedgerId, Types.INTEGER).addValue("pb", performedBy));
	}

	public int deleteIfAllowed(long id) {
		String sql = "DELETE FROM cashtransactions WHERE id = :id AND status IN ('Pending','Cancelled') AND finance_ledger_id IS NULL";
		return namedJdbc.update(sql, new MapSqlParameterSource("id", id));
	}

	public static String toSearchPatternOrNull(String raw) {
		return FinanceLedgerJdbcRepository.toSearchPatternOrNull(raw);
	}
}
