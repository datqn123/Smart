package com.example.smart_erp.auth.support;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Map;
import java.util.Optional;

import javax.crypto.SecretKey;

import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import com.example.smart_erp.common.api.ApiErrorCode;
import com.example.smart_erp.common.exception.BusinessException;
import com.example.smart_erp.config.AppSecurityProperties;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;

@Service
public class JwtTokenService {

	private final SecretKey signingKey;
	private final AppSecurityProperties.Jwt jwtProps;

	private final int accessTtlMinutes;

	public JwtTokenService(AppSecurityProperties props) {
		byte[] bytes = props.getJwt().getSecret().getBytes(StandardCharsets.UTF_8);
		if (bytes.length < 32) {
			throw new IllegalStateException(
					"app.security.jwt.secret (JWT_SECRET) must be UTF-8 with byte length >= 32 for HS256 (Task001).");
		}
		this.signingKey = Keys.hmacShaKeyFor(bytes);
		this.jwtProps = props.getJwt();
		int ttl = props.getJwt().getAccessTtlMinutes();
		this.accessTtlMinutes = ttl < 1 ? 1 : ttl;
	}

	/**
	 * @param rolePermissionsJson toàn bộ JSON {@code roles.permissions} (có thể rỗng) — rút subset menu (claim {@code mp})
	 */
	public String createAccessToken(int userId, String username, String roleName, String rolePermissionsJson) {
		Instant now = Instant.now();
		Instant exp = now.plusSeconds(accessTtlMinutes * 60L);
		Map<String, Boolean> menuPerms = MenuPermissionClaims.fromRolePermissionsJson(rolePermissionsJson);
		var builder = Jwts.builder()
				.subject(String.valueOf(userId))
				.claim("name", username)
				.claim("role", roleName)
				.claim(MenuPermissionClaims.CLAIM_NAME, menuPerms)
				.issuedAt(Date.from(now))
				.expiration(Date.from(exp))
				.signWith(signingKey);
		if (StringUtils.hasText(jwtProps.getIssuer())) {
			builder.issuer(jwtProps.getIssuer().trim());
		}
		if (StringUtils.hasText(jwtProps.getAudience())) {
			builder.claim("aud", jwtProps.getAudience().trim());
		}
		return builder.compact();
	}

	/** TTL access token (giây) theo cấu hình, dùng cho Redis login registry. */
	public long getAccessTtlSeconds() {
		return accessTtlMinutes * 60L;
	}

	/**
	 * Task002 logout — parse subject; lỗi → {@link BusinessException}{@code UNAUTHORIZED}.
	 */
	public int parseAccessTokenUserId(String compactJwt) {
		final String msg401 = "Phiên đăng nhập không hợp lệ hoặc đã hết hạn";
		Claims claims = tryParseActiveAccessClaims(compactJwt)
				.orElseThrow(() -> new BusinessException(ApiErrorCode.UNAUTHORIZED, msg401));
		try {
			return Integer.parseInt(claims.getSubject());
		}
		catch (NumberFormatException e) {
			throw new BusinessException(ApiErrorCode.UNAUTHORIZED, msg401);
		}
	}

	/**
	 * Parse + verify chữ ký + iss/aud + exp chưa qua (theo đồng hồ server).
	 */
	private Optional<Claims> tryParseActiveAccessClaims(String compactJwt) {
		if (!StringUtils.hasText(compactJwt)) {
			return Optional.empty();
		}
		try {
			Claims claims = Jwts.parser().verifyWith(signingKey).build().parseSignedClaims(compactJwt).getPayload();
			if (StringUtils.hasText(jwtProps.getIssuer())) {
				String iss = claims.getIssuer();
				if (iss == null || !jwtProps.getIssuer().trim().equals(iss)) {
					return Optional.empty();
				}
			}
			if (StringUtils.hasText(jwtProps.getAudience())) {
				String expected = jwtProps.getAudience().trim();
				Object aud = claims.get("aud");
				if (aud == null) {
					return Optional.empty();
				}
				if (aud instanceof String s) {
					if (!expected.equals(s)) {
						return Optional.empty();
					}
				}
				else if (aud instanceof java.util.Collection<?> col) {
					boolean ok = col.stream().anyMatch(o -> expected.equals(String.valueOf(o)));
					if (!ok) {
						return Optional.empty();
					}
				}
				else if (!expected.equals(String.valueOf(aud))) {
					return Optional.empty();
				}
			}
			Date exp = claims.getExpiration();
			if (exp == null || !exp.toInstant().isAfter(Instant.now())) {
				return Optional.empty();
			}
			return Optional.of(claims);
		}
		catch (JwtException | IllegalArgumentException e) {
			return Optional.empty();
		}
	}
}
