"""JWT validation for FastAPI trust boundary (Option B)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import jwt
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_JWT_ALGS = ("RS256", "RS384", "RS512", "ES256", "ES384", "ES512")
USER_ID_CLAIM_KEYS = ("user_id", "uid", "sub")
TENANT_ID_CLAIM_KEYS = ("tenant_id", "tenant", "tid", "tenantId")
ROLE_CLAIM_KEYS = ("role", "roles", "authority", "authorities")
# JWT claim keys that may carry live permission flags. Spring embeds menu
# permissions as the ``mp`` claim (see ERP guide 02_permissions).
PERMISSION_CLAIM_KEYS = ("mp", "permissions", "perms", "scope", "scopes")

# AI capability tokens implied by a privileged live role. The role is itself a
# validated JWT claim, so this is the live source of truth (SRS-006 FR-5.4) — not
# an advisory K6 mapping. Unprivileged roles must be granted via explicit flags.
_ROLE_IMPLIED_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "owner": ("draft_create", "data_read"),
    "admin": ("draft_create", "data_read"),
}


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
    jwt_hs256_secret: SecretStr | None = Field(
        default=None,
        description="Shared secret for HS256 (same as Spring app.security.jwt.secret).",
    )

    @property
    def crypto_configured(self) -> bool:
        if self.jwt_hs256_secret and self.jwt_hs256_secret.get_secret_value().strip():
            return True
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

        token = authorization[len("Bearer ") :].strip()
        if not token:
            raise ValueError("Bearer token is empty.")

        hs256 = self._settings.jwt_hs256_secret
        if hs256 and hs256.get_secret_value().strip():
            return self._decode_hs256(token, secret=hs256.get_secret_value())

        if not self._settings.jwt_issuer or not self._settings.jwt_audience:
            raise ValueError("JWT_ISSUER and JWT_AUDIENCE must be configured for asymmetric JWT validation.")

        key = self._resolve_signing_key(token)
        return jwt.decode(
            token,
            key=key,
            algorithms=list(ALLOWED_JWT_ALGS),
            audience=self._settings.jwt_audience,
            issuer=self._settings.jwt_issuer,
        )

    def _decode_hs256(self, token: str, *, secret: str) -> dict[str, Any]:
        opts: dict[str, bool] = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_aud": bool((self._settings.jwt_audience or "").strip()),
            "verify_iss": bool((self._settings.jwt_issuer or "").strip()),
        }
        decode_kw: dict[str, Any] = {
            "algorithms": ["HS256"],
            "options": opts,
        }
        if opts["verify_aud"]:
            decode_kw["audience"] = (self._settings.jwt_audience or "").strip()
        if opts["verify_iss"]:
            decode_kw["issuer"] = (self._settings.jwt_issuer or "").strip()
        return jwt.decode(token, secret, **decode_kw)

    def _resolve_signing_key(self, token: str) -> str | bytes | Any:
        if self._settings.jwt_public_key_pem:
            return self._settings.jwt_public_key_pem
        if not self._settings.jwt_jwks_url:
            raise ValueError("No JWT signing key source configured.")
        if self._jwks_client is None:
            self._jwks_client = jwt.PyJWKClient(self._settings.jwt_jwks_url)
        return self._jwks_client.get_signing_key_from_jwt(token).key


def _read_claim(claims: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = claims.get(key)
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        elif value is not None:
            normalized = str(value).strip()
            if normalized:
                return normalized
    return None


def derive_identity_context(claims: dict[str, Any]) -> tuple[str, str]:
    user_id = _read_claim(claims, USER_ID_CLAIM_KEYS)
    tenant_id = _read_claim(claims, TENANT_ID_CLAIM_KEYS)
    missing: list[str] = []
    if not user_id:
        missing.append("user_id")
    if not tenant_id:
        missing.append("tenant_id")
    if missing:
        raise ValueError(f"JWT claims missing required identity: {', '.join(missing)}.")
    return user_id, tenant_id


def _coerce_permission_flags(value: Any) -> set[str]:
    """Normalize a permission claim (str / list / dict-of-bool) into flag strings."""
    flags: set[str] = set()
    if value is None:
        return flags
    if isinstance(value, str):
        for part in re.split(r"[\s,]+", value):
            token = part.strip()
            if token:
                flags.add(token)
    elif isinstance(value, dict):
        for key, enabled in value.items():
            if enabled:
                token = str(key).strip()
                if token:
                    flags.add(token)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            token = str(item).strip()
            if token:
                flags.add(token)
    return flags


def derive_role_permissions(claims: dict[str, Any]) -> tuple[str | None, tuple[str, ...]]:
    """Extract the live role and permission set from validated JWT claims.

    This is server-authoritative: callers must overwrite any client-supplied
    role/permissions with this result. Missing claims yield ``(None, ())`` so
    protected tools fail closed (FR-5.4).
    """
    role = _read_claim(claims, ROLE_CLAIM_KEYS)
    perms: set[str] = set()
    for key in PERMISSION_CLAIM_KEYS:
        perms |= _coerce_permission_flags(claims.get(key))
    if role:
        perms |= set(_ROLE_IMPLIED_CAPABILITIES.get(role.strip().lower(), ()))
    return role, tuple(sorted(perms))


@lru_cache(maxsize=1)
def get_jwt_validator() -> JwtValidator:
    return JwtValidator(load_auth_settings())
