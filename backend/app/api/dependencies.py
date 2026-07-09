from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.security import hash_api_key, legacy_hash_api_key, verify_token
from app.core.utils import utcnow
from app.db.document_store import DocumentStore


async def get_store(request: Request) -> DocumentStore:
    return request.app.state.store


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def _parse_utc(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    store: DocumentStore = Depends(get_store),
) -> dict[str, Any]:
    token = _bearer_token(authorization) or request.cookies.get("modeltrace_access")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = await store.find_one("users", {"_id": payload["sub"], "status": "active"})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_optional_user_or_api_key(
    request: Request,
    authorization: str | None = Header(default=None),
    store: DocumentStore = Depends(get_store),
) -> dict[str, Any]:
    raw = _bearer_token(authorization) or request.cookies.get("modeltrace_access")
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if raw.startswith("mt_live_"):
        api_key = await store.find_one("api_keys", {"key_hash": hash_api_key(raw), "status": "active"})
        if not api_key:
            api_key = await store.find_one("api_keys", {"key_hash": legacy_hash_api_key(raw), "status": "active"})
            if api_key:
                await store.update_one(
                    "api_keys",
                    {"_id": api_key["_id"]},
                    {"$set": {"key_hash": hash_api_key(raw), "hash_algorithm": "hmac_sha256"}},
                )
                api_key["key_hash"] = hash_api_key(raw)
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        expires_at = api_key.get("expires_at")
        expires_at_dt = _parse_utc(expires_at) if expires_at else None
        if expires_at_dt and expires_at_dt <= datetime.now(timezone.utc):
            await store.update_one("api_keys", {"_id": api_key["_id"]}, {"$set": {"status": "expired"}})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired API key")
        await store.update_one("api_keys", {"_id": api_key["_id"]}, {"$set": {"last_used_at": utcnow()}})
        api_key["last_used_at"] = utcnow()
        return {"type": "api_key", "api_key": api_key, "org_id": api_key["org_id"], "project_id": api_key["project_id"]}
    payload = verify_token(raw, "access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = await store.find_one("users", {"_id": payload["sub"], "status": "active"})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {"type": "user", "user": user, "org_id": user["org_id"]}


def require_same_org(resource: dict[str, Any] | None, user: dict[str, Any]) -> dict[str, Any]:
    if not resource or resource.get("org_id") != user.get("org_id"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


def require_api_scope(actor_context: dict[str, Any], scope: str) -> None:
    if actor_context.get("type") != "api_key":
        return
    api_key = actor_context.get("api_key") or {}
    scopes = api_key.get("scopes") or ["predictions:write", "predictions:batch", "feedback:write"]
    if "admin" in scopes or scope in scopes:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"API key missing scope: {scope}")
