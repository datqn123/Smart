package com.example.smart_erp.ai.dbreadonly.templates;

import java.util.List;
import java.util.Locale;
import java.util.Map;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlColumnDto;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;

public final class DbTemplateUtils {

	static final int MAX_ROWS = 50;

	private DbTemplateUtils() {
	}

	public static SqlQueryReadonlyHttpResponse matrixResponse(List<Map<String, Object>> maps, List<String> columnKeys,
			String summary, String correlationId) {
		List<SqlColumnDto> cols = columnKeys.stream().map(k -> new SqlColumnDto(k, guessTypeKey(k))).toList();
		List<List<Object>> rows = McpSqlDtos.rowMatrixFromMaps(maps, columnKeys);
		int rc = rows.size();
		return new SqlQueryReadonlyHttpResponse(cols, rows, rc, truncateSummary(summary), correlationId);
	}

	private static String guessTypeKey(String key) {
		String k = key.toLowerCase(Locale.ROOT);
		if (k.contains("amount")) {
			return "number";
		}
		if (k.contains("quantity") || k.endsWith("_id") || "id".equals(k) || k.startsWith("count")
				|| k.contains("products")) {
			return "int";
		}
		if (k.contains("at") || k.contains("date")) {
			return "timestamp";
		}
		return "varchar";
	}

	private static String truncateSummary(String s) {
		if (s == null) {
			return "";
		}
		if (s.length() <= 2000) {
			return s;
		}
		return s.substring(0, 1997) + "...";
	}
}

