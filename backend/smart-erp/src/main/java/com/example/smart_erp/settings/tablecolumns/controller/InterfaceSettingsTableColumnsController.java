package com.example.smart_erp.settings.tablecolumns.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.api.ApiSuccessResponse;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.settings.tablecolumns.dto.SaveTableColumnSettingsRequest;
import com.example.smart_erp.settings.tablecolumns.response.TableColumnSettingsData;
import com.example.smart_erp.settings.tablecolumns.service.TableColumnSettingsService;

@RestController
@RequestMapping("/api/v1/interface-settings/table-columns")
@Validated
public class InterfaceSettingsTableColumnsController {

	private static final String UNAUTHORIZED_PERMIT_ALL = "Bearer JWT không được áp dụng: backend đang permit-all (mặc định APP_SECURITY_MODE). "
			+ "Đặt APP_SECURITY_MODE=jwt-api (hoặc app.security.api-protection=jwt-api), khởi động lại, đăng nhập Task001 rồi gửi lại request.";

	private static final String UNAUTHORIZED_NO_JWT_PRINCIPAL = "Không có JWT hợp lệ trong phiên bảo mật. "
			+ "Kiểm tra Header Authorization: Bearer <accessToken>; nếu đã bật jwt-api, access token có thể đã hết hạn — đăng nhập hoặc refresh lại.";

	private final TableColumnSettingsService service;

	public InterfaceSettingsTableColumnsController(TableColumnSettingsService service) {
		this.service = service;
	}

	@GetMapping
	@PreAuthorize("hasAuthority('can_manage_inventory')")
	public ResponseEntity<ApiSuccessResponse<TableColumnSettingsData>> getInventoryScope(Authentication authentication,
			@RequestParam(value = "scope", required = false, defaultValue = "inventory") String scope) {
		if (!"inventory".equalsIgnoreCase(scope.trim())) {
			throw new BusinessException(ApiErrorCode.BAD_REQUEST, "Tham số yêu cầu không hợp lệ",
					java.util.Map.of("scope", "Giá trị hợp lệ: inventory"));
		}
		Jwt jwt = requireJwt(authentication);
		TableColumnSettingsData data = service.getInventoryScope(jwt);
		return ResponseEntity.ok(ApiSuccessResponse.of(data, "Thành công"));
	}

	@PutMapping
	@PreAuthorize("hasAuthority('can_manage_inventory') and hasAuthority('can_manage_staff')")
	public ResponseEntity<ApiSuccessResponse<TableColumnSettingsData>> saveInventoryScope(Authentication authentication,
			@RequestBody SaveTableColumnSettingsRequest request) {
		Jwt jwt = requireJwt(authentication);
		TableColumnSettingsData data = service.saveInventoryScope(jwt, request);
		return ResponseEntity.ok(ApiSuccessResponse.of(data, "Đã cập nhật cấu hình cột"));
	}

	private static Jwt requireJwt(Authentication authentication) {
		if (authentication == null || authentication instanceof AnonymousAuthenticationToken) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED_PERMIT_ALL);
		}
		if (!(authentication.getPrincipal() instanceof Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED_NO_JWT_PRINCIPAL);
		}
		return jwt;
	}
}
