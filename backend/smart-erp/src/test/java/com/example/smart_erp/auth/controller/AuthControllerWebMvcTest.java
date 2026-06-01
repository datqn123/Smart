package com.example.smart_erp.auth.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Objects;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.smart_erp.auth.AuthTask001Fixtures;
import com.example.smart_erp.auth.dto.LoginRequest;
import com.example.smart_erp.auth.dto.LogoutRequest;
import com.example.smart_erp.auth.dto.RefreshRequest;
import com.example.smart_erp.auth.service.AuthService;
import com.example.smart_erp.auth.service.LoginResult;
import com.example.smart_erp.auth.service.RefreshResult;
import com.example.smart_erp.auth.service.StaffPasswordResetRequestService;
import com.example.smart_erp.auth.session.LoginSessionRegistry;
import com.example.smart_erp.auth.support.JwtTokenService;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.common.exception.GlobalExceptionHandler;
import com.example.smart_erp.common.exception.MaxUploadSizeExceededAdvice;
import com.example.smart_erp.config.PermitAllWebSecurityConfiguration;
import com.example.smart_erp.config.SecurityBeansConfiguration;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Task001 login — tài khoản dev để test thủ công: xem {@link AuthTask001Fixtures}.
 */
@WebMvcTest(controllers = AuthController.class)
@Import({ GlobalExceptionHandler.class, MaxUploadSizeExceededAdvice.class, SecurityBeansConfiguration.class,
		PermitAllWebSecurityConfiguration.class })
class AuthControllerWebMvcTest {

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private ObjectMapper objectMapper;

	@MockitoBean
	private AuthService authService;

	@MockitoBean
	private JwtTokenService jwtTokenService;

	@MockitoBean
	private LoginSessionRegistry loginSessionRegistry;

	@MockitoBean
	private StaffPasswordResetRequestService staffPasswordResetRequestService;

