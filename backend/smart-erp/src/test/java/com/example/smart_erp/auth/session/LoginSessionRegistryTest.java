package com.example.smart_erp.auth.session;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.Duration;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import com.example.smart_erp.auth.support.JwtTokenService;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@ExtendWith(MockitoExtension.class)
class LoginSessionRegistryTest {

	@Mock
	private JwtTokenService jwtTokenService;

	@Mock
	private StringRedisTemplate redis;

	@Mock
	private ValueOperations<String, String> values;

	private LoginSessionRegistry registry;

	@BeforeEach
	void setUp() {
		lenient().when(redis.opsForValue()).thenReturn(values);
		lenient().when(jwtTokenService.getAccessTtlSeconds()).thenReturn(120L);
		registry = new LoginSessionRegistry(jwtTokenService, redis);
	}

	@Test
	void register_overwritesSessionKeyWithConfiguredTtl() {
		registry.register(5, "access.jwt.here");
		verify(values).set(eq("auth:session:5"), eq("access.jwt.here"), eq(Duration.ofSeconds(120L)));
	}

	@Test
	void register_usesMinimumSixtySecondTtlWhenJwtTtlVeryLow() {
		when(jwtTokenService.getAccessTtlSeconds()).thenReturn(30L);
		registry.register(1, "t");
		verify(values).set(eq("auth:session:1"), eq("t"), eq(Duration.ofSeconds(60L)));
	}

	@Test
	void register_storesClientSessionIdWhenProvided() {
		registry.register(2, "access.jwt.here", "client-A");
		verify(values).set(eq("auth:session:2"),
				eq("{\"accessToken\":\"access.jwt.here\",\"clientSessionId\":\"client-A\"}"),
				eq(Duration.ofSeconds(120L)));
	}

	@Test
	void clear_removesSessionKey() {
		registry.clear(9);
		verify(redis).delete("auth:session:9");
	}

	@Test
	void assertNoConcurrentSession_allowsWhenNoExistingToken() {
		when(values.get("auth:session:5")).thenReturn(null);

		registry.assertNoConcurrentSession(5);

		verify(redis, never()).execute(any(), any(), any());
	}

	@Test
	void assertNoConcurrentSession_deletesWhenExistingTokenIsStale() {
		when(values.get("auth:session:5")).thenReturn("{\"accessToken\":\"expired.jwt\",\"clientSessionId\":\"client-A\"}");
		when(jwtTokenService.isAccessTokenActiveForSessionMap("expired.jwt")).thenReturn(false);

		registry.assertNoConcurrentSession(5, "client-A");

		verify(redis).execute(any(), eq(java.util.List.of("auth:session:5")),
				eq("{\"accessToken\":\"expired.jwt\",\"clientSessionId\":\"client-A\"}"));
	}

	@Test
	void assertNoConcurrentSession_throwsForbiddenWhenExistingTokenIsActive() {
		when(values.get("auth:session:5")).thenReturn("active.jwt");
		when(jwtTokenService.isAccessTokenActiveForSessionMap("active.jwt")).thenReturn(true);

		org.assertj.core.api.Assertions.assertThatThrownBy(() -> registry.assertNoConcurrentSession(5))
				.isInstanceOfSatisfying(BusinessException.class,
						ex -> org.assertj.core.api.Assertions.assertThat(ex.getCode()).isEqualTo(ApiErrorCode.FORBIDDEN));
	}

	@Test
	void assertNoConcurrentSession_allowsWhenActiveTokenSameClientSessionId() {
		when(values.get("auth:session:5")).thenReturn("{\"accessToken\":\"active.jwt\",\"clientSessionId\":\"client-A\"}");
		when(jwtTokenService.isAccessTokenActiveForSessionMap("active.jwt")).thenReturn(true);

		registry.assertNoConcurrentSession(5, "client-A");

		verify(redis, never()).execute(any(), any(), any());
	}

	@Test
	void assertNoConcurrentSession_throwsForbiddenWhenActiveTokenDifferentClientSessionId() {
		when(values.get("auth:session:5")).thenReturn("{\"accessToken\":\"active.jwt\",\"clientSessionId\":\"client-A\"}");
		when(jwtTokenService.isAccessTokenActiveForSessionMap("active.jwt")).thenReturn(true);

		org.assertj.core.api.Assertions.assertThatThrownBy(() -> registry.assertNoConcurrentSession(5, "client-B"))
				.isInstanceOfSatisfying(BusinessException.class,
						ex -> org.assertj.core.api.Assertions.assertThat(ex.getCode()).isEqualTo(ApiErrorCode.FORBIDDEN));
	}
}
