package com.example.smart_erp.finance.ledger;

import java.math.BigDecimal;
import java.sql.Types;
import java.time.LocalDate;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

/**
 * Ghi {@code financeledger} từ nghiệp vụ (idempotent theo reference + transaction_type).
 */
@SuppressWarnings("null")
@Repository
public class FinanceLedgerPostingJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public FinanceLedgerPostingJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public boolean existsPosting(String referenceType, int referenceId, String transactionType) {
		Integer n = namedJdbc.queryForObject("""
				SELECT COUNT(*)::int FROM financeledger
				WHERE reference_type = :rt AND reference_id = :rid AND transaction_type = :tt
				""", new MapSqlParameterSource("rt", referenceType).addValue("rid", referenceId).addValue("tt",
				transactionType), Integer.class);
		return n != null && n > 0;
	}

	public void insertPosting(LocalDate transactionDate, String transactionType, String referenceType, int referenceId,
			BigDecimal amount, String description, int createdBy) {
		String sql = """
				INSERT INTO financeledger (transaction_date, transaction_type, reference_type, reference_id, amount, description, created_by, fund_id)
				VALUES (:td, :ttype, :rt, :rid, :amt, :desc, :cb,
				  (SELECT cf.id FROM cash_funds cf WHERE cf.is_default = TRUE ORDER BY cf.id LIMIT 1))
				""";
		namedJdbc.update(sql,
				new MapSqlParameterSource("td", java.sql.Date.valueOf(transactionDate)).addValue("ttype", transactionType)
						.addValue("rt", referenceType).addValue("rid", referenceId).addValue("amt", amount)
						.addValue("desc", description, Types.VARCHAR).addValue("cb", createdBy));
	}
}
