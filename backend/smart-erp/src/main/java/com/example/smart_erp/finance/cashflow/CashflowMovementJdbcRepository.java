package com.example.smart_erp.finance.cashflow;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.List;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.finance.cashflow.response.CashflowMovementItemData;
import com.example.smart_erp.finance.cashflow.response.CashflowMovementSummaryData;
import com.example.smart_erp.finance.ledger.FinanceLedgerJdbcRepository;

/**
 * PRD — read model movements (financeledger ∪ cashtransactions pending/cancelled).
 */
@SuppressWarnings("null")
@Repository
public class CashflowMovementJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public CashflowMovementJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	private static String movementsCte(Integer fundId, String searchPattern) {
		String fundLedger = fundId == null ? "" : " AND fl.fund_id = :fundId ";
		String fundCash = fundId == null ? "" : " AND ct.fund_id = :fundId ";
		String searchLedger = searchPattern == null ? "" : " AND fl.description ILIKE :sp ";
		String searchCash = searchPattern == null ? ""
				: " AND (ct.transaction_code ILIKE :sp OR ct.category ILIKE :sp OR ct.description ILIKE :sp) ";
		return """
				movements AS NOT MATERIALIZED (
				  SELECT
				    'ledger:' || fl.id::text AS line_id,
				    'Ledger' AS source_kind,
				    fl.transaction_date AS transaction_date,
				    fl.amount AS signed_amount,
				    CASE WHEN fl.amount >= 0 THEN 'Income' ELSE 'Expense' END AS direction,
				    fl.description AS description,
				    fl.reference_type AS reference_type,
				    fl.reference_id AS reference_id,
				    fl.fund_id AS fund_id,
				    cf.code AS fund_code,
				    CASE WHEN fl.reference_type = 'CashTransaction' THEN fl.reference_id ELSE NULL END AS cash_tx_id,
				    NULL::varchar(20) AS status,
				    NULL::varchar(500) AS category,
				    fl.created_at AS sort_ts
				  FROM financeledger fl
				  LEFT JOIN cash_funds cf ON cf.id = fl.fund_id
				  WHERE fl.transaction_date BETWEEN :df AND :dt
				"""
				+ fundLedger + searchLedger + """
				  UNION ALL
				  SELECT
				    'cash:' || ct.id::text,
				    'CashTransaction',
				    ct.transaction_date,
				    CASE WHEN ct.direction = 'Income' THEN ct.amount ELSE -ct.amount END,
				    ct.direction,
				    ct.description,
				    NULL,
				    NULL,
				    ct.fund_id,
				    cf2.code,
				    ct.id::int,
				    ct.status,
				    ct.category,
				    ct.created_at
				  FROM cashtransactions ct
				  LEFT JOIN cash_funds cf2 ON cf2.id = ct.fund_id
				  WHERE ct.transaction_date BETWEEN :df AND :dt
				    AND ct.status IN ('Pending','Cancelled')
				""" + fundCash + searchCash + """
				)
				""";
	}

	public long count(LocalDate dateFrom, LocalDate dateTo, Integer fundId, String searchPattern) {
		String sql = "WITH " + movementsCte(fundId, searchPattern) + " SELECT COUNT(*) FROM movements";
		var src = baseParams(dateFrom, dateTo, fundId, searchPattern);
		Long c = namedJdbc.queryForObject(sql, src, Long.class);
		return c != null ? c : 0L;
	}

	public CashflowMovementSummaryData summarize(LocalDate dateFrom, LocalDate dateTo, Integer fundId, String searchPattern) {
		String sql = """
				WITH
				"""
				+ movementsCte(fundId, searchPattern)
				+ """
				SELECT
				  COALESCE(SUM(CASE WHEN signed_amount > 0 THEN signed_amount ELSE 0 END), 0) AS total_income,
				  COALESCE(SUM(CASE WHEN signed_amount < 0 THEN (-signed_amount) ELSE 0 END), 0) AS total_expense
				FROM movements
				""";
		var src = baseParams(dateFrom, dateTo, fundId, searchPattern);
		return namedJdbc.queryForObject(sql, src, (rs, rowNum) -> {
			BigDecimal ti = rs.getBigDecimal("total_income");
			BigDecimal te = rs.getBigDecimal("total_expense");
			if (ti == null) {
				ti = BigDecimal.ZERO;
			}
			if (te == null) {
				te = BigDecimal.ZERO;
			}
			BigDecimal net = ti.subtract(te);
			return new CashflowMovementSummaryData(ti, te, net);
		});
	}

	public List<CashflowMovementItemData> loadPage(LocalDate dateFrom, LocalDate dateTo, Integer fundId, String searchPattern,
			int limit, int offset) {
		String sql = """
				WITH
				"""
				+ movementsCte(fundId, searchPattern)
				+ """
				SELECT
				  line_id,
				  source_kind,
				  transaction_date,
				  ABS(signed_amount) AS display_amount,
				  direction,
				  description,
				  reference_type,
				  reference_id,
				  fund_id,
				  fund_code,
				  cash_tx_id,
				  status,
				  category
				FROM movements
				ORDER BY transaction_date DESC, sort_ts DESC, line_id DESC
				LIMIT :lim OFFSET :off
				""";
		var src = baseParams(dateFrom, dateTo, fundId, searchPattern);
		src.addValue("lim", limit).addValue("off", offset);
		return namedJdbc.query(sql, src, ROW);
	}

	private static MapSqlParameterSource baseParams(LocalDate dateFrom, LocalDate dateTo, Integer fundId, String searchPattern) {
		var src = new MapSqlParameterSource("df", java.sql.Date.valueOf(dateFrom)).addValue("dt", java.sql.Date.valueOf(dateTo));
		if (fundId != null) {
			src.addValue("fundId", fundId);
		}
		if (searchPattern != null) {
			src.addValue("sp", searchPattern);
		}
		return src;
	}

	private static final RowMapper<CashflowMovementItemData> ROW = (rs, i) -> mapRow(rs);

	private static CashflowMovementItemData mapRow(ResultSet rs) throws SQLException {
		String lineId = rs.getString("line_id");
		String sk = rs.getString("source_kind");
		LocalDate td = rs.getObject("transaction_date", LocalDate.class);
		BigDecimal amt = rs.getBigDecimal("display_amount");
		String dir = rs.getString("direction");
		String desc = rs.getString("description");
		String rt = rs.getString("reference_type");
		Integer rid = (Integer) rs.getObject("reference_id", Integer.class);
		Integer fid = (Integer) rs.getObject("fund_id", Integer.class);
		String fc = rs.getString("fund_code");
		Integer ctx = (Integer) rs.getObject("cash_tx_id", Integer.class);
		Long cashLong = ctx != null ? ctx.longValue() : null;
		String st = rs.getString("status");
		String cat = rs.getString("category");
		return new CashflowMovementItemData(lineId, sk, td.toString(), amt, dir, desc, rt, rid, fid, fc, cashLong, st, cat);
	}

	public static String toSearchPatternOrNull(String raw) {
		return FinanceLedgerJdbcRepository.toSearchPatternOrNull(raw);
	}
}
