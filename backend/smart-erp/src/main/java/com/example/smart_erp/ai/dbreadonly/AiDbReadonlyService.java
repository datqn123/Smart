package com.example.smart_erp.ai.dbreadonly;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.ColumnMetaDto;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.McpToolErrorResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlDescribeHttpResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;
import com.example.smart_erp.ai.dbreadonly.templates.DbTemplateExecutor;

/**
 * Read-only JDBC bridge implementing MCP {@code sql.describe} and {@code sql.query_readonly} semantics
 * (template-first, allowlisted objects, capped rows). Intended for the Python AI service, not public UI.
 */
@Service
public class AiDbReadonlyService {

	private static final Set<String> DESCRIBE_ALLOWLIST = Set.of("inventory", "products", "salesorders");

	private final JdbcTemplate jdbcTemplate;

	private final Map<String, DbTemplateExecutor> executors;

	public AiDbReadonlyService(JdbcTemplate jdbcTemplate, List<DbTemplateExecutor> executors) {
		this.jdbcTemplate = jdbcTemplate;
		this.executors = indexExecutors(executors);
	}

	public SqlDescribeHttpResponse describe(String objectNameRaw, String correlationId) {
		String correlation = blankToRandom(correlationId);
		QualifiedName qn = parseObjectName(objectNameRaw);
		if (!DESCRIBE_ALLOWLIST.contains(qn.table())) {
			mcpFail(HttpStatus.BAD_REQUEST, "DB_QUERY_REJECTED", "Object không nằm trong allowlist read-only: " + objectNameRaw,
					false, correlation);
		}

		String sql = """
				SELECT column_name, data_type, is_nullable
				FROM information_schema.columns
				WHERE table_schema = ? AND table_name = ?
				ORDER BY ordinal_position
				""";
		List<ColumnMetaDto> columns = new ArrayList<>();
		jdbcTemplate.query(sql, rs -> {
			String name = rs.getString("column_name");
			String type = simplifyType(rs.getString("data_type"));
			boolean nullable = "YES".equalsIgnoreCase(rs.getString("is_nullable"));
			columns.add(new ColumnMetaDto(name, type, nullable));
		}, qn.schema(), qn.table());

		if (columns.isEmpty()) {
			mcpFail(HttpStatus.NOT_FOUND, "DB_QUERY_REJECTED", "Không tìm thấy object: " + objectNameRaw, false, correlation);
		}

		String canonical = qn.schema() + "." + qn.table();
		String summary = String.format(Locale.ROOT,
				"Schema read-only (%d cột) cho `%s`; chỉ SELECT qua template được phép trong Agent.",
				columns.size(), canonical);
		return new SqlDescribeHttpResponse(canonical, columns, summary, correlation);
	}

	public SqlQueryReadonlyHttpResponse queryReadonly(String templateIdRaw, Map<String, Object> paramsRaw,
			String correlationId) {
		String correlation = blankToRandom(correlationId);
		Map<String, Object> params = McpSqlDtos.paramMapOrEmpty(paramsRaw);
		String templateId = templateIdRaw == null ? "" : templateIdRaw.trim();

		DbTemplateExecutor ex = executors.get(templateId);
		if (ex == null) {
			mcpFail(HttpStatus.BAD_REQUEST, "DB_QUERY_REJECTED", "Không có template_id: " + templateId, false, correlation);
			return null; // unreachable (mcpFail throws)
		}
		return ex.execute(params, correlation);
	}

	private static QualifiedName parseObjectName(String raw) {
		if (raw == null || raw.isBlank()) {
			throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "object_name trống");
		}
		String s = raw.trim();
		String schema = "public";
		String table;
		int dot = s.lastIndexOf('.');
		if (dot >= 0) {
			schema = s.substring(0, dot).trim().toLowerCase(Locale.ROOT);
			table = s.substring(dot + 1).trim().toLowerCase(Locale.ROOT);
		}
		else {
			table = s.toLowerCase(Locale.ROOT);
		}
		if (schema.isEmpty() || table.isEmpty()) {
			throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "object_name không hợp lệ");
		}
		return new QualifiedName(schema, table);
	}

	private record QualifiedName(String schema, String table) {
	}

	private static String simplifyType(String dataType) {
		if (dataType == null) {
			return "unknown";
		}
		return switch (dataType.toLowerCase(Locale.ROOT)) {
			case "character varying" -> "varchar";
			case "timestamp without time zone", "timestamp with time zone" -> "timestamp";
			case "numeric", "decimal" -> "number";
			default -> dataType;
		};
	}

	private static String blankToRandom(String correlationId) {
		if (correlationId == null || correlationId.isBlank()) {
			return UUID.randomUUID().toString();
		}
		return correlationId.trim();
	}

	private static void mcpFail(HttpStatus status, String code, String message, boolean retryable,
			String correlationId) {
		McpToolErrorResponse body =
				new McpToolErrorResponse(code, message, retryable, new LinkedHashMap<>(), correlationId);
		throw new McpToolInvocationException(status, body);
	}

	private static Map<String, DbTemplateExecutor> indexExecutors(List<DbTemplateExecutor> list) {
		Map<String, DbTemplateExecutor> map = new LinkedHashMap<>();
		for (DbTemplateExecutor ex : list) {
			String id = Optional.ofNullable(ex.templateId()).orElse("").trim();
			if (id.isEmpty()) {
				continue;
			}
			if (map.containsKey(id)) {
				throw new IllegalStateException("Duplicate template executor: " + id);
			}
			map.put(id, ex);
		}
		return map;
	}
}
