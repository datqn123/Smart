package com.example.smart_erp.auth.support;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;

/**
 * Task101: tập boolean gọn cho side menu, nhúng vào JWT (claim {@value #CLAIM_NAME}).
 * Cùng tập khóa với subset đọc từ cột {@code roles.permissions} (JSONB).
 */
public final class MenuPermissionClaims {

	public static final String CLAIM_NAME = "mp";

	private static final ObjectMapper MAPPER = JsonMapper.builder().build();

	private static final String[] MENU_KEYS = {
		"can_view_dashboard",
		"can_use_ai",
		"can_manage_inventory",
		"can_manage_products",
		"can_manage_customers",
		"can_manage_orders",
		"can_approve",
		"can_view_finance",
		"can_manage_staff",
		"can_configure_alerts",
		"can_view_store_profile",
		"can_view_system_logs",
		"can_manage_custom_builder",
		"can_use_custom_entities"
	};

	private MenuPermissionClaims() {
	}

	/**
	 * Rút các cờ boolean cần cho menu từ toàn bộ JSON {@code permissions} trên bảng Roles.
	 * Key thiếu hoặc lỗi parse → false.
	 */
	public static Map<String, Boolean> fromRolePermissionsJson(String rolePermissionsJson) {
		Map<String, Boolean> out = new LinkedHashMap<>();
		for (String k : MENU_KEYS) {
			out.put(k, false);
		}
		if (rolePermissionsJson == null || rolePermissionsJson.isBlank()) {
			return out;
		}
		try {
			JsonNode root = MAPPER.readTree(rolePermissionsJson);
			if (!root.isObject()) {
				return out;
			}
			for (String k : MENU_KEYS) {
				if (root.has(k) && root.get(k).isBoolean()) {
					out.put(k, root.get(k).asBoolean());
				}
			}
		}
		catch (Exception e) {
			// bảo toàn: toàn false
		}
		return Collections.unmodifiableMap(out);
	}

	/**
	 * Task101_1: từ claim {@value #CLAIM_NAME} (mỗi key true) → dùng cho
	 * {@code hasAuthority('can_…')}.
	 */
	public static List<GrantedAuthority> grantedAuthoritiesFromMpClaim(Object mp) {
		if (!(mp instanceof Map<?, ?> map)) {
			return List.of();
		}
		List<GrantedAuthority> list = new ArrayList<>();
		for (String k : MENU_KEYS) {
			Object v = map.get(k);
			if (Boolean.TRUE.equals(v)) {
				list.add(new SimpleGrantedAuthority(k));
			}
		}
		return list;
	}

	/**
	 * Mỗi nhánh boolean true trong mã {@code permissions} từ DB ánh xạ một
	 * {@code GrantedAuthority} tên bằng tên key (cùng chuỗi với JWT về mặt hiệu lực
	 * nếu BE đồng bộ claim {@value #CLAIM_NAME} từ cùng bản ghi).
	 */
	public static List<GrantedAuthority> grantedAuthoritiesFromPermissionsJson(String rolePermissionsJson) {
		Map<String, Boolean> map = fromRolePermissionsJson(rolePermissionsJson);
		List<GrantedAuthority> out = new ArrayList<>();
		for (Map.Entry<String, Boolean> e : map.entrySet()) {
			if (Boolean.TRUE.equals(e.getValue())) {
				out.add(new SimpleGrantedAuthority(e.getKey()));
			}
		}
		return out;
	}

	/**
	 * Dùng trong cấu hình OAuth2 Resource Server (khi
	 * {@code app.security.api-protection=jwt-api}).
	 */
	public static Converter<Jwt, AbstractAuthenticationToken> jwtAuthenticationConverter() {
		JwtAuthenticationConverter c = new JwtAuthenticationConverter();
		c.setJwtGrantedAuthoritiesConverter(
				(Jwt j) -> grantedAuthoritiesFromMpClaim(j.getClaim(CLAIM_NAME)));
		return c;
	}
}
