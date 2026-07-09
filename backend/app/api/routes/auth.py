from __future__ import annotations

import base64
import binascii
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_current_user, get_store
from app.core.config import settings
from app.core.password_policy import password_strength_errors
from app.core.privacy import (
    audit_actor_for_user,
    blind_index,
    normalize_email,
    protect_email,
    public_user,
    user_email,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    password_needs_rehash,
    verify_password,
    verify_token,
)
from app.core.utils import make_id, slugify, utcnow
from app.db.document_store import DocumentStore, JsonDocumentStore
from app.schemas import (
    AvatarUploadPayload,
    EmailTokenPayload,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    UserCreate,
)
from app.services.audit import create_audit_event
from app.services.email import send_transactional_email

router = APIRouter(prefix="/auth", tags=["auth"])

AVATAR_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _tokens(user_id: str) -> dict:
    return {"access_token": create_access_token(user_id), "refresh_token": create_refresh_token(user_id), "token_type": "bearer"}


def _persist_login_metadata(store: DocumentStore) -> bool:
    # The local JSON store can be hundreds of MB in this project. Persisting a
    # login timestamp/audit event rewrites the full file and makes login feel
    # frozen. MongoDB keeps the full audit path because updates are incremental.
    return not isinstance(store, JsonDocumentStore)


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _token_hash(token: str) -> str:
    hashed = blind_index(token, "email_token")
    if not hashed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    return hashed


