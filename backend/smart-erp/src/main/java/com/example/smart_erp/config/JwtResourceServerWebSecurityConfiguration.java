package com.example.smart_erp.config;

import java.nio.charset.StandardCharsets;

import javax.crypto.SecretKey;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtClaimValidator;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtValidators;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.security.oauth2.jwt.JwtTimestampValidator;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2TokenValidator;
import org.springframework.security.oauth2.jwt.JwtIssuerValidator;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.util.StringUtils;

import com.example.smart_erp.auth.support.MenuPermissionClaims;

import io.jsonwebtoken.security.Keys;

/**
 * OAuth2 Resource Server (JWT Bearer) for protected APIs; public auth endpoints under {@code /api/v1/auth/**}.
 * Activate with {@code app.security.api-protection=jwt-api} and a strong {@code app.security.jwt.secret}.
 */
@Configuration
@ConditionalOnProperty(prefix = "app.security", name = "api-protection", havingValue = "jwt-api")
public class JwtResourceServerWebSecurityConfiguration {

	@Bean
	public JwtDecoder jwtDecoder(AppSecurityProperties props) {
		String raw = props.getJwt().getSecret();
		byte[] keyBytes = raw.getBytes(StandardCharsets.UTF_8);
		if (keyBytes.length < 32) {
			throw new IllegalStateException(
					"When app.security.api-protection=jwt-api, app.security.jwt.secret (or JWT_SECRET) "
							+ "must be non-empty UTF-8 with byte length >= 32 (HS256).");
		}
		SecretKey key = Keys.hmacShaKeyFor(keyBytes);
		NimbusJwtDecoder decoder = NimbusJwtDecoder.withSecretKey(key).macAlgorithm(MacAlgorithm.HS256).build();
		decoder.setJwtValidator(buildJwtValidator(props));
		return decoder;
	}

	private static OAuth2TokenValidator<Jwt> buildJwtValidator(AppSecurityProperties props) {
		var validators = new java.util.ArrayList<OAuth2TokenValidator<Jwt>>();
		validators.add(new JwtTimestampValidator());
		validators.add(JwtValidators.createDefault());
		if (StringUtils.hasText(props.getJwt().getIssuer())) {
			validators.add(new JwtIssuerValidator(props.getJwt().getIssuer().trim()));
		}
		if (StringUtils.hasText(props.getJwt().getAudience())) {
			String expectedAudience = props.getJwt().getAudience().trim();
			validators.add(new JwtClaimValidator<java.util.Collection<String>>("aud",
					aud -> aud != null && aud.contains(expectedAudience)));
		}
		return new DelegatingOAuth2TokenValidator<>(validators);
	}

	@Bean
	public Converter<Jwt, AbstractAuthenticationToken> accessTokenConverter() {
		return MenuPermissionClaims.jwtAuthenticationConverter();
	}

	@Bean
	@Order(1)
	public SecurityFilterChain authPublicChain(HttpSecurity http) throws Exception {
		http.securityMatcher("/api/v1/auth/**").cors(Customizer.withDefaults()).csrf(csrf -> csrf.disable())
				.authorizeHttpRequests(auth -> auth.anyRequest().permitAll());
		return http.build();
	}

	@Bean
	@Order(2)
	public SecurityFilterChain resourceServerChain(HttpSecurity http, JwtDecoder jwtDecoder,
			Converter<Jwt, AbstractAuthenticationToken> accessTokenConverter) throws Exception {
		http.cors(Customizer.withDefaults()).csrf(csrf -> csrf.disable())
				.authorizeHttpRequests(auth -> auth
						// DB tool endpoints are sensitive; require authenticated context in jwt-api mode.
						.requestMatchers("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html").permitAll()
						.anyRequest().authenticated())
				.oauth2ResourceServer(oauth2 -> oauth2.jwt(
						jwt -> jwt.decoder(jwtDecoder).jwtAuthenticationConverter(accessTokenConverter)));
		return http.build();
	}
}
