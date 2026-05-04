package com.example.smart_erp.auth.session;

import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
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
	void clear_removesSessionKey() {
		registry.clear(9);
		verify(redis).delete("auth:session:9");
	}
}
