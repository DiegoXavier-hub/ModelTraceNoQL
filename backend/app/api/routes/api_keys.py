from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_store, require_same_org
from app.core.privacy import audit_actor_for_user
from app.core.security import generate_api_key
from app.core.utils import make_id, utcnow
from app.db.document_store import DocumentStore
from app.schemas import APIKeyCreate
from app.services.audit import create_audit_event

router = APIRouter(tags=["api-keys"])


@router.get("/projects/{project_id}/api-keys")
async def list_api_keys(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    keys = await store.find_many("api_keys", {"project_id": project_id}, sort=[("created_at", -1)], limit=100)
    return {"items": [{key: value for key, value in item.items() if key != "key_hash"} for item in keys]}


@router.post("/projects/{project_id}/api-keys", status_code=201)
async def create_api_key(
    project_id: str,
    payload: APIKeyCreate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    raw_key, prefix, key_hash = generate_api_key()
    doc = {
        "_id": make_id("key"),
        "project_id": project_id,
        "org_id": user["org_id"],
        "name": payload.name,
        "prefix": prefix,
        "key_hash": key_hash,
        "hash_algorithm": "hmac_sha256",
        "scopes": payload.scopes,
        "expires_at": payload.expires_at,
        "created_by": user["_id"],
        "created_at": utcnow(),
        "last_used_at": None,
        "status": "active",
    }
    await store.insert_one("api_keys", doc)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=project_id,
        actor=audit_actor_for_user(user),
        event_type="api_key.created",
        resource_type="api_key",
        resource_id=doc["_id"],
        diff={"after": {key: value for key, value in doc.items() if key != "key_hash"}},
    )
    return {"api_key": raw_key, "record": {key: value for key, value in doc.items() if key != "key_hash"}}


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    api_key = require_same_org(await store.find_one("api_keys", {"_id": api_key_id}), user)
    await store.update_one("api_keys", {"_id": api_key_id}, {"$set": {"status": "revoked"}})
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=api_key["project_id"],
        actor=audit_actor_for_user(user),
        event_type="api_key.revoked",
        resource_type="api_key",
        resource_id=api_key_id,
    )
    return {"status": "revoked", "api_key_id": api_key_id}