def _app_link(path: str, token_name: str, token: str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{settings.public_app_url}{path}{separator}{token_name}={token}"


def _email_html(title: str, body: str, action_label: str, url: str) -> str:
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;line-height:1.5;color:#0f172a">
      <h1 style="font-size:22px">{title}</h1>
      <p>{body}</p>
      <p><a href="{url}" style="display:inline-block;background:#00c8ef;color:#00111a;padding:12px 18px;border-radius:8px;font-weight:700;text-decoration:none">{action_label}</a></p>
      <p style="font-size:13px;color:#64748b">Se o botão não abrir, copie e cole este link no navegador:<br>{url}</p>
    </div>
    """.strip()


def _safe_send_email(to_email: str, subject: str, text: str, html: str | None = None) -> dict:
    try:
        return send_transactional_email(to_email, subject, text, html)
    except Exception as exc:  # pragma: no cover - depends on external SMTP
        return {"status": "failed", "transport": "smtp", "error": str(exc)}


async def _create_email_token(store: DocumentStore, user: dict, purpose: str, expires_minutes: int) -> str:
    token = secrets.token_urlsafe(40)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    document = {
        "_id": make_id("mailtok"),
        "org_id": user["org_id"],
        "user_id": user["_id"],
        "purpose": purpose,
        "token_hash": _token_hash(token),
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(minutes=expires_minutes)).isoformat().replace("+00:00", "Z"),
        "used_at": None,
        "status": "active",
    }
    await store.insert_one("email_tokens", document)
    return token


async def _consume_email_token(store: DocumentStore, purpose: str, token: str, *, mark_used: bool = True) -> dict:
    document = await store.find_one("email_tokens", {"token_hash": _token_hash(token), "purpose": purpose})
    now = datetime.now(timezone.utc)
    expires_at = _parse_utc((document or {}).get("expires_at"))
    if not document or document.get("used_at") or document.get("status") != "active" or not expires_at or expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    if mark_used:
        used_at = utcnow()
        await store.update_one(
            "email_tokens",
            {"_id": document["_id"]},
            {"$set": {"used_at": used_at, "status": "used"}},
        )
        document["used_at"] = used_at
        document["status"] = "used"
    return document


async def _send_verification_email(store: DocumentStore, user: dict) -> dict:
    email = user_email(user)
    if not email:
        return {"status": "skipped", "reason": "missing_email"}
    token = await _create_email_token(store, user, "email_verification", settings.email_verification_minutes)
    url = _app_link("/", "verify_email_token", token)
    subject = "Confirme seu email no ModelTrace"
    text = (
        f"Olá, {user.get('name', 'usuário')}.\n\n"
        "Confirme seu email para ativar todos os recursos da sua conta ModelTrace.\n\n"
        f"{url}\n\n"
        "Se você não criou esta conta, ignore esta mensagem."
    )
    html = _email_html(
        "Confirme seu email",
        "Confirme seu endereço para concluir a configuração da sua conta ModelTrace.",
        "Confirmar email",
        url,
    )
    return _safe_send_email(email, subject, text, html)


async def _send_password_reset_email(store: DocumentStore, user: dict) -> dict:
    email = user_email(user)
    if not email:
        return {"status": "skipped", "reason": "missing_email"}
    token = await _create_email_token(store, user, "password_reset", settings.password_reset_minutes)
    url = _app_link("/", "reset_token", token)
    subject = "Redefinição de senha do ModelTrace"
    text = (
        f"Olá, {user.get('name', 'usuário')}.\n\n"
        "Use o link abaixo para redefinir sua senha. O link expira em alguns minutos.\n\n"
        f"{url}\n\n"
        "Se você não solicitou a redefinição, ignore esta mensagem."
    )
    html = _email_html(
        "Redefinição de senha",
        "Use este link para criar uma nova senha de acesso ao ModelTrace.",
        "Redefinir senha",
        url,
    )
    return _safe_send_email(email, subject, text, html)


def _set_auth_cookies(response: Response, tokens: dict) -> None:
    response.set_cookie(
        "modeltrace_access",
        tokens["access_token"],
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    response.set_cookie(
        "modeltrace_refresh",
        tokens["refresh_token"],
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("modeltrace_access", path="/")
    response.delete_cookie("modeltrace_refresh", path="/")


@router.post("/register", status_code=201)
async def register(payload: UserCreate, response: Response, store: DocumentStore = Depends(get_store)) -> dict:
    email = normalize_email(str(payload.email))
    email_hash = blind_index(email, "email")
    existing = await store.find_one("users", {"email_hash": email_hash}) or await store.find_one("users", {"email": email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    org_id = make_id("org")
    user_id = make_id("user")
    org = {
        "_id": org_id,
        "name": payload.organization_name or f"{payload.name}'s Organization",
        "slug": slugify(payload.organization_name or payload.name),
        "plan": "product",
        "owner_id": user_id,
        "settings": {
            "max_projects": 20,
            "max_predictions_per_day": 100000,
            "retention_days": 730,
            "enable_bias_analysis": True,
            "enable_webhooks": True,
        },
        "created_at": utcnow(),
        "status": "active",
    }
    user = {
        "_id": user_id,
        "org_id": org_id,
        "name": payload.name,
        **protect_email(email),
        "password_hash": hash_password(payload.password),
        "role": "OWNER",
        "job_title": payload.job_title,
        "department": payload.department,
        "company": payload.company,
        "phone": payload.phone,
        "timezone": payload.timezone or "America/Sao_Paulo",
        "bio": payload.bio,
        "avatar_url": None,
        "avatar_content_type": None,
        "avatar_updated_at": None,
        "email_verified": False,
        "email_verified_at": None,
        "project_permissions": {},
        "preferences": {"theme": "dark", "default_project": None, "email_alerts": True, "locale": "pt-BR"},
        "created_at": utcnow(),
        "last_login_at": None,
        "status": "active"
    }
    await store.insert_one("organizations", org)
    await store.insert_one("users", user)
    await create_audit_event(
        store,
        org_id=org_id,
        project_id=None,
        actor=audit_actor_for_user(user),
        event_type="auth.registered",
        resource_type="user",
        resource_id=user_id,
    )
    email_delivery = await _send_verification_email(store, user)
    tokens = _tokens(user_id)
    _set_auth_cookies(response, tokens)
    return {"user": public_user(user), "email_delivery": email_delivery, **tokens}


@router.post("/login")
async def login(payload: LoginRequest, response: Response, store: DocumentStore = Depends(get_store)) -> dict:
    email = normalize_email(str(payload.email))
    email_hash = blind_index(email, "email")
    user = await store.find_one("users", {"email_hash": email_hash, "status": "active"})
    if not user:
        user = await store.find_one("users", {"email": email, "status": "active"})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    persist_login_metadata = _persist_login_metadata(store)
    updates = {"last_login_at": utcnow()} if persist_login_metadata else {}
    if password_needs_rehash(user.get("password_hash", "")):
        updates["password_hash"] = hash_password(payload.password)
    if not user.get("email_encrypted") or not user.get("email_hash"):
        updates.update(protect_email(email))
    if updates:
        await store.update_one("users", {"_id": user["_id"]}, {"$set": updates})
        user.update(updates)
    user["last_login_at"] = datetime.utcnow().isoformat()
    if persist_login_metadata:
        await create_audit_event(
            store,
            org_id=user["org_id"],
            project_id=None,
            actor=audit_actor_for_user(user),
            event_type="auth.login",
            resource_type="user",
            resource_id=user["_id"],
        )
    tokens = _tokens(user["_id"])
    _set_auth_cookies(response, tokens)
    return {"user": public_user(user), **tokens}


@router.post("/refresh")
async def refresh(request: Request, response: Response, payload: dict | None = None) -> dict:
    token = (payload or {}).get("refresh_token") or request.cookies.get("modeltrace_refresh")
    decoded = verify_token(token, "refresh") if token else None
    if not decoded:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    tokens = _tokens(decoded["sub"])
    _set_auth_cookies(response, tokens)
    return tokens


@router.post("/logout")
async def logout(response: Response) -> dict:
    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.post("/resend-verification")
async def resend_verification(user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    if user.get("email_verified"):
        return {"status": "already_verified", "email_verified": True}
    delivery = await _send_verification_email(store, user)
    return {"status": "queued", "email_verified": False, "email_delivery": delivery}


@router.post("/verify-email")
async def verify_email(payload: EmailTokenPayload, store: DocumentStore = Depends(get_store)) -> dict:
    token_document = await _consume_email_token(store, "email_verification", payload.token)
    user = await store.find_one("users", {"_id": token_document["user_id"], "status": "active"})
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    updates = {"email_verified": True, "email_verified_at": utcnow()}
    await store.update_one("users", {"_id": user["_id"]}, {"$set": updates})
    user.update(updates)
    return {"status": "verified", "user": public_user(user)}


@router.post("/password-reset/request")
async def request_password_reset(payload: PasswordResetRequest, store: DocumentStore = Depends(get_store)) -> dict:
    email = normalize_email(str(payload.email))
    email_hash = blind_index(email, "email")
    user = await store.find_one("users", {"email_hash": email_hash, "status": "active"})
    if not user:
        user = await store.find_one("users", {"email": email, "status": "active"})
    delivery = await _send_password_reset_email(store, user) if user else {"status": "skipped"}
    return {"status": "accepted", "email_delivery": delivery if settings.environment != "production" else {"status": "accepted"}}


@router.post("/password-reset/confirm")
async def confirm_password_reset(payload: PasswordResetConfirm, store: DocumentStore = Depends(get_store)) -> dict:
    token_document = await _consume_email_token(store, "password_reset", payload.token, mark_used=False)
    user = await store.find_one("users", {"_id": token_document["user_id"], "status": "active"})
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    errors = password_strength_errors(payload.new_password, email=user_email(user), name=user.get("name"))
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Password does not meet security policy: {', '.join(errors)}",
        )
    await store.update_one("users", {"_id": user["_id"]}, {"$set": {"password_hash": hash_password(payload.new_password)}})
    await store.update_one(
        "email_tokens",
        {"_id": token_document["_id"]},
        {"$set": {"used_at": utcnow(), "status": "used"}},
    )
    return {"status": "password_updated"}


@router.patch("/me")
async def update_me(
    payload: ProfileUpdate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    data = payload.model_dump(exclude_unset=True)
    updates: dict = {}
    email_delivery: dict | None = None

    if "email" in data and data["email"] is not None:
        email = normalize_email(str(data.pop("email")))
        current_email = normalize_email(user_email(user) or "")
        if email != current_email:
            email_hash = blind_index(email, "email")
            existing = await store.find_one("users", {"email_hash": email_hash})
            if existing and existing.get("_id") != user["_id"]:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
            updates.update(protect_email(email))
            updates["email_verified"] = False
            updates["email_verified_at"] = None

    if "preferences" in data and isinstance(data["preferences"], dict):
        preferences = dict(user.get("preferences") or {})
        for key in {"theme", "default_project", "email_alerts", "locale", "compact_mode"}:
            if key in data["preferences"]:
                preferences[key] = data["preferences"][key]
        updates["preferences"] = preferences
        data.pop("preferences", None)

    for field in ["name", "job_title", "department", "company", "phone", "timezone", "bio"]:
        if field in data:
            updates[field] = data[field]

    if not updates:
        return {"user": public_user(user), "updated": False}

    updates["updated_at"] = utcnow()
    await store.update_one("users", {"_id": user["_id"]}, {"$set": updates})
    user.update(updates)
    if "email_hash" in updates:
        email_delivery = await _send_verification_email(store, user)
    return {"user": public_user(user), "updated": True, "email_delivery": email_delivery}


@router.post("/me/avatar")
async def upload_avatar(
    payload: AvatarUploadPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    encoded = payload.data_base64.split(",", 1)[1] if "," in payload.data_base64 else payload.data_base64
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image payload") from None
    if len(raw) > settings.max_avatar_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Avatar file is too large")

    extension = AVATAR_EXTENSIONS[payload.content_type]
    avatar_dir = Path(settings.upload_dir) / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    avatar_path = avatar_dir / f"{user['_id']}.{extension}"
    avatar_path.write_bytes(raw)

    version = int(datetime.now(timezone.utc).timestamp())
    updates = {
        "avatar_path": str(avatar_path),
        "avatar_url": f"{settings.api_prefix}/auth/me/avatar?v={version}",
        "avatar_content_type": payload.content_type,
        "avatar_file_name": payload.file_name,
        "avatar_updated_at": utcnow(),
        "updated_at": utcnow(),
    }
    await store.update_one("users", {"_id": user["_id"]}, {"$set": updates})
    user.update(updates)
    return {"user": public_user(user)}


@router.get("/me/avatar")
async def get_avatar(user: dict = Depends(get_current_user)) -> FileResponse:
    path_value = user.get("avatar_path")
    if not path_value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")
    path = Path(path_value)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Avatar not found")
    return FileResponse(path, media_type=user.get("avatar_content_type") or "image/png", filename=path.name)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)) -> dict:
    return {"user": public_user(user)}
