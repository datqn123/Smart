package com.example.smart_erp.settings.systemlogs;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.settings.systemlogs.response.SystemLogDetailData;
import com.example.smart_erp.settings.systemlogs.response.SystemLogItemData;
import com.example.smart_erp.settings.systemlogs.response.SystemLogsListData;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
@SuppressWarnings("null")
public class SystemLogsService {

	private static final String MP_KEY_CAN_VIEW_SYSTEM_LOGS = "can_view_system_logs";

	/** JWT claim {@code role} — chỉ Admin được xem system logs (SRS_PRD_system-audit-unified-admin-view). */
	private static final String JWT_CLAIM_ROLE = "role";

	private static final String ROLE_ADMIN = "Admin";

	private static final int DEFAULT_PAGE = 1;
	private static final int DEFAULT_LIMIT = 20;
	private static final int MAX_LIMIT = 100;

	private static final int MAX_SEARCH_LEN = 200;
	private static final int MAX_MODULE_LEN = 100;

	private static final List<String> ALLOWED_LOG_LEVELS = List.of("INFO", "WARNING", "ERROR", "CRITICAL");

	private static final String MSG_FORBIDDEN_VIEW = "Bạn không có quyền xem nhật ký hệ thống.";
	private static final String MSG_FORBIDDEN_DELETE_POLICY = "Không được phép xóa nhật ký hệ thống theo chính sách hệ thống.";

	private static final ObjectMapper FALLBACK_MAPPER = new ObjectMapper();

	private final SystemLogsJdbcRepository repo;
	private final ObjectMapper objectMapper;

	public SystemLogsService(SystemLogsJdbcRepository repo, ObjectMapper objectMapper) {
		this.repo = repo;
		this.objectMapper = objectMapper;
	}

