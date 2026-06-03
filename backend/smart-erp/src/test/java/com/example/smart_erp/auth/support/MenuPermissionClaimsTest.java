package com.example.smart_erp.auth.support;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

class MenuPermissionClaimsTest {

	@Test
	void fromRolePermissionsJson_parsesOwnerLikeSeed() {
		String json = "{\"can_view_dashboard\": true, \"can_use_ai\": false, \"can_manage_inventory\": true}";
		Map<String, Boolean> m = MenuPermissionClaims.fromRolePermissionsJson(json);
		assertThat(m.get("can_view_dashboard")).isTrue();
		assertThat(m.get("can_use_ai")).isFalse();
		assertThat(m.get("can_manage_inventory")).isTrue();
		assertThat(m.get("can_approve")).isFalse();
		assertThat(m.get("can_manage_customers")).isFalse();
	}

	@Test
	void fromRolePermissionsJson_canManageCustomersWhenPresent() {
		String json = "{\"can_manage_customers\": true}";
		assertThat(MenuPermissionClaims.fromRolePermissionsJson(json).get("can_manage_customers")).isTrue();
	}

	@Test
	void fromRolePermissionsJson_customBuilderPermissionsWhenPresent() {
		String json = "{\"can_manage_custom_builder\": true, \"can_use_custom_entities\": true}";
		Map<String, Boolean> m = MenuPermissionClaims.fromRolePermissionsJson(json);
		assertThat(m.get("can_manage_custom_builder")).isTrue();
		assertThat(m.get("can_use_custom_entities")).isTrue();
	}

	@Test
	void fromRolePermissionsJson_nullOrBlank_allFalse() {
		assertThat(MenuPermissionClaims.fromRolePermissionsJson(null).get("can_view_finance")).isFalse();
		assertThat(MenuPermissionClaims.fromRolePermissionsJson("").get("can_view_finance")).isFalse();
	}

	@Test
	void grantedAuthoritiesFromMpClaim_marksTrueAsAuthorities() {
		List<GrantedAuthority> list = MenuPermissionClaims.grantedAuthoritiesFromMpClaim(
				Map.of("can_manage_staff", true, "can_approve", false, "can_manage_custom_builder", true));
		assertThat(list)
				.contains(new SimpleGrantedAuthority("can_manage_staff"))
				.contains(new SimpleGrantedAuthority("can_manage_custom_builder"))
				.doesNotContain(new SimpleGrantedAuthority("can_approve"));
	}

	@Test
	void grantedAuthoritiesFromPermissionsJson_matchesJsonBooleans() {
		String json = """
				{"can_view_dashboard": true, "can_manage_staff": true}
				""";
		assertThat(MenuPermissionClaims.grantedAuthoritiesFromPermissionsJson(json))
				.containsExactlyInAnyOrder(
						new SimpleGrantedAuthority("can_view_dashboard"), new SimpleGrantedAuthority("can_manage_staff"));
	}
}
