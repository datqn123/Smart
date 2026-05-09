package com.example.smart_erp.ai.dbreadonly.templates;

import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;

@Component
public class InventoryActiveProductsCountExecutor implements DbTemplateExecutor {

	private final JdbcTemplate jdbcTemplate;

	public InventoryActiveProductsCountExecutor(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
	}

	@Override
	public String templateId() {
		return "inventory_active_products_count_v1";
	}

	@Override
	public SqlQueryReadonlyHttpResponse execute(Map<String, Object> params, String correlationId) {
		int minQty = minQuantity(params);
		final String sql = """
				SELECT COUNT(DISTINCT p.id) AS active_products_with_inventory
				FROM inventory i
				JOIN products p ON p.id = i.product_id
				WHERE p.status = 'Active' AND i.quantity >= ?
				""";
		List<Map<String, Object>> maps = jdbcTemplate.queryForList(sql, minQty);
		return DbTemplateUtils.matrixResponse(
				maps,
				List.of("active_products_with_inventory"),
				"Đếm số sản phẩm Active có tồn kho (template inventory_active_products_count_v1).",
				correlationId);
	}

	private static int minQuantity(Map<String, Object> params) {
		Object v = params.get("min_quantity");
		if (v == null) {
			return 0;
		}
		int n = (v instanceof Number nb) ? nb.intValue() : Integer.parseInt(v.toString().trim());
		return Math.max(0, n);
	}
}

