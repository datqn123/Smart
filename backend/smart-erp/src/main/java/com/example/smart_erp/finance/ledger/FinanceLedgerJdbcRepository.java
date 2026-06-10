package com.example.smart_erp.finance.ledger;

import java.math.BigDecimal;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import com.example.smart_erp.finance.ledger.response.FinanceLedgerItemData;
import com.example.smart_erp.inventory.repository.InventoryListJdbcRepository;

/**
 * SRS Task063 — đọc sổ cái tài chính từ bảng {@code financeledger}.
 */
@SuppressWarnings("null")
@Repository
public class FinanceLedgerJdbcRepository {

	private static final String BASE_FROM = """
			FROM financeledger fl
			LEFT JOIN salesorders so
			  ON fl.reference_type = 'SalesOrder'
			  AND fl.reference_id = so.id
			""";

	private final NamedParameterJdbcTemplate namedJdbc;

	public FinanceLedgerJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public long countFiltered(LocalDate effectiveFrom, LocalDate effectiveTo, String transactionType, String referenceType,
			String searchPattern) {
		Filter f = buildWhere(effectiveFrom, effectiveTo, transactionType, referenceType, searchPattern);
		String sql = "SELECT COUNT(*) " + BASE_FROM + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	public List<FinanceLedgerItemData> loadPage(LocalDate effectiveFrom, LocalDate effectiveTo, String transactionType,
			String referenceType, String searchPattern, int limit, int offset) {
		Filter f = buildWhere(effectiveFrom, effectiveTo, transactionType, referenceType, searchPattern);

		String filteredCte = """
				WITH filtered AS (
				  SELECT
				    fl.id,
				    fl.transaction_date,
				    fl.transaction_type,
				    fl.reference_type,
				    fl.reference_id,
				    fl.amount,
				    fl.description,
				    so.order_code AS so_code
				  """
				+ BASE_FROM + f.where + """
				)
				""";

		// Starting balance: sum of all amounts before the current page
		String startingBalanceSql = filteredCte + """
				SELECT COALESCE(SUM(amount), 0) AS start_balance FROM (
				  SELECT amount FROM filtered ORDER BY transaction_date ASC, id ASC LIMIT :_offset
				) t
				""";
		MapSqlParameterSource balanceParams = new MapSqlParameterSource();
		balanceParams.addValues(f.source.getValues());
		balanceParams.addValue("_offset", offset);
		BigDecimal startBalance = namedJdbc.queryForObject(startingBalanceSql, balanceParams, BigDecimal.class);
		if (startBalance == null) {
			startBalance = BigDecimal.ZERO;
		}

		String pageSql = filteredCte + """
				SELECT
				  id,
				  transaction_date,
				  CASE
				    WHEN reference_type = 'SalesOrder' AND so_code IS NOT NULL THEN so_code
				    ELSE 'FL-' || id::text
				  END AS transaction_code,
				  description,
				  transaction_type,
				  reference_type,
				  reference_id,
				  amount,
				  CASE
				    WHEN amount < 0 THEN (amount * -1)
				    ELSE 0
				  END AS debit,
				  CASE
				    WHEN amount > 0 THEN amount
				    ELSE 0
				  END AS credit
				FROM filtered
				ORDER BY transaction_date ASC, id ASC
				LIMIT :_limit OFFSET :_offset
				""";
		MapSqlParameterSource pageParams = new MapSqlParameterSource();
		pageParams.addValues(f.source.getValues());
		pageParams.addValue("_limit", limit);
		pageParams.addValue("_offset", offset);
		List<FinanceLedgerItemData> rows = namedJdbc.query(pageSql, pageParams, (rs, rn) -> {
			return new FinanceLedgerItemData(rs.getLong("id"), rs.getObject("transaction_date", LocalDate.class),
					rs.getString("transaction_code"), rs.getString("description"), rs.getString("transaction_type"),
					rs.getString("reference_type"), (Integer) rs.getObject("reference_id", Integer.class),
					rs.getBigDecimal("amount"), rs.getBigDecimal("debit"), rs.getBigDecimal("credit"), null);
		});

		BigDecimal running = startBalance;
		List<FinanceLedgerItemData> result = new ArrayList<>(rows.size());
		for (FinanceLedgerItemData row : rows) {
			running = running.add(row.amount());
			result.add(new FinanceLedgerItemData(row.id(), row.date(), row.transactionCode(), row.description(),
					row.transactionType(), row.referenceType(), row.referenceId(), row.amount(), row.debit(),
					row.credit(), running));
		}
		return result;
	}

	/** Dùng khi cần pattern ILIKE an toàn (trim + escape wildcard). */
	public static String toSearchPatternOrNull(String raw) {
		if (raw == null || raw.isBlank()) {
			return null;
		}
		return InventoryListJdbcRepository.buildSearchPattern(raw);
	}

	private static Filter buildWhere(LocalDate effectiveFrom, LocalDate effectiveTo, String transactionType,
			String referenceType, String searchPattern) {
		StringBuilder sb = new StringBuilder(" WHERE 1=1");
		MapSqlParameterSource src = new MapSqlParameterSource();
		if (effectiveFrom != null) {
			sb.append(" AND fl.transaction_date >= :_from");
			src.addValue("_from", effectiveFrom);
		}
		if (effectiveTo != null) {
			sb.append(" AND fl.transaction_date <= :_to");
			src.addValue("_to", effectiveTo);
		}
		if (transactionType != null) {
			sb.append(" AND fl.transaction_type = :_tt");
			src.addValue("_tt", transactionType);
		}
		if (referenceType != null) {
			sb.append(" AND fl.reference_type = :_rt");
			src.addValue("_rt", referenceType);
		}
		if (searchPattern != null) {
			sb.append("""
					 AND (
					   fl.description ILIKE :_sp
					   OR (
					     CASE
					       WHEN fl.reference_type = 'SalesOrder' AND so.order_code IS NOT NULL THEN so.order_code
					       ELSE 'FL-' || fl.id::text
					     END
					   ) ILIKE :_sp
					 )
					""");
			src.addValue("_sp", searchPattern);
		}
		return new Filter(sb.toString(), src);
	}

	private static final RowMapper<FinanceLedgerItemData> ROW = (rs, i) -> mapRow(rs);

	private static FinanceLedgerItemData mapRow(ResultSet rs) throws SQLException {
		return new FinanceLedgerItemData(rs.getLong("id"), rs.getObject("transaction_date", LocalDate.class),
				rs.getString("transaction_code"), rs.getString("description"), rs.getString("transaction_type"),
				rs.getString("reference_type"), (Integer) rs.getObject("reference_id", Integer.class),
				rs.getBigDecimal("amount"), rs.getBigDecimal("debit"), rs.getBigDecimal("credit"),
				rs.getBigDecimal("balance"));
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

