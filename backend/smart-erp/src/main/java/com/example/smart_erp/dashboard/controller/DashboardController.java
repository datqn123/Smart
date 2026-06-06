package com.example.smart_erp.dashboard.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.api.ApiSuccessResponse;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.dashboard.response.DashboardData;
import com.example.smart_erp.dashboard.service.DashboardService;

@RestController
@RequestMapping("/api/v1")
public class DashboardController {

	private static final String UNAUTHORIZED = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";

	private final DashboardService dashboardService;

	public DashboardController(DashboardService dashboardService) {
		this.dashboardService = dashboardService;
	}

	@GetMapping("/dashboard")
	@PreAuthorize("hasAuthority('can_view_dashboard')")
	public ResponseEntity<ApiSuccessResponse<DashboardData>> dashboard(Authentication authentication,
			@RequestParam(name = "trendDays", required = false) String trendDays,
			@RequestParam(name = "recentLimit", required = false) String recentLimit,
			@RequestParam(name = "topCustomerLimit", required = false) String topCustomerLimit,
			@RequestParam(name = "alertLimit", required = false) String alertLimit,
			@RequestParam(name = "include", required = false) String include) {
		DashboardData data = dashboardService.getDashboard(requireJwt(authentication), trendDays, recentLimit,
				topCustomerLimit, alertLimit, include);
		return ResponseEntity.ok(ApiSuccessResponse.of(data, "Thành công"));
	}

	private static Jwt requireJwt(Authentication authentication) {
		if (authentication == null || authentication instanceof AnonymousAuthenticationToken
				|| !(authentication.getPrincipal() instanceof Jwt jwt)) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, UNAUTHORIZED);
		}
		return jwt;
	}
}
