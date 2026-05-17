package com.example.smart_erp.ai.dbreadonly.templates;

import java.util.Map;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;

public interface DbTemplateExecutor {

	String templateId();

	SqlQueryReadonlyHttpResponse execute(Map<String, Object> params, String correlationId);
}

