package com.example.smart_erp.auth.controller;

import java.util.Collections;
import java.util.Map;

import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.smart_erp.auth.dto.LoginRequest;
import com.example.smart_erp.auth.dto.LogoutRequest;
import com.example.smart_erp.auth.dto.PasswordResetRequestDto;
import com.example.smart_erp.auth.dto.RefreshRequest;
import com.example.smart_erp.auth.response.LoginResponseData;
import com.example.smart_erp.auth.response.RefreshResponseData;
import com.example.smart_erp.auth.service.AuthService;
import com.example.smart_erp.auth.service.LoginResult;
import com.example.smart_erp.auth.service.RefreshResult;
import com.example.smart_erp.auth.service.StaffPasswordResetRequestService;
import com.example.smart_erp.auth.session.LoginSessionRegistry;
import com.example.smart_erp.auth.support.JwtTokenService;
import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.api.ApiSuccessResponse;
import com.example.smart_erp.common.exception.BusinessException;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

	private static final String LOGOUT_SUCCESS_MESSAGE = "Đăng xuất thành công và đã hủy các phiên làm việc";

	private static final String UNAUTHORIZED_TOKEN_MESSAGE = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn";

	private static final String REFRESH_SUCCESS_MESSAGE = "Token đã được làm mới";

	private final AuthService authService;

	private final StaffPasswordResetRequestService staffPasswordResetRequestService;

	private final JwtTokenService jwtTokenService;

	private final LoginSessionRegistry loginSessionRegistry;

	public AuthController(AuthService authService, StaffPasswordResetRequestService staffPasswordResetRequestService,
			JwtTokenService jwtTokenService, LoginSessionRegistry loginSessionRegistry) {
		this.authService = authService;
		this.staffPasswordResetRequestService = staffPasswordResetRequestService;
		this.jwtTokenService = jwtTokenService;
		this.loginSessionRegistry = loginSessionRegistry;
	}

	@PostMapping("/refresh")
	public ResponseEntity<ApiSuccessResponse<RefreshResponseData>> refresh(@Valid @RequestBody RefreshRequest request) {
		RefreshResult result = authService.refresh(request.refreshToken());
		loginSessionRegistry.register(result.userId(), result.accessToken());
		RefreshResponseData data = new RefreshResponseData(result.accessToken(), result.refreshTokenPlain());
		return ResponseEntity.ok(ApiSuccessResponse.of(data, REFRESH_SUCCESS_MESSAGE));
	}

	@PostMapping("/login")
	public ResponseEntity<ApiSuccessResponse<LoginResponseData>> login(@Valid @RequestBody LoginRequest request) {
		LoginResult result = authService.login(request.email(), request.password());
		LoginResponseData data = new LoginResponseData(result.accessToken(), result.refreshToken(), result.user());
		return ResponseEntity.ok(ApiSuccessResponse.of(data, "Đăng nhập thành công"));
	}

	/** Task004 §1 — public */
	@PostMapping("/password-reset-requests")
	public ResponseEntity<ApiSuccessResponse<Map<String, Object>>> passwordResetRequests(
			@Valid @RequestBody PasswordResetRequestDto request) {
		staffPasswordResetRequestService.submitPublicRequest(request.username(), request.message());
		return ResponseEntity
				.ok(ApiSuccessResponse.of(Collections.emptyMap(), StaffPasswordResetRequestService.RESPONSE_MESSAGE));
	}

	@PostMapping("/logout")
	public ResponseEntity<ApiSuccessResponse<Map<String, Object>>> logout(
			@RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String authorization,
			@Valid @RequestBody LogoutRequest request) {
		String compactAccess = extractBearerAccessToken(authorization);
		int userId = jwtTokenService.parseAccessTokenUserId(compactAccess);
		authService.logout(userId, request.refreshToken());
		loginSessionRegistry.clear(userId);
		return ResponseEntity.ok(ApiSuccessResponse.of(Collections.emptyMap(), LOGOUT_SUCCESS_MESSAGE));
	}

	private static String extractBearerAccessToken(String authorization) {
		if (authorization == null) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED_TOKEN_MESSAGE);
		}
		String trimmed = authorization.strip();
		if (!trimmed.regionMatches(true, 0, "Bearer ", 0, 7)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED_TOKEN_MESSAGE);
		}
		String token = trimmed.substring(7).strip();
		if (!StringUtils.hasText(token)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED_TOKEN_MESSAGE);
		}
		return token;
	}
}
