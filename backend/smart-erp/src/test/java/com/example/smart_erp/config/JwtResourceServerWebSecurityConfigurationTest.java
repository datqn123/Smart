package com.example.smart_erp.config;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.Date;

import javax.crypto.SecretKey;

import org.junit.jupiter.api.Test;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtException;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

class JwtResourceServerWebSecurityConfigurationTest {

	private static final String SECRET = "test-jwt-signing-secret-32-chars-min!!";

	@Test
	void jwtDecoder_rejectsTokenWhenAudienceMissingButConfigured() {
		AppSecurityProperties props = props("https://issuer.test", "erp-api");
		JwtDecoder decoder = new JwtResourceServerWebSecurityConfiguration().jwtDecoder(props);

		String tokenMissingAudience = token("https://issuer.test", null);

		assertThatThrownBy(() -> decoder.decode(tokenMissingAudience)).isInstanceOf(JwtException.class);
	}

	@Test
	void jwtDecoder_rejectsTokenWhenIssuerMismatch() {
		AppSecurityProperties props = props("https://issuer.test", "erp-api");
		JwtDecoder decoder = new JwtResourceServerWebSecurityConfiguration().jwtDecoder(props);

		String tokenWrongIssuer = token("https://other-issuer.test", "erp-api");

		assertThatThrownBy(() -> decoder.decode(tokenWrongIssuer)).isInstanceOf(JwtException.class);
	}

	@Test
	void jwtDecoder_acceptsTokenWhenIssuerAndAudienceMatch() {
		AppSecurityProperties props = props("https://issuer.test", "erp-api");
		JwtDecoder decoder = new JwtResourceServerWebSecurityConfiguration().jwtDecoder(props);

		String tokenValid = token("https://issuer.test", "erp-api");

		assertThatCode(() -> decoder.decode(tokenValid)).doesNotThrowAnyException();
	}

	private static AppSecurityProperties props(String issuer, String audience) {
		AppSecurityProperties p = new AppSecurityProperties();
		AppSecurityProperties.Jwt jwt = new AppSecurityProperties.Jwt();
		jwt.setSecret(SECRET);
		jwt.setIssuer(issuer);
		jwt.setAudience(audience);
		jwt.setAccessTtlMinutes(30);
		p.setJwt(jwt);
		p.setApiProtection("jwt-api");
		return p;
	}

	private static String token(String issuer, String audience) {
		SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes(java.nio.charset.StandardCharsets.UTF_8));
		var builder = Jwts.builder()
				.subject("1")
				.claim("user_id", "1")
				.claim("tenant_id", "1")
				.claim("name", "admin")
				.claim("role", "Owner")
				.issuedAt(Date.from(Instant.now()))
				.expiration(Date.from(Instant.now().plusSeconds(300)))
				.signWith(key);
		if (issuer != null) {
			builder.issuer(issuer);
		}
		if (audience != null) {
			builder.claim("aud", audience);
		}
		return builder.compact();
	}
}

