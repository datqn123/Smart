package com.example.smart_erp.auth.session;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import com.example.smart_erp.auth.repository.UserRepository;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

/**
 * Sau {@value #MAX_FAILURES} lần mật khẩu sai liên tiếp cho cùng một user Active → {@code status = Locked}.
 */
@Component
public class LoginBruteForceProtection {

	static final int MAX_FAILURES = 5;

	private final Cache<Integer, AtomicInteger> failuresByUserId = Caffeine.newBuilder()
			.expireAfterWrite(30, TimeUnit.MINUTES)
			.build();

	public void onSuccess(Integer userId) {
		failuresByUserId.invalidate(userId);
	}

	@Transactional(propagation = Propagation.REQUIRES_NEW)
	public void onFailure(Integer userId, UserRepository userRepository) {
		AtomicInteger counter = failuresByUserId.get(userId, k -> new AtomicInteger(0));
		int n = counter.incrementAndGet();
		if (n >= MAX_FAILURES) {
			userRepository.lockActiveUserById(userId);
			failuresByUserId.invalidate(userId);
		}
	}
}
