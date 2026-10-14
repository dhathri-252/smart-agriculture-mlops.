"""Authentication primitives using only the Python standard library.

- Passwords: PBKDF2-HMAC-SHA256 with a random per-user salt (never stored in
  plain text, never hard-coded).
- Session tokens: compact HMAC-SHA256 signed tokens (JWT-like structure) so
  no third-party dependency is required. Secrets come from the environment
  (see api/config.get_auth_secret).
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional

from api.config import get_auth_secret, get_token_ttl_seconds

PBKDF2_ITERATIONS = 390_000
_ALGO = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    """Return an encoded salt+hash string. Salt is random per password."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{_ALGO}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification of a password against a stored hash."""
    try:
        algo, iterations_s, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    if not isinstance(password, str):
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(
    claims: dict,
    secret: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
) -> str:
    """Create a signed token: base64url(header).base64url(payload).signature."""
    secret = secret or get_auth_secret()
    ttl = ttl_seconds if ttl_seconds is not None else get_token_ttl_seconds()
    now = int(time.time())
    header = {"alg": "HS256", "typ": "SAT"}
    payload = dict(claims)
    payload.setdefault("iat", now)
    payload["exp"] = now + ttl
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode("ascii")
    signature = _b64url(
        hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )
    return f"{h}.{p}.{signature}"


def decode_token(token: str, secret: Optional[str] = None) -> Optional[dict]:
    """Verify signature + expiry; return claims or None if invalid."""
    if not token or token.count(".") != 2:
        return None
    secret = secret or get_auth_secret()
    h, p, signature = token.split(".")
    signing_input = f"{h}.{p}".encode("ascii")
    expected = _b64url(
        hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(_b64url_decode(p))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None
