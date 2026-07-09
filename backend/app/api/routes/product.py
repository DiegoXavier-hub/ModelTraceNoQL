from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_store, require_same_org
from app.api.routes.alerts import _create_rule_alert, _default_project_rules, _evaluate_rule, _violates
from app.core.privacy import audit_actor_for_user, blind_index, reveal_predictions_for_user
from app.core.utils import get_nested, make_id, utcnow
from app.db.document_store import DocumentStore
from app.schemas import DataContractPayload, EntityNotePayload, JobRunPayload, NotificationUpdate, SavedViewPayload
from app.services.audit import create_audit_event
from app.services.diagnostics import build_model_diagnostics
from app.services.metrics import build_project_dashboard, generate_drift_report, recompute_model_metrics
from app.services.notifications import create_notification

router = APIRouter(tags=["product"])


async def _run_job(store: DocumentStore, job_id: str) -> None:
    job = await store.find_one("jobs", {"_id": job_id})
    if not job:
        return
    await store.update_one("jobs", {"_id": job_id}, {"$set": {"status": "running", "started_at": utcnow()}})
    result: dict[str, Any] = {}
    try:
        job_type = job["type"]
        if job_type == "alerts":
            project_id = job.get("project_id")
            rules = await store.find_many("alert_rules", {"project_id": project_id, "enabled": True}, limit=200)
            if job.get("params", {}).get("include_defaults", True):
                existing_ids = {rule["_id"] for rule in rules}
                rules.extend([rule for rule in await _default_project_rules(store, project_id, job["org_id"]) if rule["_id"] not in existing_ids])
            created = []
            evaluated = []
            for rule in rules:
                value, detail = await _evaluate_rule(store, rule)
                violated = _violates(value, rule["operator"], float(rule["threshold"]))
                evaluated.append({"rule_id": rule["_id"], "value": value, "violated": violated, "detail": detail})
                if violated:
                    alert = await _create_rule_alert(store, rule, value, detail)
                    if alert:
                        created.append(alert)
            result = {"evaluated": len(evaluated), "created": len(created)}
        elif job_type == "drift":
            result = await generate_drift_report(store, job["model_id"])
        elif job_type == "metrics":
            result = {"snapshots": len(await recompute_model_metrics(store, job["model_id"]))}
        elif job_type == "diagnostics":
            result = await build_model_diagnostics(store, job["model_id"], job.get("params", {}).get("slice_feature"))
        elif job_type == "dashboard":
            result = await build_project_dashboard(store, job["project_id"])
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        await store.update_one(
            "jobs",
            {"_id": job_id},
            {"$set": {"status": "completed", "finished_at": utcnow(), "result": result}},
        )
        await create_notification(
            store,
            org_id=job["org_id"],
            user_id=job.get("created_by"),
            project_id=job.get("project_id"),
            type_="job.completed",
            title="Job concluido",
            message=f"{job_type} finalizado com sucesso.",
            severity="success",
            link={"view": "governance", "resource_id": job_id},
            metadata={"job_id": job_id, "type": job_type},
        )
    except Exception as exc:
        await store.update_one(
            "jobs",
            {"_id": job_id},
            {"$set": {"status": "failed", "finished_at": utcnow(), "error": str(exc)}},
        )
        await create_notification(
            store,
            org_id=job["org_id"],
            user_id=job.get("created_by"),
            project_id=job.get("project_id"),
            type_="job.failed",
            title="Job com erro",
            message=f"{job.get('type')} falhou: {exc}",
            severity="error",
            link={"view": "governance", "resource_id": job_id},
            metadata={"job_id": job_id, "type": job.get("type")},
        )


@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_: dict[str, Any] = {"org_id": user["org_id"]}
    if unread_only:
        filter_["read_at"] = None
    notifications = await store.find_many("notifications", filter_, sort=[("created_at", -1)], limit=100)
    return {"items": notifications, "unread": await store.count("notifications", {"org_id": user["org_id"], "read_at": None})}


