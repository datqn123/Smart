package com.example.smart_erp.ai.dbreadonly;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.StatementCallback;
import org.springframework.stereotype.Service;

import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.McpToolErrorResponse;
import com.example.smart_erp.ai.dbreadonly.dto.McpSqlDtos.SqlQueryReadonlyHttpResponse;
import com.example.smart_erp.ai.dbreadonly.templates.DbTemplateUtils;

import net.sf.jsqlparser.parser.CCJSqlParserUtil;
import net.sf.jsqlparser.schema.Table;
import net.sf.jsqlparser.statement.Statement;
import net.sf.jsqlparser.statement.select.Select;
import net.sf.jsqlparser.util.TablesNamesFinder;

@Service
public class AiDbReadonlyRawSqlService {

	private static final int DEFAULT_MAX_ROWS = 50;

	// Phase 1: allow only public schema; later can evolve to `reporting.*` views.
	private static final Set<String> ALLOWED_SCHEMAS = Set.of("public");

	private final JdbcTemplate jdbcTemplate;

	public AiDbReadonlyRawSqlService(JdbcTemplate jdbcTemplate) {
		this.jdbcTemplate = jdbcTemplate;
	}

	public SqlQueryReadonlyHttpResponse queryRaw(String queryRaw, Integer maxRows, String correlationId) {
		String cid = correlationId == null || correlationId.isBlank() ? UUID.randomUUID().toString() : correlationId.trim();
		String q = normalize(queryRaw);
		int lim = clamp(maxRows, 1, DEFAULT_MAX_ROWS);

		guardParseAndValidate(q, cid);
		String limited = ensureLimit(q, lim);

		try {
			// Apply a hard statement timeout as defense-in-depth (Postgres).
			jdbcTemplate.execute((StatementCallback<Void>) stmt -> {
				stmt.setQueryTimeout((int) Duration.ofSeconds(5).toSeconds());
				return null;
			});

			List<Map<String, Object>> rows = jdbcTemplate.queryForList(limited);
			List<String> cols = rows.isEmpty() ? List.of() : new ArrayList<>(rows.get(0).keySet());
			return DbTemplateUtils.matrixResponse(rows, cols, "Raw SQL read-only (guarded, LIMIT=" + lim + ").", cid);
		}
		catch (Exception e) {
			throw new McpToolInvocationException(HttpStatus.BAD_REQUEST,
					new McpToolErrorResponse("DB_UPSTREAM_ERROR",
							"Raw query failed: " + safeMsg(e.getMessage()),
							false,
							Map.of(),
							cid));
		}
	}

	/** SELECT and WITH ... SELECT (CTE) for chart calendar spine queries. */
	private static boolean isReadOnlySelect(Statement st, String q) {
		if (st instanceof Select) {
			return true;
		}
		String normalized = q.strip().replaceAll("\\s+", " ").toUpperCase(Locale.ROOT);
		return normalized.startsWith("WITH ") && normalized.contains(" SELECT ");
	}

	private static void guardParseAndValidate(String q, String cid) {
		if (q.isEmpty()) {
			throw reject("DB_QUERY_REJECTED", "Query must not be blank", cid);
		}
		if (q.contains(";")) {
			throw reject("DB_QUERY_REJECTED", "Only single statement is allowed (no ';')", cid);
		}
		String low = q.toLowerCase(Locale.ROOT);
		for (String bad : List.of("insert ", "update ", "delete ", "merge ", "drop ", "alter ", "create ", "grant ", "revoke ",
				"copy ", "call ", "do ", "truncate ")) {
			if (low.contains(bad)) {
				throw reject("DB_QUERY_REJECTED", "Disallowed keyword: " + bad.trim(), cid);
			}
		}
		try {
			Statement st = CCJSqlParserUtil.parse(q);
			if (!isReadOnlySelect(st, q)) {
				throw reject("DB_QUERY_REJECTED", "Only SELECT statements are allowed", cid);
			}
			// Disallow explicit non-public schema qualifiers on Table AST nodes only.
			// Do not scan raw text for "a.b" — that misclassifies table.column and aliases (e.g. p.name).
			if (st instanceof Select select) {
				validateExplicitSchemas(select, cid);
			}
		}
		catch (McpToolInvocationException ex) {
			throw ex;
		}
		catch (Exception e) {
			throw reject("DB_QUERY_REJECTED", "SQL parse failed", cid);
		}
	}

	private static void validateExplicitSchemas(Select select, String correlationId) {
		TablesNamesFinder<Void> finder = new TablesNamesFinder<>() {
			@Override
			public void visit(Table tableName) {
				assertAllowedTableSchema(tableName, correlationId);
				super.visit(tableName);
			}

			@Override
			public <S> Void visit(Table tableName, S context) {
				assertAllowedTableSchema(tableName, correlationId);
				return super.visit(tableName, context);
			}
		};
		finder.getTables((Statement) select);
	}

	private static void assertAllowedTableSchema(Table tableName, String correlationId) {
		String schema = tableName.getSchemaName();
		if (schema == null || schema.isBlank()) {
			return;
		}
		String s = schema.toLowerCase(Locale.ROOT);
		if (!ALLOWED_SCHEMAS.contains(s)) {
			throw reject("DB_QUERY_REJECTED", "Schema not allowed: " + schema, correlationId);
		}
	}

	private static String ensureLimit(String q, int lim) {
		String low = q.toLowerCase(Locale.ROOT);
		if (low.contains(" limit ")) {
			return q;
		}
		return q + " LIMIT " + lim;
	}

	private static String normalize(String raw) {
		return raw == null ? "" : raw.trim().replaceAll("\\s+", " ");
	}

	private static int clamp(Integer v, int min, int max) {
		if (v == null) {
			return max;
		}
		return Math.min(max, Math.max(min, v.intValue()));
	}

	private static McpToolInvocationException reject(String code, String msg, String cid) {
		return new McpToolInvocationException(HttpStatus.BAD_REQUEST,
				new McpToolErrorResponse(code, msg, false, Map.of(), cid));
	}

	private static String safeMsg(String s) {
		if (s == null) {
			return "error";
		}
		return s.length() > 300 ? s.substring(0, 300) : s;
	}
}