	@Test
	void refresh_success_returns200RegistersSessionAndEchoesRefresh() throws Exception {
		when(authService.refresh("my-refresh")).thenReturn(new RefreshResult("new.access", "my-refresh", 1));
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new RefreshRequest("my-refresh")));

		mockMvc.perform(post("/api/v1/auth/refresh").header("X-Client-Session-Id", "client-A")
				.contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isOk()).andExpect(jsonPath("$.success").value(true))
				.andExpect(jsonPath("$.data.accessToken").value("new.access"))
				.andExpect(jsonPath("$.data.refreshToken").value("my-refresh"))
				.andExpect(jsonPath("$.message").value("Token đã được làm mới"));

		verify(authService).refresh("my-refresh");
		verify(loginSessionRegistry).register(1, "new.access", "client-A");
	}

	@Test
	void refresh_returns400WhenRefreshTokenBlank() throws Exception {
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new RefreshRequest("")));
		mockMvc.perform(post("/api/v1/auth/refresh").contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isBadRequest()).andExpect(jsonPath("$.details.refreshToken").exists());

		verifyNoInteractions(authService, loginSessionRegistry);
	}

	@Test
	void refresh_returns401WhenServiceUnauthorized() throws Exception {
		when(authService.refresh("bad")).thenThrow(
				new BusinessException(ApiErrorCode.UNAUTHORIZED, "Refresh token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại."));
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new RefreshRequest("bad")));

		mockMvc.perform(post("/api/v1/auth/refresh").contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error").value("UNAUTHORIZED"));

		verify(loginSessionRegistry, never()).register(anyInt(), anyString(), any());
	}

	@Test
	void refresh_returns429WhenThrottled() throws Exception {
		when(authService.refresh("tok")).thenThrow(new BusinessException(ApiErrorCode.TOO_MANY_REQUESTS, "Chậm lại"));
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new RefreshRequest("tok")));

		mockMvc.perform(post("/api/v1/auth/refresh").contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isTooManyRequests()).andExpect(jsonPath("$.error").value("TOO_MANY_REQUESTS"));

		verify(loginSessionRegistry, never()).register(anyInt(), anyString(), any());
	}

	@Test
	void login_trimsPaddedEmailBeforeAuthService() throws Exception {
		LoginResult.LoginUserDto user = new LoginResult.LoginUserDto(1, "admin", "System Administrator",
				AuthTask001Fixtures.DEV_OWNER_EMAIL, "Owner");
		when(authService.login(eq(AuthTask001Fixtures.DEV_OWNER_EMAIL), eq(AuthTask001Fixtures.DEV_OWNER_PASSWORD),
				eq("client-A")))
				.thenReturn(new LoginResult("access.jwt", "refreshuuid", user));

		String bodyJson = """
				{"email":"  %s  ","password":"%s"}
				""".formatted(AuthTask001Fixtures.DEV_OWNER_EMAIL, AuthTask001Fixtures.DEV_OWNER_PASSWORD);

		mockMvc.perform(post("/api/v1/auth/login").header("X-Client-Session-Id", "client-A")
				.contentType(MediaType.APPLICATION_JSON_VALUE)
				.content(Objects.requireNonNull(bodyJson.strip())))
				.andExpect(status().isOk());

		verify(authService).login(AuthTask001Fixtures.DEV_OWNER_EMAIL, AuthTask001Fixtures.DEV_OWNER_PASSWORD, "client-A");
	}

	@Test
	void login_returnsEnvelope() throws Exception {
		LoginResult.LoginUserDto user = new LoginResult.LoginUserDto(1, "admin", "System Administrator",
				AuthTask001Fixtures.DEV_OWNER_EMAIL, "Owner");
		when(authService.login(eq(AuthTask001Fixtures.DEV_OWNER_EMAIL), eq(AuthTask001Fixtures.DEV_OWNER_PASSWORD),
				eq("client-A")))
				.thenReturn(new LoginResult("access.jwt", "refreshuuid", user));

		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(
				new LoginRequest(AuthTask001Fixtures.DEV_OWNER_EMAIL, AuthTask001Fixtures.DEV_OWNER_PASSWORD)));
		mockMvc.perform(post("/api/v1/auth/login").header("X-Client-Session-Id", "client-A")
				.contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.success").value(true))
				.andExpect(jsonPath("$.data.accessToken").value("access.jwt"))
				.andExpect(jsonPath("$.data.refreshToken").value("refreshuuid"))
				.andExpect(jsonPath("$.data.user.role").value("Owner"))
				.andExpect(jsonPath("$.message").value("Đăng nhập thành công"));
	}

	@Test
	void login_validation_returns400WithDetailsWhenPasswordTooShort() throws Exception {
		String bodyJson = Objects.requireNonNull(
				objectMapper.writeValueAsString(new LoginRequest("staff01@example.com", "12345")));
		mockMvc.perform(post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.success").value(false))
				.andExpect(jsonPath("$.error").value("BAD_REQUEST"))
				.andExpect(jsonPath("$.details.password").value("Mật khẩu phải có ít nhất 6 ký tự"));
	}

	@Test
	void login_validation_returns400WithDetailsWhenFieldsInvalid() throws Exception {
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new LoginRequest("", "")));
		mockMvc.perform(post("/api/v1/auth/login").contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.success").value(false))
				.andExpect(jsonPath("$.error").value("BAD_REQUEST"))
				.andExpect(jsonPath("$.details.email").exists())
				.andExpect(jsonPath("$.details.password").exists());
	}

	@Test
	void logout_success_returns200AndClearsSessionRegistry() throws Exception {
		when(jwtTokenService.parseAccessTokenUserId("access.jwt")).thenReturn(1);
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new LogoutRequest("refreshplain")));

		mockMvc.perform(post("/api/v1/auth/logout").header(HttpHeaders.AUTHORIZATION, "Bearer access.jwt")
				.contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson)).andExpect(status().isOk())
				.andExpect(jsonPath("$.success").value(true)).andExpect(jsonPath("$.data").isMap())
				.andExpect(jsonPath("$.message").value("Đăng xuất thành công và đã hủy các phiên làm việc"));

		verify(authService).logout(1, "refreshplain");
		verify(loginSessionRegistry).clear(1);
	}

	@Test
	void logout_returns400WhenRefreshTokenBlank() throws Exception {
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new LogoutRequest("")));
		mockMvc.perform(post("/api/v1/auth/logout").header(HttpHeaders.AUTHORIZATION, "Bearer access.jwt")
				.contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson)).andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.details.refreshToken").exists());

		verifyNoInteractions(jwtTokenService, loginSessionRegistry);
	}

	@Test
	void logout_returns401WhenMissingAuthorization() throws Exception {
		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new LogoutRequest("refreshplain")));
		mockMvc.perform(post("/api/v1/auth/logout").contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson))
				.andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error").value("UNAUTHORIZED"));

		verifyNoInteractions(jwtTokenService, authService, loginSessionRegistry);
	}

	@Test
	void logout_returns403WhenRefreshDoesNotMatch() throws Exception {
		when(jwtTokenService.parseAccessTokenUserId("access.jwt")).thenReturn(1);
		doThrow(new BusinessException(ApiErrorCode.FORBIDDEN, "Refresh token không khớp với phiên đăng nhập hiện tại"))
				.when(authService).logout(1, "bad");

		String bodyJson = Objects.requireNonNull(objectMapper.writeValueAsString(new LogoutRequest("bad")));
		mockMvc.perform(post("/api/v1/auth/logout").header(HttpHeaders.AUTHORIZATION, "Bearer access.jwt")
				.contentType(MediaType.APPLICATION_JSON_VALUE).content(bodyJson)).andExpect(status().isForbidden())
				.andExpect(jsonPath("$.error").value("FORBIDDEN"));

		verify(loginSessionRegistry, never()).clear(anyInt());
	}
}
