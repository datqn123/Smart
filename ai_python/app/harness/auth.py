from __future__ import annotations
import jwt


class AuthError(Exception):
    """Request khong xac thuc duoc -> bi tu choi, KHONG vao pipeline."""


def verify_jwt(token: str | None, *, secret: str, issuer: str = "",
               audience: str = "", dev_bypass: bool = False) -> dict:
    if dev_bypass:
        return {"sub": "dev-user", "dev_bypass": True}
    if not token:
        raise AuthError("missing token")
    options = {"verify_aud": bool(audience)}
    try:
        claims = jwt.decode(
            token, secret, algorithms=["HS256"],
            audience=audience or None,
            issuer=issuer or None,
            options=options,
        )
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc)) from exc
    if "sub" not in claims:
        raise AuthError("token missing sub")
    return claims