@router.patch("/notifications/{notification_id}")
async def update_notification(
    notification_id: str,
    payload: NotificationUpdate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    notification = require_same_org(await store.find_one("notifications", {"_id": notification_id}), user)
    await store.update_one(
        "notifications",
        {"_id": notification_id},
        {"$set": {"read_at": utcnow() if payload.read else None}},
    )
    return await store.find_one("notifications", {"_id": notification_id}) or notification


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    changed = await store.transform_many(
        "notifications",
        {"org_id": user["org_id"], "read_at": None},
        lambda _: {"$set": {"read_at": utcnow()}},
    )
    return {"updated": changed}


@router.get("/jobs")
async def list_jobs(
    project_id: str | None = None,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_: dict[str, Any] = {"org_id": user["org_id"]}
    if project_id:
        filter_["project_id"] = project_id
    jobs = await store.find_many("jobs", filter_, sort=[("created_at", -1)], limit=100)
    return {"items": jobs}


@router.post("/jobs", status_code=202)
async def run_job(
    payload: JobRunPayload,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    if payload.project_id:
        require_same_org(await store.find_one("projects", {"_id": payload.project_id}), user)
    if payload.model_id:
        require_same_org(await store.find_one("models", {"_id": payload.model_id}), user)
    if payload.type in {"alerts", "dashboard"} and not payload.project_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="project_id is required")
    if payload.type in {"drift", "metrics", "diagnostics"} and not payload.model_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="model_id is required")

    job = {
        "_id": make_id("job"),
        "org_id": user["org_id"],
        "project_id": payload.project_id,
        "model_id": payload.model_id,
        "type": payload.type,
        "params": payload.params,
        "status": "queued",
        "created_by": user["_id"],
        "created_at": utcnow(),
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": None,
    }
    await store.insert_one("jobs", job)
    background_tasks.add_task(_run_job, store, job["_id"])
    return job


@router.get("/saved-views")
async def list_saved_views(
    view: str | None = None,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_: dict[str, Any] = {"org_id": user["org_id"]}
    if view:
        filter_["view"] = view
    items = await store.find_many("saved_views", filter_, sort=[("created_at", -1)], limit=100)
    return {"items": items}


@router.post("/saved-views", status_code=201)
async def create_saved_view(
    payload: SavedViewPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    item = {
        "_id": make_id("view"),
        "org_id": user["org_id"],
        "user_id": user["_id"],
        **payload.model_dump(),
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await store.insert_one("saved_views", item)
    return item


@router.delete("/saved-views/{view_id}")
async def delete_saved_view(view_id: str, user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    item = require_same_org(await store.find_one("saved_views", {"_id": view_id}), user)
    if item.get("user_id") != user["_id"] and not item.get("shared"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Saved view is not available")
    await store.delete_one("saved_views", {"_id": view_id})
    return {"status": "deleted", "view_id": view_id}


@router.get("/projects/{project_id}/entity-timeline")
async def entity_timeline(
    project_id: str,
    q: str = Query(min_length=1, max_length=240),
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    entity_hash = blind_index(q, "entity")
    predictions = await store.find_many(
        "predictions",
        {"project_id": project_id, "entity.id_hash": entity_hash},
        sort=[("created_at", -1)],
        limit=200,
    )
    if not predictions:
        all_items = await store.find_many("predictions", {"project_id": project_id}, sort=[("created_at", -1)], limit=0)
        visible = reveal_predictions_for_user(all_items)
        predictions = [
            item
            for item in visible
            if q.lower() in f"{get_nested(item, 'entity.id', '')} {get_nested(item, 'entity.display_name', '')}".lower()
        ][:200]
    else:
        predictions = reveal_predictions_for_user(predictions)
    prediction_ids = [item["_id"] for item in predictions]
    notes = await store.find_many("entity_notes", {"project_id": project_id, "entity_hash": entity_hash}, sort=[("created_at", -1)], limit=100)
    cases = await store.find_many("intervention_cases", {"project_id": project_id, "prediction_id": {"$in": prediction_ids}}, sort=[("created_at", -1)], limit=100) if prediction_ids else []
    replays = await store.find_many("prediction_replays", {"prediction_id": {"$in": prediction_ids}}, sort=[("created_at", -1)], limit=100) if prediction_ids else []
    events = []
    for item in predictions:
        events.append({"type": "prediction", "created_at": item.get("created_at"), "title": item.get("prediction", {}).get("label"), "item": item})
    for item in cases:
        events.append({"type": "case", "created_at": item.get("created_at"), "title": item.get("recommended_action"), "item": item})
    for item in replays:
        events.append({"type": "replay", "created_at": item.get("created_at"), "title": item.get("replay", {}).get("target_version"), "item": item})
    for item in notes:
        events.append({"type": "note", "created_at": item.get("created_at"), "title": "Nota", "item": item})
    events.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {"query": q, "entity_hash": entity_hash, "predictions": predictions, "cases": cases, "replays": replays, "notes": notes, "events": events}


@router.post("/projects/{project_id}/entity-notes", status_code=201)
async def create_entity_note(
    project_id: str,
    payload: EntityNotePayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    note = {
        "_id": make_id("note"),
        "org_id": user["org_id"],
        "project_id": project_id,
        "entity_hash": blind_index(payload.entity_id, "entity"),
        "entity_id": payload.entity_id,
        "content": payload.content,
        "tags": payload.tags,
        "created_by": user["_id"],
        "created_at": utcnow(),
    }
    await store.insert_one("entity_notes", note)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=project_id,
        actor=audit_actor_for_user(user),
        event_type="entity.note_created",
        resource_type="entity",
        resource_id=note["entity_hash"],
        diff={"after": {key: value for key, value in note.items() if key != "entity_id"}},
    )
    return note


@router.get("/projects/{project_id}/data-contract")
async def get_project_contract(project_id: str, user: dict = Depends(get_current_user), store: DocumentStore = Depends(get_store)) -> dict:
    project = require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    models = await store.find_many("models", {"project_id": project_id}, limit=200)
    return {
        "project_id": project_id,
        "mode": get_nested(project, "settings.data_contract_mode", "warn"),
        "models": [{"model_id": model["_id"], "name": model["name"], "expected_features": model.get("expected_features", [])} for model in models],
    }


@router.patch("/projects/{project_id}/data-contract")
async def update_project_contract(
    project_id: str,
    payload: DataContractPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    await store.update_one("projects", {"_id": project_id}, {"$set": {"settings.data_contract_mode": payload.mode}})
    if payload.expected_features is not None:
        models = await store.find_many("models", {"project_id": project_id}, limit=200)
        for model in models:
            await store.update_one("models", {"_id": model["_id"]}, {"$set": {"expected_features": payload.expected_features}})
    return await get_project_contract(project_id, user, store)
