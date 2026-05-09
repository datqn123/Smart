package com.example.smart_erp.ai.dbreadonly.templates;

import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;

@Component
public class InventoryBySkuPrefixExecutor implements DbTemplateExecutor {

	private final JdbcTemplate jdbcTemplate;

	public InventoryBySkuPrefixExecutor(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
	}

	@Override
	public String templateId() {
		return "inventory_by_sku_prefix_v1";
	}

	@Override
	public SqlQueryReadonlyHttpResponse execute(Map<String, Object> params, String correlationId) {
		String prefix = stringParam(params, "sku_prefix", "").trim();
		if (prefix.isEmpty()) {
			prefix = "%";
		}
		else if (!prefix.endsWith("%")) {
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
		List<Map<String, Object>> maps = jdbcTemplate.queryForList(sql, prefix, lim);
		return DbTemplateUtils.matrixResponse(maps,
				List.of("inv_id", "sku_code", "quantity", "location_id", "batch_number"),
				"Tồn kho theo SKU (template inventory_by_sku_prefix_v1), tối đa " + lim + " dòng.", correlationId);
	}

	private static int limitParam(Map<String, Object> params, String key, int defaultVal) {
		Object v = params.get(key);
		if (v == null) {
			return Math.min(defaultVal, DbTemplateUtils.MAX_ROWS);
		}
		int n = (v instanceof Number nb) ? nb.intValue() : Integer.parseInt(v.toString().trim());
		if (n < 1) {
			return 1;
		}
		return Math.min(n, DbTemplateUtils.MAX_ROWS);
	}

	private static String stringParam(Map<String, Object> params, String key, String defaultVal) {
		Object v = params.get(key);
		if (v == null) {
			return defaultVal;
		}
		String s = v.toString().trim();
		return s.isEmpty() ? defaultVal : s;
	}
}

