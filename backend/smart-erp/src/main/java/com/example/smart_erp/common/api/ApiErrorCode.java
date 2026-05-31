package com.example.smart_erp.common.api;

import org.springframework.http.HttpStatus;

/**
 * Machine-readable codes for JSON field {@code error}; must stay aligned with
 * {@code docs/frontend/api/API_RESPONSE_ENVELOPE.md}.
 */
public enum ApiErrorCode {
	BAD_REQUEST(HttpStatus.BAD_REQUEST),
	UNAUTHORIZED(HttpStatus.UNAUTHORIZED),
	FORBIDDEN(HttpStatus.FORBIDDEN),
	NOT_FOUND(HttpStatus.NOT_FOUND),
	CONFLICT(HttpStatus.CONFLICT),
	UNPROCESSABLE_ENTITY(HttpStatus.UNPROCESSABLE_ENTITY),
	TOO_MANY_REQUESTS(HttpStatus.TOO_MANY_REQUESTS),
	INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR);

	private final HttpStatus status;

	ApiErrorCode(HttpStatus status) {
		this.status = status;
	}

	public HttpStatus httpStatus() {
		return status;
	}

	/**
	 * Primitive status for {@link org.springframework.http.ResponseEntity#status(int)} — avoids
	 * nullness mismatch between {@link HttpStatus} and {@link org.springframework.http.HttpStatusCode}.
	 */
	public int statusCodeValue() {
		return status.value();
	}
}
