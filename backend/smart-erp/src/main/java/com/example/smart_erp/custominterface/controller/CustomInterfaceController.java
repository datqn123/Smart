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
import com.example.smart_erp.custominterface.dto.CustomFolderRequest;
import com.example.smart_erp.custominterface.dto.CustomPageRequest;
import com.example.smart_erp.custominterface.dto.CustomPublishRequest;
import com.example.smart_erp.custominterface.dto.CustomReorderRequest;
import com.example.smart_erp.custominterface.response.CustomMenuTreeData;
import com.example.smart_erp.custominterface.response.ValidationSummaryData;
import com.example.smart_erp.custominterface.service.CustomInterfaceService;

@RestController
@RequestMapping("/api/v1/custom")
public class CustomInterfaceController {

	private static final String UNAUTHORIZED = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";

	private final CustomInterfaceService service;

	public CustomInterfaceController(CustomInterfaceService service) {
		this.service = service;
	}

	@GetMapping("/menu-tree")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> menuTree() {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.menuTree(), "Thành công"));
	}

	@PostMapping("/menu-folders")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> createFolder(Authentication authentication,
			@RequestBody CustomFolderRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.createFolder(request, requireJwt(authentication)),
				"Đã lưu bản nháp cấu hình giao diện"));
	}

	@PatchMapping("/menu-folders/{folderKey}")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> updateFolder(Authentication authentication,
			@PathVariable String folderKey, @RequestBody CustomFolderRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.updateFolder(folderKey, request, requireJwt(authentication)),
				"Đã lưu bản nháp cấu hình giao diện"));
	}

	@PostMapping("/menu-pages")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> createPage(Authentication authentication,
			@RequestBody CustomPageRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.createPage(request, requireJwt(authentication)),
				"Đã lưu bản nháp cấu hình giao diện"));
	}

	@PatchMapping("/menu-pages/{pageKey}")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> updatePage(Authentication authentication,
			@PathVariable String pageKey, @RequestBody CustomPageRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.updatePage(pageKey, request, requireJwt(authentication)),
				"Đã lưu bản nháp cấu hình giao diện"));
	}

	@PostMapping("/menu/reorder")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> reorder(Authentication authentication,
			@RequestBody CustomReorderRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.reorder(request, requireJwt(authentication)),
				"Đã cập nhật thứ tự giao diện"));
	}

	@PostMapping("/menu/validate")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<ValidationSummaryData>> validatePublish() {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.validatePublish(), "Thành công"));
	}

	@PostMapping("/menu/publish")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> publish(Authentication authentication,
			@RequestBody(required = false) CustomPublishRequest request) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.publish(request, requireJwt(authentication)),
				"Đã publish cấu hình giao diện"));
	}

	@PatchMapping("/menu-folders/{folderKey}/archive")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> archiveFolder(Authentication authentication,
			@PathVariable String folderKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.archiveFolder(folderKey, requireJwt(authentication)),
				"Đã ẩn danh mục menu"));
	}

	@PatchMapping("/menu-pages/{pageKey}/archive")
	@PreAuthorize("hasAuthority('can_manage_custom_builder')")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> archivePage(Authentication authentication,
			@PathVariable String pageKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.archivePage(pageKey, requireJwt(authentication)),
				"Đã ẩn giao diện tùy chỉnh"));
	}

	@GetMapping("/runtime-menu")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> runtimeMenu(Authentication authentication) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.runtimeMenu(authentication, requireJwt(authentication)),
				"Thành công"));
	}

	@GetMapping("/pages/{pageKey}/runtime")
	public ResponseEntity<ApiSuccessResponse<CustomMenuTreeData>> runtimePage(Authentication authentication,
			@PathVariable String pageKey) {
		return ResponseEntity.ok(ApiSuccessResponse.of(service.runtimePage(pageKey, authentication, requireJwt(authentication)),
				"Thành công"));
	}

	private static Jwt requireJwt(Authentication authentication) {
		if (authentication == null || authentication instanceof AnonymousAuthenticationToken
				|| !(authentication.getPrincipal() instanceof Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED);
		}
		return jwt;
	}
}
