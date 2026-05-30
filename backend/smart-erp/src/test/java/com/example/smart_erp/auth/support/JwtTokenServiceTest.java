package com.example.smart_erp.auth.support;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

import com.example.smart_erp.config.AppSecurityProperties;

class JwtTokenServiceTest {

	@Test
	void isAccessTokenActiveForSessionMap_distinguishesValidAndInvalidToken() {
		AppSecurityProperties props = new AppSecurityProperties();
		AppSecurityProperties.Jwt jwt = new AppSecurityProperties.Jwt();
		jwt.setSecret("test-jwt-signing-secret-32-chars-min!!");
		jwt.setIssuer("https://issuer.test");
		jwt.setAudience("erp-api");
		jwt.setAccessTtlMinutes(1);
		props.setJwt(jwt);

		JwtTokenService service = new JwtTokenService(props);
		String token = service.createAccessToken(1, "admin", "Owner", "{}");

		assertThat(service.isAccessTokenActiveForSessionMap(token)).isTrue();
		assertThat(service.isAccessTokenActiveForSessionMap(token + "x")).isFalse();
	}
}
