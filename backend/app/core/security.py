from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings

PASSWORD_ALGORITHM = "pbkdf2_sha256_v2"
LEGACY_PASSWORD_ALGORITHM = "pbkdf2_sha256"
API_KEY_HASH_PREFIX = "hmac_sha256:"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        _password_material(password),
        salt,
        settings.password_iterations,
    )
    return f"{PASSWORD_ALGORITHM}${settings.password_iterations}${_b64url(salt)}${_b64url(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    parsed = _parse_password_hash(password_hash)
    if parsed is None:
        return False
    algorithm, iterations, salt, expected = parsed
    material = _password_material(password) if algorithm == PASSWORD_ALGORITHM else password.encode("utf-8")
    actual = hashlib.pbkdf2_hmac("sha256", material, salt, iterations)
    return hmac.compare_digest(actual, expected)


def password_needs_rehash(password_hash: str) -> bool:
    parsed = _parse_password_hash(password_hash)
    if parsed is None:
        return True
    algorithm, iterations, _, _ = parsed
    return algorithm != PASSWORD_ALGORITHM or iterations < settings.password_iterations


def _password_material(password: str) -> bytes:
    if not settings.password_pepper:
        return password.encode("utf-8")
    return hmac.new(settings.password_pepper.encode("utf-8"), password.encode("utf-8"), hashlib.sha256).digest()


def _parse_password_hash(password_hash: str) -> tuple[str, int, bytes, bytes] | None:
    parts = password_hash.split("$")
    try:
        if len(parts) == 4 and parts[0] == PASSWORD_ALGORITHM:
            return parts[0], int(parts[1]), _b64url_decode(parts[2]), _b64url_decode(parts[3])
        if len(parts) == 3 and parts[0] == LEGACY_PASSWORD_ALGORITHM:
            return parts[0], 180_000, _b64url_decode(parts[1]), _b64url_decode(parts[2])
    except (ValueError, TypeError):
        return None
    return None


def _sign(message: str) -> str:
    digest = hmac.new(settings.secret_key.encode("utf-8"), message.encode("ascii"), hashlib.sha256).digest()
    return _b64url(digest)


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    encoded_header = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    return f"{signing_input}.{_sign(signing_input)}"


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any] | None:
    try:
        encoded_header, encoded_payload, signature = token.split(".", 2)
    except ValueError:
        return None
    signing_input = f"{encoded_header}.{encoded_payload}"
    if not hmac.compare_digest(_sign(signing_input), signature):
        return None
    try:
        payload = json.loads(_b64url_decode(encoded_payload))
    except json.JSONDecodeError:
        return None
    if payload.get("type") != expected_type:
        return None
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        return None
    return payload


def create_access_token(user_id: str) -> str:
    return create_token(user_id, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: str) -> str:
    return create_token(user_id, "refresh", timedelta(days=settings.refresh_token_days))


def generate_api_key() -> tuple[str, str, str]:
    raw = "mt_live_" + secrets.token_urlsafe(32)
    prefix = raw[:16]
    key_hash = hash_api_key(raw)
    return raw, prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    secret = settings.api_key_hash_secret or settings.secret_key
    digest = hmac.new(secret.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{API_KEY_HASH_PREFIX}{digest}"


def legacy_hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
