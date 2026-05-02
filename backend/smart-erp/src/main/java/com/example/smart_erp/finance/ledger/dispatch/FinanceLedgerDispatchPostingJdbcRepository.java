package com.example.smart_erp.finance.ledger.dispatch;

import java.math.BigDecimal;
import java.sql.Types;
import java.time.LocalDate;
import java.util.Map;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

/**
 * Ghi sổ COGS cho phiếu xuất kho (PRD finance-ledger-unified-business-postings, phương án B).
 */
@SuppressWarnings("null")
@Repository
public class FinanceLedgerDispatchPostingJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public FinanceLedgerDispatchPostingJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	/**
	 * Đã có bút COGS “chính” (không phải dòng hoàn) — không ghi trùng lần finalize.
	 */
	public boolean existsPrimaryCogsPosting(int dispatchId) {
		Integer n = namedJdbc.queryForObject("""
				SELECT COUNT(*)::int FROM financeledger fl
				WHERE fl.reference_type = 'StockDispatch' AND fl.reference_id = :id
				  AND fl.transaction_type = 'OperatingExpense'
				  AND COALESCE(fl.description, '') NOT LIKE 'Hoàn COGS%'
				""", Map.of("id", dispatchId), Integer.class);
		return n != null && n > 0;
	}

	public BigDecimal sumNetAmountForDispatch(int dispatchId) {
		BigDecimal s = namedJdbc.queryForObject("""
				SELECT COALESCE(SUM(amount), 0) FROM financeledger
				WHERE reference_type = 'StockDispatch' AND reference_id = :id
				  AND transaction_type = 'OperatingExpense'
				""", Map.of("id", dispatchId), BigDecimal.class);
		return s != null ? s : BigDecimal.ZERO;
	}

	public void insertOperatingExpenseStockDispatch(LocalDate transactionDate, int dispatchId, BigDecimal signedAmount,
			String description, int createdBy) {
		String sql = """
				INSERT INTO financeledger (transaction_date, transaction_type, reference_type, reference_id, amount, description, created_by, fund_id)
				VALUES (:td, 'OperatingExpense', 'StockDispatch', :rid, :amt, :desc, :cb,
				  (SELECT cf.id FROM cash_funds cf WHERE cf.is_default = TRUE ORDER BY cf.id LIMIT 1))
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("td", java.sql.Date.valueOf(transactionDate)).addValue("rid", dispatchId)
						.addValue("amt", signedAmount).addValue("desc", description, Types.VARCHAR)
						.addValue("cb", createdBy));
	}
}
