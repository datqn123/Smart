"""JWT validation for FastAPI trust boundary (Option B)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_JWT_ALGS = ("RS256", "RS384", "RS512", "ES256", "ES384", "ES512")


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    auth_dev_bypass: bool = Field(default=False)
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_jwks_url: str | None = None
    jwt_public_key_pem: str | None = None

    @property
    def crypto_configured(self) -> bool:
        return bool((self.jwt_jwks_url or "").strip() or (self.jwt_public_key_pem or "").strip())


@lru_cache(maxsize=1)
def load_auth_settings() -> AuthSettings:
    return AuthSettings()


class JwtValidator:
    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        self._jwks_client: jwt.PyJWKClient | None = None

    def validate_authorization_header(self, authorization: str | None) -> dict[str, Any]:
        if self._settings.auth_dev_bypass:
            return {"sub": "dev-bypass", "auth_dev_bypass": True}

        if not authorization or not authorization.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header.")
        if not self._settings.crypto_configured:
            raise ValueError("JWT validation crypto is not configured.")
        if not self._settings.jwt_issuer or not self._settings.jwt_audience:
            raise ValueError("JWT_ISSUER and JWT_AUDIENCE must be configured.")

        token = authorization[len("Bearer ") :].strip()
        if not token:
            raise ValueError("Bearer token is empty.")
        key = self._resolve_signing_key(token)
        return jwt.decode(
            token,
            key=key,
            algorithms=list(ALLOWED_JWT_ALGS),
            audience=self._settings.jwt_audience,
            issuer=self._settings.jwt_issuer,
        )

    def _resolve_signing_key(self, token: str) -> str | bytes | Any:
        if self._settings.jwt_public_key_pem:
            return self._settings.jwt_public_key_pem
        if not self._settings.jwt_jwks_url:
            raise ValueError("No JWT signing key source configured.")
        if self._jwks_client is None:
            self._jwks_client = jwt.PyJWKClient(self._settings.jwt_jwks_url)
        return self._jwks_client.get_signing_key_from_jwt(token).key


@lru_cache(maxsize=1)
def get_jwt_validator() -> JwtValidator:
    return JwtValidator(load_auth_settings())
