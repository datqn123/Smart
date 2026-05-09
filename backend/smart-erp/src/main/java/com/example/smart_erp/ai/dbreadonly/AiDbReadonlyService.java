package com.example.smart_erp.ai.dbreadonly;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.ColumnMetaDto;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.McpToolErrorResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlColumnDto;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlDescribeHttpResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;

/**
 * Read-only JDBC bridge implementing MCP {@code sql.describe} and {@code sql.query_readonly} semantics
 * (template-first, allowlisted objects, capped rows). Intended for the Python AI service, not public UI.
 */
@Service
public class AiDbReadonlyService {

	private static final int MAX_ROWS = 50;

	private static final Set<String> DESCRIBE_ALLOWLIST = Set.of("inventory", "products", "salesorders");

	private final JdbcTemplate jdbcTemplate;

	public AiDbReadonlyService(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
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

		return switch (templateId) {
			case "inventory_by_sku_prefix_v1" -> runInventoryBySkuPrefix(params, correlation);
			case "recent_sales_orders_v1" -> runRecentSalesOrders(params, correlation);
			default -> {
				mcpFail(HttpStatus.BAD_REQUEST, "DB_QUERY_REJECTED", "Không có template_id: " + templateId, false, correlation);
				yield null; // unreachable
			}
		};
	}

	private SqlQueryReadonlyHttpResponse runInventoryBySkuPrefix(Map<String, Object> params, String correlation) {
		String prefix = stringParam(params, "sku_prefix", "DEMO-");
		if (!prefix.endsWith("%")) {
			prefix = prefix + "%";
		}
		int lim = limitParam(params, "limit", 25);
		final String sql = """
				SELECT i.id AS inv_id, p.sku_code AS sku_code, i.quantity AS quantity,
				       i.location_id AS location_id, i.batch_number AS batch_number
				FROM inventory i
				JOIN products p ON p.id = i.product_id
				WHERE p.sku_code ILIKE ?
				ORDER BY p.sku_code, i.id
				LIMIT ?
				""";
		List<Map<String, Object>> maps =
				jdbcTemplate.queryForList(sql, prefix, lim);
		return matrixResponse(maps,
				List.of("inv_id", "sku_code", "quantity", "location_id", "batch_number"),
				"Tồn kho theo SKU (template inventory_by_sku_prefix_v1), tối đa " + lim + " dòng.", correlation);
	}

	private SqlQueryReadonlyHttpResponse runRecentSalesOrders(Map<String, Object> params, String correlation) {
		int lim = limitParam(params, "limit", 15);
		final String sql = """
				SELECT id AS id, order_code AS order_code, order_channel AS order_channel, status AS status,
				       total_amount AS total_amount, created_at AS created_at
				FROM salesorders
				ORDER BY created_at DESC
				LIMIT ?
				""";
		List<Map<String, Object>> maps = jdbcTemplate.queryForList(sql, lim);
		return matrixResponse(maps,
				List.of("id", "order_code", "order_channel", "status", "total_amount", "created_at"),
				"Đơn bán gần đây (template recent_sales_orders_v1), tối đa " + lim + " dòng.", correlation);
	}

	private SqlQueryReadonlyHttpResponse matrixResponse(List<Map<String, Object>> maps, List<String> columnKeys,
			String summary, String correlation) {
		List<SqlColumnDto> cols =
				columnKeys.stream().map(k -> new SqlColumnDto(k, guessTypeKey(k))).toList();
		List<List<Object>> rows = McpSqlDtos.rowMatrixFromMaps(maps, columnKeys);
		int rc = rows.size();
		return new SqlQueryReadonlyHttpResponse(cols, rows, rc, truncateSummary(summary), correlation);
	}

	private static String guessTypeKey(String key) {
		String k = key.toLowerCase(Locale.ROOT);
		if (k.contains("amount")) {
			return "number";
		}
		if (k.contains("quantity") || k.endsWith("_id") || "id".equals(k)) {
			return "int";
		}
		if (k.contains("at") || k.contains("date")) {
			return "timestamp";
		}
		return "varchar";
	}

	private static int limitParam(Map<String, Object> params, String key, int defaultVal) {
		Object v = params.get(key);
		if (v == null) {
			return Math.min(defaultVal, MAX_ROWS);
		}
		int n = (v instanceof Number nb) ? nb.intValue() : Integer.parseInt(v.toString().trim());
		if (n < 1) {
			return 1;
		}
		return Math.min(n, MAX_ROWS);
	}

	private static String stringParam(Map<String, Object> params, String key, String defaultVal) {
		Object v = params.get(key);
		if (v == null) {
			return defaultVal;
		}
		String s = v.toString().trim();
		return s.isEmpty() ? defaultVal : s;
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

	private static String truncateSummary(String s) {
		if (s.length() <= 2000) {
			return s;
		}
		return s.substring(0, 1997) + "...";
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
}