	@Transactional(readOnly = true)
	public SystemLogsListData list(String search, String module, String logLevel, String dateFromRaw, String dateToRaw, Integer page,
			Integer limit, org.springframework.security.oauth2.jwt.Jwt jwt) {
		requireCanView(jwt);

		int p = page != null ? page.intValue() : DEFAULT_PAGE;
		int l = limit != null ? limit.intValue() : DEFAULT_LIMIT;
		if (p < 1) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ", Map.of("page", "page phải >= 1"));
		}
		if (l < 1 || l > MAX_LIMIT) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of("limit", "Giới hạn mỗi trang phải từ 1 đến " + MAX_LIMIT));
		}

		String searchPattern = buildSearchPattern(search);
		String normalizedModule = normalizeNullableTrimmed(module, MAX_MODULE_LEN, "module");
		String normalizedLogLevel = normalizeNullableEnum(logLevel, "logLevel");

		Instant dateFrom = parseNullableDateOrDateTime(dateFromRaw, "dateFrom", true);
		Instant dateTo = parseNullableDateOrDateTime(dateToRaw, "dateTo", false);
		if (dateFrom != null && dateTo != null && dateTo.isBefore(dateFrom)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of("dateTo", "dateTo phải >= dateFrom"));
		}

		long total = repo.countRows(searchPattern, normalizedModule, normalizedLogLevel, dateFrom, dateTo);
		var rows = repo.loadPage(searchPattern, normalizedModule, normalizedLogLevel, dateFrom, dateTo, p, l);
		var items = rows.stream().map(SystemLogsService::toItem).toList();
		return new SystemLogsListData(items, p, l, total);
	}

	@Transactional(readOnly = true)
	public SystemLogDetailData getDetail(long id, org.springframework.security.oauth2.jwt.Jwt jwt) {
		requireCanView(jwt);
		if (id <= 0) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số yêu cầu không hợp lệ",
					Map.of("id", "Giá trị phải là số nguyên dương"));
		}

		var row = repo.findById(id).orElseThrow(() -> new BusinessException(ApiErrorCode.NOT_FOUND, "Không tìm thấy nhật ký hệ thống."));
		JsonNode context = decodeNullableJson(row.contextDataJson(), "contextData");
		return new SystemLogDetailData(
				row.id(),
				toIsoUtc(row.createdAt()),
				normalizeUser(row.fullName()),
				Objects.requireNonNullElse(row.action(), ""),
				Objects.requireNonNullElse(row.module(), ""),
				Objects.requireNonNullElse(row.message(), ""),
				toSeverityPascal(row.logLevel()),
				extractClientIp(context),
				row.stackTrace(),
				context);
	}

	public void deleteById(long id, org.springframework.security.oauth2.jwt.Jwt jwt) {
		requireCanView(jwt);
		throw new BusinessException(ApiErrorCode.FORBIDDEN, MSG_FORBIDDEN_DELETE_POLICY);
	}

	public void bulkDelete(List<Long> ids, org.springframework.security.oauth2.jwt.Jwt jwt) {
		requireCanView(jwt);
		throw new BusinessException(ApiErrorCode.FORBIDDEN, MSG_FORBIDDEN_DELETE_POLICY);
	}

	private void requireCanView(org.springframework.security.oauth2.jwt.Jwt jwt) {
		if (jwt == null) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, "Phiên đăng nhập không hợp lệ");
		}
		String role = jwt.getClaimAsString(JWT_CLAIM_ROLE);
		if (!ROLE_ADMIN.equals(role)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, MSG_FORBIDDEN_VIEW);
		}
		Object mp = jwt.getClaim("mp");
		if (!(mp instanceof Map<?, ?> map)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, MSG_FORBIDDEN_VIEW);
		}
		Object v = map.get(MP_KEY_CAN_VIEW_SYSTEM_LOGS);
		if (!Boolean.TRUE.equals(v)) {
			throw new BusinessException(ApiErrorCode.FORBIDDEN, MSG_FORBIDDEN_VIEW);
		}
	}

	private static SystemLogItemData toItem(SystemLogsJdbcRepository.SystemLogRow r) {
		JsonNode context = decodeNullableJsonStatic(r.contextDataJson());
		return new SystemLogItemData(
				r.id(),
				toIsoUtc(r.createdAt()),
				normalizeUser(r.fullName()),
				Objects.requireNonNullElse(r.action(), ""),
				Objects.requireNonNullElse(r.module(), ""),
				Objects.requireNonNullElse(r.message(), ""),
				toSeverityPascal(r.logLevel()),
				extractClientIp(context));
	}

	private JsonNode decodeNullableJson(String json, String field) {
		if (!StringUtils.hasText(json)) {
			return null;
		}
		try {
			return objectMapper.readTree(json);
		}
		catch (Exception e) {
			throw new BusinessException(ApiErrorCode.INTERNAL_SERVER_ERROR, "Không đọc được dữ liệu nhật ký",
					Map.of(field, "Không hợp lệ"));
		}
	}

	private static JsonNode decodeNullableJsonStatic(String json) {
		if (!StringUtils.hasText(json)) {
			return null;
		}
		try {
			return FALLBACK_MAPPER.readTree(json);
		}
		catch (Exception e) {
			return null;
		}
	}

	private static String extractClientIp(JsonNode context) {
		if (context == null || !context.isObject()) {
			return null;
		}
		JsonNode ip = context.get("clientIp");
		if (ip != null && ip.isTextual()) {
			String t = ip.asText().trim();
			return t.isEmpty() ? null : t;
		}
		return null;
	}

	private static String toIsoUtc(Instant t) {
		Instant ts = t != null ? t : Instant.parse("1970-01-01T00:00:00Z");
		return ts.toString();
	}

	private static String normalizeUser(String fullName) {
		return StringUtils.hasText(fullName) ? fullName : "System";
	}

	private static String toSeverityPascal(String raw) {
		String t = raw != null ? raw.trim().toUpperCase() : "";
		if (t.isEmpty()) {
			return "Info";
		}
		return switch (t) {
			case "INFO" -> "Info";
			case "WARNING" -> "Warning";
			case "ERROR" -> "Error";
			case "CRITICAL" -> "Critical";
			default -> "Info";
		};
	}

	private static String normalizeNullableTrimmed(String raw, int maxLen, String field) {
		if (raw == null) {
			return null;
		}
		String t = raw.trim();
		if (t.isEmpty()) {
			return null;
		}
		if (t.length() > maxLen) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of(field, "Tối đa " + maxLen + " ký tự"));
		}
		return t;
	}

	private static String normalizeNullableEnum(String raw, String field) {
		if (raw == null) {
			return null;
		}
		String t = raw.trim();
		if (t.isEmpty()) {
			return null;
		}
		t = t.toUpperCase();
		if (!ALLOWED_LOG_LEVELS.contains(t)) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of(field, "Giá trị không hợp lệ"));
		}
		return t;
	}

	public static String buildSearchPattern(String raw) {
		if (raw == null) {
			return null;
		}
		String t = raw.trim();
		if (t.isEmpty()) {
			return "%";
		}
		if (t.length() > MAX_SEARCH_LEN) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of("search", "Tối đa " + MAX_SEARCH_LEN + " ký tự"));
		}
		t = t.replace("%", "").replace("_", "");
		if (t.isEmpty()) {
			return "%";
		}
		return "%" + t + "%";
	}

	private static Instant parseNullableDateOrDateTime(String raw, String field, boolean isStartOfDay) {
		if (!StringUtils.hasText(raw)) {
			return null;
		}
		String t = raw.trim();
		try {
			if (t.contains("T")) {
				return Instant.parse(t);
			}
			LocalDate d = LocalDate.parse(t);
			if (isStartOfDay) {
				return d.atStartOfDay().toInstant(ZoneOffset.UTC);
			}
			return d.plusDays(1).atStartOfDay().toInstant(ZoneOffset.UTC).minusMillis(1);
		}
		catch (Exception e) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Dữ liệu không hợp lệ",
					Map.of(field, "Không hợp lệ"));
		}
	}
}

