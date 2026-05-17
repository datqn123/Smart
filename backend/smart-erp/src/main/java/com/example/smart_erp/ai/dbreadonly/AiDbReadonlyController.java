package com.example.smart_erp.ai.dbreadonly;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.McpToolErrorResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlDescribeHttpRequest;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlDescribeHttpResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpRequest;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyRawHttpRequest;

/**
 * HTTP façade for MCP {@code db-readonly} tools consumed by {@code ai_python}. Paths are POST (JSON bodies)
 * so agents do not cram parameters into URLs.
 *
 * <p>
 * Dev note: endpoints are intentionally open when {@code jwt-api} is off; with {@code jwt-api}, they remain
 * {@code permitAll} so Python can reach DB without JWT (EventSource cannot attach headers). Prefer network ACL
 * / private binding in production.</p>
 */
@RestController
@RequestMapping(path = "/api/v1/ai/db", produces = MediaType.APPLICATION_JSON_VALUE)
public class AiDbReadonlyController {

	private final AiDbReadonlyService service;
	private final AiDbReadonlyRawSqlService rawSqlService;

	public AiDbReadonlyController(AiDbReadonlyService service, AiDbReadonlyRawSqlService rawSqlService) {
		this.service = service;
		this.rawSqlService = rawSqlService;
	}

	@PostMapping(path = "/sql/describe", consumes = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<?> sqlDescribe(@RequestBody SqlDescribeHttpRequest req,
			@RequestHeader(value = "X-Correlation-Id", required = false) String correlationId) {
		try {
			SqlDescribeHttpResponse body = service.describe(req.objectName(), correlationId);
			return ResponseEntity.ok(body);
		}
		catch (McpToolInvocationException ex) {
			return ResponseEntity.status(ex.getStatus()).body(ex.getErrorBody());
		}
		catch (ResponseStatusException ex) {
			return toolError(HttpStatus.BAD_REQUEST, "BAD_REQUEST",
					ex.getReason() != null ? ex.getReason() : ex.getStatusCode().toString(), correlationId);
		}
	}

	@PostMapping(path = "/sql/query-readonly", consumes = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<?> sqlQueryReadonly(@RequestBody SqlQueryReadonlyHttpRequest req,
			@RequestHeader(value = "X-Correlation-Id", required = false) String correlationId) {
		try {
			SqlQueryReadonlyHttpResponse body =
					service.queryReadonly(req.templateId(), req.params(), correlationId);
			return ResponseEntity.ok(body);
		}
		catch (McpToolInvocationException ex) {
			return ResponseEntity.status(ex.getStatus()).body(ex.getErrorBody());
		}
		catch (ResponseStatusException ex) {
			return toolError(HttpStatus.BAD_REQUEST, "BAD_REQUEST",
					ex.getReason() != null ? ex.getReason() : ex.getStatusCode().toString(), correlationId);
		}
	}

	@PostMapping(path = "/sql/query-readonly-raw", consumes = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<?> sqlQueryReadonlyRaw(@RequestBody SqlQueryReadonlyRawHttpRequest req,
			@RequestHeader(value = "X-Correlation-Id", required = false) String correlationId) {
		try {
			SqlQueryReadonlyHttpResponse body = rawSqlService.queryRaw(req.query(), req.maxRows(), correlationId);
			return ResponseEntity.ok(body);
		}
		catch (McpToolInvocationException ex) {
			return ResponseEntity.status(ex.getStatus()).body(ex.getErrorBody());
		}
	}

	private static ResponseEntity<McpToolErrorResponse> toolError(HttpStatus status, String code, String message,
			String correlationId) {
		String cid = (correlationId == null || correlationId.isBlank()) ? java.util.UUID.randomUUID().toString()
				: correlationId.trim();
		return ResponseEntity.status(status).body(new McpToolErrorResponse(code, message, false, java.util.Map.of(), cid));
	}
}
