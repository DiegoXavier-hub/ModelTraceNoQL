from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_store
from app.core.config import settings
from app.core.privacy import (
    mask_email,
    protect_display_name,
    protect_email,
    protect_entity_id,
    redact_sensitive,
    user_email,
)
from app.db.document_store import DocumentStore

router = APIRouter(prefix="/security", tags=["security"])


def _check(check_id: str, label: str, status_: str, detail: str, severity: str = "info") -> dict:
    return {"id": check_id, "label": label, "status": status_, "severity": severity, "detail": detail}


@router.get("/posture")
async def security_posture(user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    user_count = await store.count("users", {"org_id": user["org_id"]})
    protected_users = await store.count("users", {"org_id": user["org_id"], "email_encrypted": {"$exists": True}})
    api_keys = await store.find_many("api_keys", {"org_id": user["org_id"]}, limit=0)
    hmac_keys = sum(1 for item in api_keys if str(item.get("key_hash", "")).startswith("hmac_sha256:"))

    checks = [
        _check(
            "field_encryption",
            "Criptografia de PII em repouso",
            "configured" if settings.field_encryption_key else "derived",
            "Chave dedicada configurada."
            if settings.field_encryption_key
            else "Chave dedicada ausente; usando derivacao de SECRET_KEY.",
            "ok" if settings.field_encryption_key else "warning",
        ),
        _check(
            "pii_blind_index",
            "Busca segura por e-mail e entidade",
            "configured" if settings.pii_hash_key else "derived",
            "Chave dedicada configurada."
            if settings.pii_hash_key
            else "Chave dedicada ausente; indices usam derivacao de SECRET_KEY.",
            "ok" if settings.pii_hash_key else "warning",
        ),
        _check(
            "password_hashing",
            "Hashing de senhas",
            "active",
            f"PBKDF2-SHA256 versionado, {settings.password_iterations:,} iteracoes.",
            "ok",
        ),
        _check(
            "api_key_hashing",
            "API keys em HMAC",
            "active" if hmac_keys == len(api_keys) else "partial",
            f"{hmac_keys}/{len(api_keys)} chaves em HMAC-SHA256.",
            "ok" if hmac_keys == len(api_keys) else "warning",
        ),
        _check(
            "secret_key",
            "SECRET_KEY forte",
            "default" if settings.uses_default_secret else "configured",
            "Valor de desenvolvimento ativo." if settings.uses_default_secret else "Chave configurada por ambiente.",
            "critical" if settings.uses_default_secret and settings.is_production else "warning" if settings.uses_default_secret else "ok",
        ),
        _check(
            "security_headers",
            "Headers de seguranca",
            "enabled" if settings.enable_security_headers else "disabled",
            "Headers de hardening ativos nas rotas de API.",
            "ok" if settings.enable_security_headers else "warning",
        ),
        _check(
            "protected_users",
            "Usuarios migrados",
            "complete" if protected_users == user_count else "partial",
            f"{protected_users}/{user_count} usuarios com e-mail protegido.",
            "ok" if protected_users == user_count else "warning",
        ),
    ]

    return {
        "environment": settings.environment,
        "store": "mongo" if settings.mongodb_url else "json",
        "org_id": user["org_id"],
        "checks": checks,
        "recommendations": [
            "Separe FIELD_ENCRYPTION_KEY, PII_HASH_KEY, PASSWORD_PEPPER e API_KEY_HASH_SECRET.",
            "Ative TLS no proxy e COOKIE_SECURE=true em producao.",
            "Rotacione API keys legadas.",
            "Mantenha redact_pii=true nas exportacoes padrao.",
        ],
    }


@router.post("/migrate-sensitive-data")
async def migrate_sensitive_data(user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    if user.get("role") not in {"OWNER", "ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can run security migrations")

    counts = {
        "users": 0,
        "projects": 0,
        "predictions": 0,
        "audit_events": 0,
        "intervention_cases": 0,
        "legacy_api_keys_requiring_rotation": 0,
    }

    def migrate_user(item: dict) -> dict | None:
        email = user_email(item)
        if not email:
            return None
        if not item.get("email_encrypted") or not item.get("email_hash") or "@" in str(item.get("email", "")):
            return {"$set": protect_email(email)}
        return None

    counts["users"] = await store.transform_many("users", {"org_id": user["org_id"]}, migrate_user)

    def migrate_project(project: dict) -> dict | None:
        settings_doc = project.get("settings", {})
        alert_email = settings_doc.get("alert_email")
        if isinstance(alert_email, str) and "@" in alert_email:
            return {
                "$set": {
                    "settings.alert_email": mask_email(alert_email),
                    "settings.alert_email_hash": protect_email(alert_email)["email_hash"],
                }
            }
        return None

    counts["projects"] = await store.transform_many("projects", {"org_id": user["org_id"]}, migrate_project)

    def migrate_prediction(prediction: dict) -> dict | None:
        entity = prediction.get("entity", {})
        updates = {}
        entity_id = entity.get("id")
        if entity_id and not entity.get("id_encrypted"):
            protected_id = protect_entity_id(str(entity_id))
            updates.update({f"entity.{key}": value for key, value in protected_id.items()})
        display_name = entity.get("display_name")
        if display_name and display_name != "[protected]" and not entity.get("display_name_encrypted"):
            protected_name = protect_display_name(str(display_name))
            updates.update({f"entity.{key}": value for key, value in protected_name.items()})
        if updates:
            return {"$set": updates}
        return None

    counts["predictions"] = await store.transform_many("predictions", {"org_id": user["org_id"]}, migrate_prediction)

    def migrate_audit_event(event: dict) -> dict | None:
        updates = {
            "actor": redact_sensitive(event.get("actor", {})),
            "diff": redact_sensitive(event.get("diff", {})),
            "context": redact_sensitive(event.get("context", {})),
        }
        if (
            updates["actor"] != event.get("actor", {})
            or updates["diff"] != event.get("diff", {})
            or updates["context"] != event.get("context", {})
        ):
            return {"$set": updates}
        return None

    counts["audit_events"] = await store.transform_many("audit_events", {"org_id": user["org_id"]}, migrate_audit_event)

    def migrate_case(case: dict) -> dict | None:
        timeline = case.get("timeline")
        if timeline:
            redacted = redact_sensitive(timeline)
            if redacted != timeline:
                return {"$set": {"timeline": redacted}}
        return None

    counts["intervention_cases"] = await store.transform_many(
        "intervention_cases",
        {"org_id": user["org_id"]},
        migrate_case,
    )

    api_keys = await store.find_many("api_keys", {"org_id": user["org_id"]}, limit=0)
    counts["legacy_api_keys_requiring_rotation"] = sum(
        1 for item in api_keys if not str(item.get("key_hash", "")).startswith("hmac_sha256:")
    )

    return {
        "status": "completed",
        "counts": counts,
        "notes": "API keys legadas exigem uso assistido ou rotacao para migrar o hash.",
    }
