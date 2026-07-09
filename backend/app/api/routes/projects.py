from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_store, require_same_org
from app.core.privacy import audit_actor_for_user, reveal_dashboard_for_user
from app.core.utils import make_id, slugify, utcnow
from app.db.document_store import DocumentStore
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.audit import create_audit_event
from app.services.metrics import build_project_dashboard

router = APIRouter(tags=["projects"])


@router.get("/projects")
async def list_projects(user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    projects = await store.find_many("projects", {"org_id": user["org_id"]}, sort=[("created_at", -1)], limit=200)
    return {"items": projects}


@router.post("/projects", status_code=201)
async def create_project(
    payload: ProjectCreate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    project = {
        "_id": make_id("proj"),
        "org_id": user["org_id"],
        "name": payload.name,
        "slug": slugify(payload.name),
        "description": payload.description,
        "i18n": payload.i18n,
        "problem_type": payload.problem_type,
        "domain": payload.domain,
        "owner_id": user["_id"],
        "collaborators": [],
        "tags": payload.tags,
        "settings": {
            "default_threshold": payload.default_threshold,
            "positive_label": "positive",
            "negative_label": "negative",
            "retention_days": 730,
            "enable_drift_monitoring": True,
            "drift_check_frequency": "weekly",
            "alert_email": user.get("email_masked") or user.get("email"),
            "alert_email_hash": user.get("email_hash"),
            "bias_sensitive_features": payload.bias_sensitive_features,
        },
        "stats": {"total_predictions": 0, "total_models": 0, "active_alerts": 0, "last_prediction_at": None},
        "created_at": utcnow(),
        "status": "active",
    }
    await store.insert_one("projects", project)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=project["_id"],
        actor=audit_actor_for_user(user),
        event_type="project.created",
        resource_type="project",
        resource_id=project["_id"],
        diff={"after": project},
    )
    return project


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    project = require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    return project


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    before = require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    updates = {key: value for key, value in payload.model_dump(exclude_none=True).items()}
    data_contract_mode = updates.pop("data_contract_mode", None)
    if data_contract_mode:
        updates["settings.data_contract_mode"] = data_contract_mode
    if "name" in updates:
        updates["slug"] = slugify(updates["name"])
    if not updates:
        return before
    await store.update_one("projects", {"_id": project_id}, {"$set": updates})
    after = await store.find_one("projects", {"_id": project_id})
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=project_id,
        actor=audit_actor_for_user(user),
        event_type="project.updated",
        resource_type="project",
        resource_id=project_id,
        diff={"before": before, "after": after},
    )
    return after or before


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    await store.update_one("projects", {"_id": project_id}, {"$set": {"status": "archived"}})
    return {"status": "archived", "project_id": project_id}


@router.get("/projects/{project_id}/dashboard")
async def project_dashboard(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    return reveal_dashboard_for_user(await build_project_dashboard(store, project_id))


@router.get("/projects/{project_id}/audit-events")
async def project_audit_events(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    events = await store.find_many("audit_events", {"project_id": project_id}, sort=[("created_at", -1)], limit=200)
    return {"items": events}
