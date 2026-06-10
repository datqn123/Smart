package com.example.smart_erp.settings.systemlogs;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

@SuppressWarnings("null")
@Repository
public class SystemLogsJdbcRepository {

	private static final String BASE_FROM = """
			FROM systemlogs s
			LEFT JOIN users u ON u.id = s.user_id
			""";

	private static final String SELECT_LIST_COLUMNS = """
			SELECT
			  s.id,
			  s.created_at,
			  s.log_level,
			  s.module,
			  s.action,
			  s.message,
			  s.context_data,
			  u.full_name
			""";

	private static final String SELECT_DETAIL_COLUMNS = """
			SELECT
			  s.id,
			  s.created_at,
			  s.log_level,
			  s.module,
			  s.action,
			  s.message,
			  s.stack_trace,
			  s.context_data,
			  u.full_name
			""";

	private final NamedParameterJdbcTemplate namedJdbc;

	public SystemLogsJdbcRepository(NamedParameterJdbcTemplate namedJdbc) {
		this.namedJdbc = namedJdbc;
	}

	public long countRows(String searchPattern, String module, String logLevel, Instant dateFrom, Instant dateTo) {
		Filter f = buildFilter(searchPattern, module, logLevel, dateFrom, dateTo);
		String sql = "SELECT COUNT(*) " + BASE_FROM + f.where;
		Long c = namedJdbc.queryForObject(sql, f.source, Long.class);
		return c != null ? c : 0L;
	}

	public List<SystemLogRow> loadPage(String searchPattern, String module, String logLevel, Instant dateFrom, Instant dateTo, int page,
			int limit) {
		Filter f = buildFilter(searchPattern, module, logLevel, dateFrom, dateTo);
		int offset = (page - 1) * limit;
		String sql = SELECT_LIST_COLUMNS + BASE_FROM + f.where + " ORDER BY s.created_at DESC LIMIT " + limit + " OFFSET " + offset;
		return namedJdbc.query(sql, f.source, LIST_ROW);
	}

	public Optional<SystemLogDetailRow> findById(long id) {
		String sql = SELECT_DETAIL_COLUMNS + BASE_FROM + " WHERE s.id = :_id";
		var src = new MapSqlParameterSource().addValue("_id", id);
		List<SystemLogDetailRow> rows = namedJdbc.query(sql, src, DETAIL_ROW);
		return rows.stream().findFirst();
	}

	private static Filter buildFilter(String searchPattern, String module, String logLevel, Instant dateFrom, Instant dateTo) {
		StringBuilder sb = new StringBuilder(" WHERE 1=1");
		var src = new MapSqlParameterSource();

		if (module != null && !module.isBlank()) {
			sb.append(" AND s.module = :_module");
			src.addValue("_module", module.trim());
		}

		if (logLevel != null && !logLevel.isBlank()) {
			sb.append(" AND s.log_level = :_log_level");
			src.addValue("_log_level", logLevel.trim());
		}

		if (dateFrom != null) {
			sb.append(" AND s.created_at >= :_date_from");
			src.addValue("_date_from", dateFrom);
		}

		if (dateTo != null) {
			sb.append(" AND s.created_at <= :_date_to");
			src.addValue("_date_to", dateTo);
		}

		if (searchPattern != null && !searchPattern.isBlank() && !"%".equals(searchPattern)) {
			sb.append("""
					 AND (
					  s.message ILIKE :_search OR
					  s.action  ILIKE :_search OR
					  s.module  ILIKE :_search OR
					  COALESCE(u.full_name, '') ILIKE :_search
					)
					""");
			src.addValue("_search", searchPattern);
		}

		return new Filter(sb.toString(), src);
	}

	private static final RowMapper<SystemLogRow> LIST_ROW = SystemLogsJdbcRepository::mapListRow;

	private static SystemLogRow mapListRow(ResultSet rs, int i) throws SQLException {
		Instant createdAt = rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toInstant()
				: Instant.parse("1970-01-01T00:00:00Z");
		return new SystemLogRow(
				rs.getLong("id"),
				createdAt,
				rs.getString("log_level"),
				rs.getString("module"),
				rs.getString("action"),
				rs.getString("message"),
				rs.getString("context_data"),
				rs.getString("full_name"));
	}

	private static final RowMapper<SystemLogDetailRow> DETAIL_ROW = SystemLogsJdbcRepository::mapDetailRow;

	private static SystemLogDetailRow mapDetailRow(ResultSet rs, int i) throws SQLException {
		Instant createdAt = rs.getTimestamp("created_at") != null ? rs.getTimestamp("created_at").toInstant()
				: Instant.parse("1970-01-01T00:00:00Z");
		return new SystemLogDetailRow(
				rs.getLong("id"),
				createdAt,
				rs.getString("log_level"),
				rs.getString("module"),
				rs.getString("action"),
				rs.getString("message"),
				rs.getString("stack_trace"),
				rs.getString("context_data"),
				rs.getString("full_name"));
	}

	public record SystemLogRow(
			long id,
			Instant createdAt,
			String logLevel,
			String module,
			String action,
			String message,
			String contextDataJson,
			String fullName) {
	}

	public record SystemLogDetailRow(
			long id,
			Instant createdAt,
			String logLevel,
			String module,
			String action,
			String message,
			String stackTrace,
			String contextDataJson,
			String fullName) {
	}

	private static final class Filter {
		final String where;
		final MapSqlParameterSource source;

		Filter(String w, MapSqlParameterSource s) {
			this.where = Objects.requireNonNull(w, "where");
			this.source = Objects.requireNonNull(s, "source");
		}
	}
}

