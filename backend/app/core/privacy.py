from __future__ import annotations

import base64
import copy
import hashlib
import hmac
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import settings

ENCRYPTED_PREFIX = "enc:v1:"
HASH_PREFIX = "hmac_sha256:"
_FERNET: Fernet | None = None

_SECRET_KEYWORDS = {
    "access_token",
    "refresh_token",
    "token",
    "password",
    "password_hash",
    "secret",
    "api_key",
    "key_hash",
    "authorization",
    "cookie",
}
_PII_KEYWORDS = {"email", "display_name", "entity_display_name"}


def _purpose_key(purpose: str) -> bytes:
    seed = settings.pii_hash_key or settings.secret_key
    return f"{seed}:{purpose}".encode("utf-8")


def _fernet_key() -> bytes:
    seed = settings.field_encryption_key or settings.secret_key
    derived = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"modeltrace-field-encryption-v1",
        info=b"fernet",
    ).derive(seed.encode("utf-8"))
    return base64.urlsafe_b64encode(derived)


def _fernet() -> Fernet:
    global _FERNET
    if _FERNET is None:
        _FERNET = Fernet(_fernet_key())
    return _FERNET


def normalize_email(email: str) -> str:
    return email.strip().lower()


def encrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    if value.startswith(ENCRYPTED_PREFIX):
        return value
    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.startswith(ENCRYPTED_PREFIX):
        return value
    token = value.removeprefix(ENCRYPTED_PREFIX)
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


def blind_index(value: str | None, purpose: str) -> str | None:
    if value is None:
        return None
    normalized = normalize_email(value) if purpose == "email" else value.strip()
    digest = hmac.new(_purpose_key(purpose), normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{HASH_PREFIX}{digest}"


def mask_email(email: str | None) -> str | None:
    if not email:
        return None
    if "@" not in email:
        return "[protected]"
    local, domain = email.split("@", 1)
    if not local:
        return f"***@{domain}"
    visible = local[:1]
    return f"{visible}***@{domain}"


def protect_email(email: str) -> dict[str, str | None]:
    normalized = normalize_email(email)
    return {
        "email": mask_email(normalized),
        "email_masked": mask_email(normalized),
        "email_encrypted": encrypt_text(normalized),
        "email_hash": blind_index(normalized, "email"),
    }


def user_email(user: dict[str, Any]) -> str | None:
    decrypted = decrypt_text(user.get("email_encrypted"))
    if decrypted:
        return decrypted
    raw = user.get("email")
    if isinstance(raw, str) and not raw.startswith(ENCRYPTED_PREFIX) and "[protected]" not in raw:
        return raw
    return user.get("email_masked")


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    output = {
        key: value
        for key, value in user.items()
        if key
        not in {
            "password_hash",
            "email_hash",
            "email_encrypted",
            "security_events",
            "avatar_path",
        }
    }
    email = user_email(user)
    if email:
        output["email"] = email
        output["email_masked"] = mask_email(email)
    return output


def audit_actor_for_user(user: dict[str, Any]) -> dict[str, Any]:
    email = user_email(user)
    return {
        "type": "user",
        "id": user.get("_id"),
        "email_hash": user.get("email_hash") or blind_index(email, "email"),
        "email_masked": user.get("email_masked") or mask_email(email),
    }


def audit_actor_for_api_key(api_key: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "api_key",
        "id": api_key.get("_id"),
        "prefix": api_key.get("prefix"),
    }


def protect_display_name(value: str | None) -> dict[str, str | None]:
    if not value:
        return {"display_name": None, "display_name_encrypted": None, "display_name_masked": None}
    return {
        "display_name": "[protected]",
        "display_name_encrypted": encrypt_text(value),
        "display_name_masked": "[protected]",
    }


def protect_entity_id(value: str) -> dict[str, str | None]:
    hashed = blind_index(value, "entity")
    suffix = (hashed or "").removeprefix(HASH_PREFIX)[:12]
    return {
        "id": f"entity_{suffix}" if suffix else "[protected]",
        "id_hash": hashed,
        "id_encrypted": encrypt_text(value),
    }


def reveal_entity(entity: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(entity, dict):
        return {}
    output = {
        key: value
        for key, value in entity.items()
        if key not in {"id_encrypted", "display_name_encrypted", "display_name_masked"}
    }
    decrypted_id = decrypt_text(entity.get("id_encrypted"))
    stored_id = entity.get("id")
    if decrypted_id:
        output["id"] = decrypted_id
        output["id_masked"] = stored_id
    elif stored_id and stored_id != "[protected]":
        output["id"] = stored_id
    else:
        output.pop("id", None)

    decrypted_display = decrypt_text(entity.get("display_name_encrypted"))
    stored_display = entity.get("display_name")
    if decrypted_display:
        output["display_name"] = decrypted_display
    elif stored_display and stored_display != "[protected]":
        output["display_name"] = stored_display
    elif output.get("id"):
        output["display_name"] = output["id"]
    return output


def reveal_prediction_for_user(item: dict[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(item)
    output["entity"] = reveal_entity(output.get("entity"))
    return output


def reveal_predictions_for_user(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [reveal_prediction_for_user(item) for item in items]


def reveal_dashboard_for_user(dashboard: dict[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(dashboard)
    output["latest_critical"] = reveal_predictions_for_user(output.get("latest_critical") or [])
    return output


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if not isinstance(value, dict):
        return value

    redacted: dict[str, Any] = {}
    for key, item in value.items():
        lowered = key.lower()
        if lowered.endswith("_encrypted"):
            redacted[key] = "[redacted]"
        elif any(secret in lowered for secret in _SECRET_KEYWORDS):
            redacted[key] = "[redacted]"
        elif lowered in {"email_hash", "actor_email_hash"}:
            redacted[key] = item
        elif any(pii in lowered for pii in _PII_KEYWORDS):
            if "email" in lowered and isinstance(item, str):
                redacted[key] = mask_email(item)
            else:
                redacted[key] = "[protected]" if item is not None else None
        else:
            redacted[key] = redact_sensitive(item)
    return redacted


def redact_prediction_for_export(item: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_sensitive(item)
    entity = redacted.get("entity")
    if isinstance(entity, dict):
        raw_id = item.get("entity", {}).get("id")
        entity["id_hash"] = blind_index(str(raw_id), "entity") if raw_id is not None else None
        entity.pop("id", None)
    return redacted
