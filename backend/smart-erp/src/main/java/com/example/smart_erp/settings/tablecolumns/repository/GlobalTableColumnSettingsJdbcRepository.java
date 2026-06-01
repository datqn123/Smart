package com.example.smart_erp.settings.tablecolumns.repository;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

@Repository
public class GlobalTableColumnSettingsJdbcRepository {

	private final NamedParameterJdbcTemplate namedJdbc;

	public GlobalTableColumnSettingsJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public List<Row> findAll() {
		String sql = """
				SELECT
				  s.table_key,
				  s.hidden_columns::text AS hidden_columns_json,
				  s.column_order::text AS column_order_json,
				  s.updated_at,
				  u.full_name AS updated_by_name
				FROM global_table_column_settings s
				LEFT JOIN users u ON u.id = s.updated_by
				ORDER BY s.table_key
				""";
		return namedJdbc.query(sql, (rs, i) -> new Row(
				rs.getString("table_key"),
				rs.getString("hidden_columns_json"),
				rs.getString("column_order_json"),
				toInstant(rs.getTimestamp("updated_at")),
				rs.getString("updated_by_name")));
	}

	public void upsert(String tableKey, String hiddenColumnsJson, String columnOrderJson, int updatedBy) {
		String sql = """
				INSERT INTO global_table_column_settings (
				  table_key, hidden_columns, column_order, updated_by
				) VALUES (
				  :tableKey, CAST(:hiddenColumnsJson AS jsonb), CAST(:columnOrderJson AS jsonb), :updatedBy
				)
				ON CONFLICT (table_key) DO UPDATE SET
				  hidden_columns = EXCLUDED.hidden_columns,
				  column_order = EXCLUDED.column_order,
				  updated_by = EXCLUDED.updated_by,
				  updated_at = CURRENT_TIMESTAMP
				""";
		MapSqlParameterSource p = new MapSqlParameterSource()
				.addValue("tableKey", tableKey)
				.addValue("hiddenColumnsJson", hiddenColumnsJson)
				.addValue("columnOrderJson", columnOrderJson)
				.addValue("updatedBy", updatedBy);
		namedJdbc.update(sql, p);
	}

	private static Instant toInstant(Timestamp ts) {
		return ts == null ? null : ts.toInstant();
	}

	public record Row(
			String tableKey,
			String hiddenColumnsJson,
			String columnOrderJson,
			Instant updatedAt,
			String updatedByName) {
	}
}
