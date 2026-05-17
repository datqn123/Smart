package com.example.smart_erp.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Security toggles for auth development. See {@code application.properties}.
 */
@ConfigurationProperties(prefix = "app.security")
public class AppSecurityProperties {

	/**
	 * {@code permit-all}: mọi request mở (dev). {@code jwt-api}: OAuth2 Resource Server + Bearer JWT.
	 */
	private String apiProtection = "permit-all";

	/**
	 * JWT signing / validation (HS256). Required length when using {@code api-protection=jwt-api}:
	 * UTF-8 byte length ≥ 32 (see {@code io.jsonwebtoken.security.Keys#hmacShaKeyFor}).
	 */
	private Jwt jwt = new Jwt();

	public String getApiProtection() {
		return apiProtection;
	}

	public void setApiProtection(String apiProtection) {
		this.apiProtection = apiProtection != null ? apiProtection : "permit-all";
	}

	public Jwt getJwt() {
		return jwt;
	}

	public void setJwt(Jwt jwt) {
		this.jwt = jwt;
	}

	public static class Jwt {

		/**
		 * Symmetric secret; use env {@code JWT_SECRET} in real deployments.
		 */
		private String secret = "";

		/**
		 * Optional JWT {@code iss} (issuer) — URL hoặc id dịch vụ phát hành token.
		 */
		private String issuer = "";

		/**
		 * Optional JWT {@code aud} (audience) — api nào được phép dùng token này.
		 */
		private String audience = "";

		/**
		 * Thời gian sống access JWT (phút), tối thiểu 1. Mặc định 30. Env
		 * {@code JWT_ACCESS_TTL_MINUTES} / property ghi đè khi deploy.
		 */
		private int accessTtlMinutes = 30;

		public String getSecret() {
			return secret;
		}

		public void setSecret(String secret) {
			this.secret = secret != null ? secret : "";
		}

		public String getIssuer() {
			return issuer;
		}

		public void setIssuer(String issuer) {
			this.issuer = issuer != null ? issuer : "";
		}

		public String getAudience() {
			return audience;
		}

		public void setAudience(String audience) {
			this.audience = audience != null ? audience : "";
		}

		public int getAccessTtlMinutes() {
			return accessTtlMinutes;
		}

		public void setAccessTtlMinutes(int accessTtlMinutes) {
			this.accessTtlMinutes = accessTtlMinutes;
		}
	}
}
