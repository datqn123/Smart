package com.example.smart_erp.auth.session;

import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Component;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

/**
 * Task003 / SRS §7.2: tối đa một access mới qua {@code /auth/refresh} mỗi {@value MIN_GAP_MINUTES} phút / user (in-memory),
 * giảm tải server và hạn chế thử refresh token hàng loạt. Nên giữ khoảng cách này ≥ chu kỳ làm mới access hợp lệ
 * (TTL access JWT mặc định cùng thứ tự phút) để người dùng hợp lệ vẫn refresh được sau khi JWT hết hạn.
 * Được xóa khi {@link com.example.smart_erp.auth.service.AuthService#login(String, String)} thành công hoặc sau {@code logout}.
 */
@Component
public class RefreshAccessThrottle {

	static final int MIN_GAP_MINUTES = 5;

	private static final Duration MIN_GAP = Duration.ofMinutes(MIN_GAP_MINUTES);

	private static final String TOO_SOON = "Vui lòng đợi %d phút trước khi làm mới access token."
			.formatted(MIN_GAP_MINUTES);

	private final ConcurrentHashMap<Integer, Instant> lastIssuedAt = new ConcurrentHashMap<>();

	public void assertCanIssueNewAccess(int userId) {
		Instant now = Instant.now();
		Instant prev = lastIssuedAt.get(userId);
		if (prev != null && Duration.between(prev, now).compareTo(MIN_GAP) < 0) {
			throw new BusinessException(ApiErrorCode.TOO_MANY_REQUESTS, TOO_SOON);
		}
	}

	public void recordIssued(int userId) {
		lastIssuedAt.put(userId, Instant.now());
	}

	public void clear(int userId) {
		lastIssuedAt.remove(userId);
	}
}
