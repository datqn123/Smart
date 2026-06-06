package com.example.smart_erp.dashboard.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.security.oauth2.jwt.Jwt;

import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.dashboard.service.DashboardService.Section;

class DashboardServiceTest {

	@Test
	void parseQueryDefaultsToAllSectionsAndDefaultLimits() {
		var query = DashboardService.parseQuery(null, null, null, null, null);

		assertThat(query.trendDays()).isEqualTo(7);
		assertThat(query.recentLimit()).isEqualTo(5);
		assertThat(query.topCustomerLimit()).isEqualTo(5);
		assertThat(query.alertLimit()).isEqualTo(5);
		assertThat(query.includes()).containsExactlyInAnyOrder(Section.values());
	}

	@Test
	void parseQueryClampsLimitsAndSupportsPartialIncludes() {
		var query = DashboardService.parseQuery("30", "99", "2", "21", "kpis,orders,alerts");

		assertThat(query.trendDays()).isEqualTo(30);
		assertThat(query.recentLimit()).isEqualTo(20);
		assertThat(query.topCustomerLimit()).isEqualTo(2);
		assertThat(query.alertLimit()).isEqualTo(20);
		assertThat(query.includes(Section.KPIS)).isTrue();
		assertThat(query.includes(Section.ORDERS)).isTrue();
		assertThat(query.includes(Section.ALERTS)).isTrue();
		assertThat(query.includes(Section.FINANCIAL)).isFalse();
	}

	@Test
	void parseQueryRejectsInvalidTrendDaysAndInclude() {
		assertThatThrownBy(() -> DashboardService.parseQuery("14", null, null, null, null))
				.isInstanceOf(BusinessException.class);
		assertThatThrownBy(() -> DashboardService.parseQuery(null, null, null, null, "kpis,bad"))
				.isInstanceOf(BusinessException.class);
	}

	@Test
	void canSeeFinancialsAllowsOnlyFinancialRoles() {
		assertThat(DashboardService.canSeeFinancials(jwt("Owner"))).isTrue();
		assertThat(DashboardService.canSeeFinancials(jwt("Admin"))).isTrue();
		assertThat(DashboardService.canSeeFinancials(jwt("Manager"))).isTrue();
		assertThat(DashboardService.canSeeFinancials(jwt("Staff"))).isFalse();
	}

	private static Jwt jwt(String role) {
		return new Jwt("token", Instant.EPOCH, Instant.EPOCH.plusSeconds(60), Map.of("alg", "none"), Map.of("role", role));
	}
}
