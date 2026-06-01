package com.example.smart_erp.auth.session;

import java.time.Duration;
import java.util.List;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.example.smart_erp.auth.support.JwtTokenService;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Phiên đăng nhập tại thời điểm (Task001): lưu trong Redis để dùng chung giữa nhiều instance.
 * <p>
 * {@link #register} luôn ghi đè theo userId — đăng nhập lại sau khi client mất {@code sessionStorage}
 * (tab đóng, chưa logout) vẫn được vì chỉ cập nhật Redis <strong>sau</strong> khi mật khẩu đúng.
 */
@Component
@SuppressWarnings("null")
public class LoginSessionRegistry {

	private static final String KEY_PREFIX = "auth:session:";
	private static final String FORBIDDEN_CONCURRENT_SESSION =
			"Tài khoản đang được đăng nhập ở một thiết bị khác. Vui lòng đăng xuất ở thiết bị đó hoặc liên hệ Admin.";
	private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
	private static final DefaultRedisScript<Long> COMPARE_AND_DELETE_SCRIPT = new DefaultRedisScript<>(
			"if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
			Long.class);

	private final JwtTokenService jwtTokenService;
	private final StringRedisTemplate redis;

	public LoginSessionRegistry(JwtTokenService jwtTokenService, StringRedisTemplate redis) {
		this.jwtTokenService = jwtTokenService;
		this.redis = redis;
	}

	public void register(Integer userId, String accessToken) {
		register(userId, accessToken, null);
	}

	public void register(Integer userId, String accessToken, String clientSessionId) {
		long ttlSeconds = Math.max(60L, jwtTokenService.getAccessTtlSeconds());
		String value = encodeRegistryValue(accessToken, clientSessionId);
		redis.opsForValue().set(key(userId), value, Duration.ofSeconds(ttlSeconds));
	}

	/**
	 * Task001/Task100: chỉ chặn đăng nhập mới nếu session hiện tại còn active.
	 */
	public void assertNoConcurrentSession(Integer userId) {
		assertNoConcurrentSession(userId, null);
	}

	public void assertNoConcurrentSession(Integer userId, String clientSessionId) {
		String existing = redis.opsForValue().get(key(userId));
		if (!StringUtils.hasText(existing)) {
			return;
		}
		SessionEntry entry = decodeRegistryValue(existing);
		if (!jwtTokenService.isAccessTokenActiveForSessionMap(entry.accessToken())) {
			compareAndDeleteIfUnchanged(key(userId), existing);
			return;
		}
		if (isSameClient(entry.clientSessionId(), clientSessionId)) {
			return;
		}
		throw new BusinessException(ApiErrorCode.FORBIDDEN, FORBIDDEN_CONCURRENT_SESSION);
	}

	/** Dùng cho test / logout (Task002). */
	public void clear(Integer userId) {
		redis.delete(key(userId));
	}

	private static String key(Integer userId) {
		return KEY_PREFIX + userId;
	}

	private static String encodeRegistryValue(String accessToken, String clientSessionId) {
		String tokenNorm = accessToken == null ? "" : accessToken.strip();
		String clientNorm = normalizeClientSessionId(clientSessionId);
		if (!StringUtils.hasText(clientNorm)) {
			return tokenNorm;
		}
		try {
			return OBJECT_MAPPER.writeValueAsString(new SessionEntry(tokenNorm, clientNorm));
		}
		catch (JsonProcessingException ex) {
			return tokenNorm;
		}
	}

	private static SessionEntry decodeRegistryValue(String raw) {
		if (!StringUtils.hasText(raw)) {
			return new SessionEntry("", null);
		}
		String value = raw.strip();
		if (!value.startsWith("{")) {
			return new SessionEntry(value, null);
		}
		try {
			JsonNode node = OBJECT_MAPPER.readTree(value);
			String token = node.path("accessToken").asText("");
			if (!StringUtils.hasText(token)) {
				return new SessionEntry(value, null);
			}
			String client = node.path("clientSessionId").asText(null);
			return new SessionEntry(token, normalizeClientSessionId(client));
		}
		catch (Exception ex) {
			return new SessionEntry(value, null);
		}
	}

	private static boolean isSameClient(String storedClientSessionId, String incomingClientSessionId) {
		String stored = normalizeClientSessionId(storedClientSessionId);
		String incoming = normalizeClientSessionId(incomingClientSessionId);
		return StringUtils.hasText(stored) && stored.equals(incoming);
	}

	private static String normalizeClientSessionId(String value) {
		if (!StringUtils.hasText(value)) {
			return null;
		}
		return value.strip();
	}

	private void compareAndDeleteIfUnchanged(String redisKey, String expectedToken) {
		redis.execute(COMPARE_AND_DELETE_SCRIPT, List.of(redisKey), expectedToken);
	}

	private record SessionEntry(String accessToken, String clientSessionId) {
	}
}
