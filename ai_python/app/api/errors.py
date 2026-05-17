"""Canonical API error envelopes for Task004."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import ErrorEnvelope, ErrorObject


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.correlation_id = correlation_id


def _request_correlation_id(request: Request) -> str | None:
    return request.headers.get("x-correlation-id")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        body = ErrorEnvelope(
            correlation_id=exc.correlation_id or _request_correlation_id(request),
            error=ErrorObject(code=exc.code, message=exc.message, details=exc.details),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        body = ErrorEnvelope(
            correlation_id=_request_correlation_id(request),
            error=ErrorObject(
                code="AI_VALIDATION_FAILED",
                message="Request validation failed.",
                details={"errors": exc.errors()},
            ),
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        details = exc.detail if isinstance(exc.detail, dict) else None
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        body = ErrorEnvelope(
            correlation_id=_request_correlation_id(request),
            error=ErrorObject(
                code="AI_HTTP_ERROR",
                message=message,
                details=details,
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())
