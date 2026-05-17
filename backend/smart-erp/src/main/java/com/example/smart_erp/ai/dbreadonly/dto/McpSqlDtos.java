package com.example.smart_erp.ai.dbreadonly.dto;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Wire shapes aligned with MCP {@code db-readonly} pack (Smart ERP) for Python consumer.
 */
public final class McpSqlDtos {

	private McpSqlDtos() {
	}

	@JsonInclude(JsonInclude.Include.NON_NULL)
	public record SqlDescribeHttpRequest(@JsonProperty("object_name") String objectName) {
	}

	public record SqlQueryReadonlyHttpRequest(@JsonProperty("template_id") String templateId,
			@JsonProperty("params") Map<String, Object> params) {
		public SqlQueryReadonlyHttpRequest {
			templateId = templateId == null ? "" : templateId.trim();
			if (params == null) {
				params = Map.of();
			}
		}
	}

	public record SqlQueryReadonlyRawHttpRequest(@JsonProperty("query") String query,
			@JsonProperty("max_rows") Integer maxRows) {
	}

	@JsonInclude(JsonInclude.Include.NON_NULL)
	public record ColumnMetaDto(String name, String type, boolean nullable) {
	}

	public record SqlDescribeHttpResponse(@JsonProperty("object_name") String objectName, List<ColumnMetaDto> columns,
			String summary, @JsonProperty("correlation_id") String correlationId) {
	}

	public record SqlColumnDto(String name, String type) {
	}

	public record SqlQueryReadonlyHttpResponse(List<SqlColumnDto> columns, List<List<Object>> rows,
			@JsonProperty("row_count") int row_count, String summary,
			@JsonProperty("correlation_id") String correlationId) {
	}

	public record McpToolErrorResponse(String code, String message, boolean retryable,
			@JsonProperty(value = "details", required = false) Map<String, Object> details,
			@JsonProperty("correlation_id") String correlationId) {
	}

	public static Map<String, Object> paramMapOrEmpty(Map<String, Object> raw) {
		if (raw == null || raw.isEmpty()) {
			return Map.of();
		}
		return new LinkedHashMap<>(raw);
	}

	public static List<List<Object>> rowMatrixFromMaps(List<Map<String, Object>> maps, List<String> columnOrder) {
		List<List<Object>> rows = new ArrayList<>(maps.size());
		for (Map<String, Object> m : maps) {
			List<Object> one = new ArrayList<>(columnOrder.size());
			for (String col : columnOrder) {
				one.add(m.get(col));
			}
			rows.add(one);
		}
		return rows;
	}
}
