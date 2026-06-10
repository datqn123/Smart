import time
import jwt
import pytest
from app.harness.auth import verify_jwt, AuthError

SECRET = "test-secret"


def _token(claims, secret=SECRET):
    return jwt.encode(claims, secret, algorithm="HS256")


def test_valid_token_returns_claims():
    tok = _token({"sub": "user-1", "exp": int(time.time()) + 60})
    claims = verify_jwt(tok, secret=SECRET)
    assert claims["sub"] == "user-1"


def test_expired_token_rejected():  # fact-auth
    tok = _token({"sub": "u", "exp": int(time.time()) - 10})
    with pytest.raises(AuthError):
        verify_jwt(tok, secret=SECRET)


def test_bad_signature_rejected():  # fact-auth
    tok = _token({"sub": "u", "exp": int(time.time()) + 60}, secret="other")
    with pytest.raises(AuthError):
        verify_jwt(tok, secret=SECRET)


def test_dev_bypass_returns_synthetic_claims():
    claims = verify_jwt(None, secret=SECRET, dev_bypass=True)
    assert claims["sub"] == "dev-user"
