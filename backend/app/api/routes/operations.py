from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user, get_store, require_same_org
from app.core.privacy import audit_actor_for_user
from app.core.utils import utcnow
from app.db.document_store import DocumentStore
from app.services.audit import create_audit_event

router = APIRouter(tags=["operations"])


class CaseStatusPayload(BaseModel):
    status: str
    note: str = ""


@router.get("/projects/{project_id}/operations")
async def project_operations(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    project = require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    cases = await store.find_many(
        "intervention_cases",
        {"project_id": project_id},
        sort=[("priority_rank", 1), ("risk_score", -1)],
        limit=120,
    )
    incidents = await store.find_many("incidents", {"project_id": project_id}, sort=[("created_at", -1)], limit=30)
    cohorts = await store.find_many("cohorts", {"project_id": project_id}, sort=[("created_at", -1)], limit=40)
    evaluations = await store.find_many("model_evaluations", {"project_id": project_id}, sort=[("rank", 1)], limit=100)
    cards = await store.find_many("model_cards", {"project_id": project_id}, sort=[("created_at", -1)], limit=50)
    quality = await store.find_many("data_quality_reports", {"project_id": project_id}, sort=[("created_at", -1)], limit=1)
    datasets = await store.find_many("datasets", {"project_id": project_id}, sort=[("created_at", -1)], limit=10)
    approvals = await store.find_many("approvals", {"project_id": project_id}, sort=[("created_at", -1)], limit=50)
    alerts = await store.find_many("alerts", {"project_id": project_id, "status": {"$ne": "resolved"}}, sort=[("created_at", -1)], limit=50)

    open_cases = [item for item in cases if item.get("status") in {"open", "assigned", "in_progress"}]
    critical_cases = [item for item in open_cases if item.get("priority") == "critical"]
    pending_feedback = [item for item in cases if item.get("outcome_status") == "pending"]
    expected_entities = sum(1 for item in pending_feedback if item.get("recommended_action") != "monitor")

    return {
        "project": project,
        "generated_at": utcnow(),
        "summary": {
            "open_cases": len(open_cases),
            "critical_cases": len(critical_cases),
            "pending_feedback": len(pending_feedback),
            "expected_interventions": expected_entities,
            "active_incidents": sum(1 for item in incidents if item.get("status") != "resolved"),
            "active_alerts": len(alerts),
            "models_evaluated": len(evaluations),
        },
        "datasets": datasets,
        "data_quality": quality[0] if quality else None,
        "cohorts": cohorts,
        "intervention_cases": cases,
        "incidents": incidents,
        "alerts": alerts,
        "model_evaluations": evaluations,
        "model_cards": cards,
        "approvals": approvals,
    }


@router.get("/projects/{project_id}/intervention-cases")
async def list_intervention_cases(
    project_id: str,
    status_filter: str | None = None,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    filter_: dict = {"project_id": project_id}
    if status_filter:
        filter_["status"] = status_filter
    cases = await store.find_many(
        "intervention_cases",
        filter_,
        sort=[("priority_rank", 1), ("risk_score", -1)],
        limit=300,
    )
    return {"items": cases}


@router.post("/intervention-cases/{case_id}/status")
async def update_intervention_case_status(
    case_id: str,
    payload: CaseStatusPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    case = require_same_org(await store.find_one("intervention_cases", {"_id": case_id}), user)
    allowed = {"open", "assigned", "in_progress", "paused", "resolved", "dismissed"}
    if payload.status not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid case status")

    event = {
        "status": payload.status,
        "note": payload.note,
        "actor": audit_actor_for_user(user),
        "created_at": utcnow(),
    }
    timeline = list(case.get("timeline", []))
    timeline.append(event)
    await store.update_one(
        "intervention_cases",
        {"_id": case_id},
        {"$set": {"status": payload.status, "timeline": timeline, "updated_at": utcnow()}},
    )
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=case["project_id"],
        actor=audit_actor_for_user(user),
        event_type="intervention_case.status_changed",
        resource_type="intervention_case",
        resource_id=case_id,
        diff={"after": event},
    )
    return await store.find_one("intervention_cases", {"_id": case_id}) or case


@router.get("/models/{model_id}/evaluations")
async def list_model_evaluations(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    model = require_same_org(await store.find_one("models", {"_id": model_id}), user)
    evaluations = await store.find_many(
        "model_evaluations",
        {"model_id": model_id, "project_id": model["project_id"]},
        sort=[("window", 1), ("rank", 1)],
        limit=100,
    )
    return {"items": evaluations}
