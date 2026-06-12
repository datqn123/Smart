package com.example.smart_erp.custominterface.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.api.ApiSuccessResponse;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.custominterface.dto.CustomBuilderBundleRequest;
import com.example.smart_erp.custominterface.dto.CustomPublishRequest;
import com.example.smart_erp.custominterface.response.CustomBuilderBundleData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.custominterface.service.CustomBuilderService;

@RestController
@RequestMapping("/api/v1/custom/builder")
public class CustomBuilderController {

	private static final String UNAUTHORIZED = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";

	private final CustomBuilderService service;

	public CustomBuilderController(CustomBuilderService service) {
		this.service = service;
	}

	@GetMapping("/pages/{pageKey}/bundle")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> bundle(@PathVariable String pageKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.getBundle(pageKey), "Thành công"));
	}

	@PatchMapping("/pages/{pageKey}/bundle")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> saveBundle(Authentication authentication,
			@PathVariable String pageKey, @RequestBody CustomBuilderBundleRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.saveBundle(pageKey, request, requireJwt(authentication)),
				"Đã lưu bản nháp cấu hình giao diện"));
	}

	@PostMapping("/pages/{pageKey}/validate")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<ValidationSummaryData>> validate(@PathVariable String pageKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.validatePage(pageKey), "Thành công"));
	}

	@PostMapping("/pages/{pageKey}/publish")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomBuilderBundleData>> publish(Authentication authentication,
			@PathVariable String pageKey, @RequestBody(required = false) CustomPublishRequest request) {
		String etag = request == null ? null : request.etag();
		return ResponseEntity.ok(ApiSuccessResponse.of(service.publish(pageKey, etag, requireJwt(authentication)),
				"Đã publish cấu hình giao diện"));
	}

	private static Jwt requireJwt(Authentication authentication) {
		if (authentication == null || authentication instanceof AnonymousAuthenticationToken
				|| !(authentication.getPrincipal() instanceof Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED);
		}
		return jwt;
	}
}
