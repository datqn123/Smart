package com.example.smart_erp.ai.dbreadonly;

import org.springframework.http.HttpStatus;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.McpToolErrorResponse;

public class McpToolInvocationException extends RuntimeException {

	private final HttpStatus status;

	private final McpToolErrorResponse errorBody;

	public McpToolInvocationException(HttpStatus status, McpToolErrorResponse errorBody) {
		super(errorBody.message());
		this.status = status;
		this.errorBody = errorBody;
	}

	public HttpStatus getStatus() {
		return status;
	}

	public McpToolErrorResponse getErrorBody() {
		return errorBody;
	}
}
