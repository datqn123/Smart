package com.example.smart_erp.auth.session;

import java.time.Duration;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import com.example.smart_erp.auth.support.JwtTokenService;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

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
	private static final String FORBIDDEN_CONCURRENT_SESSION = "Tài khoản đang được đăng nhập trên thiết bị khác";

	private final JwtTokenService jwtTokenService;
	private final StringRedisTemplate redis;

	public LoginSessionRegistry(JwtTokenService jwtTokenService, StringRedisTemplate redis) {
		this.jwtTokenService = jwtTokenService;
		this.redis = redis;
	}

	public void register(Integer userId, String accessToken) {
		long ttlSeconds = Math.max(60L, jwtTokenService.getAccessTtlSeconds());
		redis.opsForValue().set(key(userId), accessToken, Duration.ofSeconds(ttlSeconds));
	}

	/**
	 * Task001/Task100: chỉ chặn đăng nhập mới nếu session hiện tại còn active.
	 */
	public void assertNoConcurrentSession(Integer userId) {
		String existing = redis.opsForValue().get(key(userId));
		if (!StringUtils.hasText(existing)) {
			return;
		}
		if (!jwtTokenService.isAccessTokenActiveForSessionMap(existing)) {
			redis.delete(key(userId));
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
}
