package com.example.smart_erp.ai.dbreadonly.templates;

import java.util.List;
import java.util.Map;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;

@Component
public class RecentSalesOrdersExecutor implements DbTemplateExecutor {

	private final JdbcTemplate jdbcTemplate;

	public RecentSalesOrdersExecutor(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
	}

	@Override
	public String templateId() {
		return "recent_sales_orders_v1";
	}

	@Override
	public SqlQueryReadonlyHttpResponse execute(Map<String, Object> params, String correlationId) {
		int lim = limitParam(params, "limit", 15);
		final String sql = """
				SELECT id AS id, order_code AS order_code, order_channel AS order_channel, status AS status,
				       total_amount AS total_amount, created_at AS created_at
				FROM salesorders
				ORDER BY created_at DESC
				LIMIT ?
				""";
		List<Map<String, Object>> maps = jdbcTemplate.queryForList(sql, lim);
		return DbTemplateUtils.matrixResponse(maps,
				List.of("id", "order_code", "order_channel", "status", "total_amount", "created_at"),
				"Đơn bán gần đây (template recent_sales_orders_v1), tối đa " + lim + " dòng.", correlationId);
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
}

