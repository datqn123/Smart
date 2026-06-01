package com.example.smart_erp.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.Instant;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.util.ReflectionTestUtils;

import com.example.smart_erp.auth.entity.Role;
import com.example.smart_erp.auth.entity.User;
import com.example.smart_erp.auth.repository.RefreshTokenRepository;
import com.example.smart_erp.auth.repository.SystemLogJdbcRepository;
import com.example.smart_erp.auth.repository.UserRepository;
import com.example.smart_erp.auth.session.LoginBruteForceProtection;
import com.example.smart_erp.auth.session.LoginSessionRegistry;
import com.example.smart_erp.auth.session.RefreshAccessThrottle;
import com.example.smart_erp.auth.support.JwtTokenService;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;

@ExtendWith(MockitoExtension.class)
class AuthServiceLoginTest {

	@Mock
	private UserRepository userRepository;

	@Mock
	private RefreshTokenRepository refreshTokenRepository;

	@Mock
	private PasswordEncoder passwordEncoder;

	@Mock
	private JwtTokenService jwtTokenService;

	@Mock
	private SystemLogJdbcRepository systemLogJdbcRepository;

	@Mock
	private LoginSessionRegistry loginSessionRegistry;

	@Mock
	private LoginBruteForceProtection loginBruteForceProtection;

	private final RefreshAccessThrottle refreshAccessThrottle = new RefreshAccessThrottle();

	private AuthService authService;

	@BeforeEach
	void setUp() {
		authService = new AuthService(userRepository, refreshTokenRepository, passwordEncoder, jwtTokenService,
				systemLogJdbcRepository, loginSessionRegistry, loginBruteForceProtection, refreshAccessThrottle);
	}

	@Test
	void login_throws403WhenConcurrentSessionStillActive() {
		User user = activeUser(7);
		when(userRepository.countActiveByEmailIgnoreCase("admin@example.com")).thenReturn(1L);
		when(userRepository.findActiveByEmailIgnoreCase("admin@example.com")).thenReturn(Optional.of(user));
		when(userRepository.findByEmailIgnoreCase("admin@example.com")).thenReturn(Optional.of(user));
		org.mockito.Mockito.doThrow(new BusinessException(ApiErrorCode.FORBIDDEN,
				"Tài khoản đang được đăng nhập ở một thiết bị khác. Vui lòng đăng xuất ở thiết bị đó hoặc liên hệ Admin."))
				.when(loginSessionRegistry).assertNoConcurrentSession(7, "client-A");

		when(passwordEncoder.matches("secret123", "hashed")).thenReturn(true);

		assertThatThrownBy(() -> authService.login("admin@example.com", "secret123", "client-A"))
				.isInstanceOfSatisfying(BusinessException.class,
						ex -> assertThat(ex.getCode()).isEqualTo(ApiErrorCode.FORBIDDEN));

		verify(refreshTokenRepository, never()).save(any());
		verify(systemLogJdbcRepository, never()).insertAuthLoginSuccess(7);
	}

	@Test
	void login_allowsWhenSessionGuardPasses() {
		User user = activeUser(7);
		when(userRepository.countActiveByEmailIgnoreCase("admin@example.com")).thenReturn(1L);
		when(userRepository.findActiveByEmailIgnoreCase("admin@example.com")).thenReturn(Optional.of(user));
		when(userRepository.findByEmailIgnoreCase("admin@example.com")).thenReturn(Optional.of(user));
		when(passwordEncoder.matches("secret123", "hashed")).thenReturn(true);
		when(jwtTokenService.createAccessToken(eq(7), eq("admin"), eq("Owner"), anyString())).thenReturn("new.jwt");
		when(userRepository.save(any(User.class))).thenReturn(user);

		LoginResult result = authService.login("admin@example.com", "secret123", "client-A");

		assertThat(result.accessToken()).isEqualTo("new.jwt");
		verify(loginSessionRegistry).assertNoConcurrentSession(7, "client-A");
		verify(loginSessionRegistry).register(7, "new.jwt", "client-A");
	}

	private static User activeUser(int id) {
		User u = new User();
		ReflectionTestUtils.setField(u, "id", id);
		ReflectionTestUtils.setField(u, "username", "admin");
		ReflectionTestUtils.setField(u, "fullName", "Admin");
		ReflectionTestUtils.setField(u, "email", "admin@example.com");
		ReflectionTestUtils.setField(u, "passwordHash", "hashed");
		ReflectionTestUtils.setField(u, "status", "Active");
		ReflectionTestUtils.setField(u, "lastLogin", Instant.now());
		Role role = new Role();
		ReflectionTestUtils.setField(role, "name", "Owner");
		ReflectionTestUtils.setField(role, "permissions", "{\"can_view_dashboard\":true}");
		ReflectionTestUtils.setField(u, "role", role);
		return u;
	}
}
