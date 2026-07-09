from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_optional_user_or_api_key, get_store, require_api_scope
from app.core.privacy import audit_actor_for_user, blind_index, reveal_prediction_for_user, reveal_predictions_for_user
from app.core.utils import make_id, utcnow
from app.db.document_store import DocumentStore
from app.schemas import AnnotationPayload, BatchPredictionPayload, FeedbackPayload, PredictionPayload, ReplayPayload, WhatIfPayload
from app.services.audit import create_audit_event
from app.services.predictions import add_feedback, record_prediction
from app.services.whatif import estimate_what_if

router = APIRouter(tags=["predictions"])


@router.post("/predictions", status_code=201)
async def create_prediction(
    payload: PredictionPayload,
    actor_context: dict = Depends(get_optional_user_or_api_key),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_api_scope(actor_context, "predictions:write")
    prediction = await record_prediction(store, payload, actor_context)
    return {"prediction_id": prediction["_id"], "status": "recorded", "prediction": reveal_prediction_for_user(prediction)}


@router.post("/predictions/batch", status_code=201)
async def create_predictions_batch(
    payload: BatchPredictionPayload,
    actor_context: dict = Depends(get_optional_user_or_api_key),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_api_scope(actor_context, "predictions:batch")
    results = []
    for item in payload.items:
        try:
            prediction = await record_prediction(store, item, actor_context)
            results.append({"status": "recorded", "prediction_id": prediction["_id"]})
        except Exception as exc:  # batch returns item-level failures
            detail = getattr(exc, "detail", str(exc))
            status_code = getattr(exc, "status_code", 500)
            results.append({"status": "failed", "status_code": status_code, "detail": detail})
    return {"items": results}


@router.get("/predictions")
async def list_predictions(
    project_id: str | None = None,
    model_id: str | None = None,
    model_version: str | None = None,
    label: str | None = None,
    score_band: str | None = None,
    entity_id: str | None = None,
    q: str | None = None,
    feedback_available: bool | None = None,
    limit: int = Query(default=50, ge=1, le=5000),
    skip: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_: dict = {"org_id": user["org_id"]}
    if project_id:
        filter_["project_id"] = project_id
    if model_id:
        filter_["model_id"] = model_id
    if model_version:
        filter_["model_version"] = model_version
    if label:
        filter_["prediction.label"] = label
    if score_band:
        filter_["prediction.score_band"] = score_band
    if entity_id:
        filter_["entity.id_hash"] = blind_index(entity_id, "entity")
    if feedback_available is not None:
        filter_["feedback.available"] = feedback_available
    if q and q.strip():
        normalized = q.strip().lower()
        all_items = await store.find_many("predictions", filter_, sort=[("created_at", -1)], limit=0)
        visible_items = reveal_predictions_for_user(all_items)
        matched = [
            item
            for item in visible_items
            if normalized
            in " ".join(
                str(value)
                for value in [
                    item.get("_id"),
                    item.get("entity", {}).get("id"),
                    item.get("entity", {}).get("id_hash"),
                    item.get("entity", {}).get("display_name"),
                    item.get("model_version"),
                    item.get("prediction", {}).get("label"),
                    item.get("feedback", {}).get("classification_result"),
                ]
                if value is not None
            ).lower()
        ]
        total = len(matched)
        items = matched[skip : skip + limit]
    else:
        items = await store.find_many("predictions", filter_, sort=[("created_at", -1)], limit=limit, skip=skip)
        total = await store.count("predictions", filter_)
    return {"items": reveal_predictions_for_user(items), "total": total, "limit": limit, "skip": skip}


@router.get("/predictions/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    item = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not item:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return reveal_prediction_for_user(item)


@router.post("/predictions/{prediction_id}/feedback")
async def create_feedback(
    prediction_id: str,
    payload: FeedbackPayload,
    actor_context: dict = Depends(get_optional_user_or_api_key),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_api_scope(actor_context, "feedback:write")
    return reveal_prediction_for_user(await add_feedback(store, prediction_id, payload, actor_context))


@router.post("/predictions/{prediction_id}/annotations", status_code=201)
async def create_annotation(
    prediction_id: str,
    payload: AnnotationPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not prediction:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    annotation = {
        "_id": make_id("ann"),
        "prediction_id": prediction_id,
        "project_id": prediction["project_id"],
        "org_id": user["org_id"],
        "user_id": user["_id"],
        "type": payload.type,
        "content": payload.content,
        "tags": payload.tags,
        "created_at": utcnow(),
    }
    await store.insert_one("prediction_annotations", annotation)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=prediction["project_id"],
        actor=audit_actor_for_user(user),
        event_type="prediction.annotation_added",
        resource_type="prediction",
        resource_id=prediction_id,
        diff={"after": annotation},
    )
    return annotation


@router.get("/predictions/{prediction_id}/annotations")
async def list_annotations(
    prediction_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not prediction:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    annotations = await store.find_many(
        "prediction_annotations", {"prediction_id": prediction_id}, sort=[("created_at", -1)], limit=100
    )
    return {"items": annotations}


@router.get("/predictions/{prediction_id}/audit-trail")
async def prediction_audit_trail(
    prediction_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not prediction:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    events = await store.find_many(
        "audit_events",
        {"resource.type": "prediction", "resource.id": prediction_id},
        sort=[("created_at", -1)],
        limit=100,
    )
    return {"items": events}


@router.post("/predictions/{prediction_id}/whatif")
async def prediction_what_if(
    prediction_id: str,
    payload: WhatIfPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not prediction:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return estimate_what_if(prediction, payload.hypothetical_features)


@router.post("/predictions/{prediction_id}/replay", status_code=201)
async def prediction_replay(
    prediction_id: str,
    payload: ReplayPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not prediction:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    model = await store.find_one("models", {"_id": prediction["model_id"], "org_id": user["org_id"]})
    threshold = float(prediction.get("prediction", {}).get("threshold", (model or {}).get("default_threshold", 0.5)))
    estimated = None
    if payload.replay_score is None:
        estimated = estimate_what_if(prediction, payload.hypothetical_features or prediction.get("features", {}))
        replay_score = estimated["estimated_score"]
    else:
        replay_score = payload.replay_score
    replay_label = payload.replay_label or (
        (model or {}).get("labels", {}).get("positive", "high_risk")
        if replay_score >= threshold
        else (model or {}).get("labels", {}).get("negative", "negative")
    )
    replay = {
        "_id": make_id("replay"),
        "prediction_id": prediction_id,
        "project_id": prediction["project_id"],
        "org_id": user["org_id"],
        "model_id": prediction["model_id"],
        "original": {
            "model_version": prediction.get("model_version"),
            "score": prediction.get("prediction", {}).get("score"),
            "label": prediction.get("prediction", {}).get("label"),
            "above_threshold": prediction.get("prediction", {}).get("above_threshold"),
        },
        "replay": {
            "target_version": payload.target_version,
            "score": replay_score,
            "label": replay_label,
            "above_threshold": replay_score >= threshold,
        },
        "hypothetical_features": payload.hypothetical_features,
        "estimation": estimated,
        "decision_changed": prediction.get("prediction", {}).get("label") != replay_label,
        "created_by": user["_id"],
        "created_at": utcnow(),
    }
    await store.insert_one("prediction_replays", replay)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=prediction["project_id"],
        actor=audit_actor_for_user(user),
        event_type="prediction.replay_created",
        resource_type="prediction",
        resource_id=prediction_id,
        diff={"after": replay},
    )
    return replay


@router.get("/predictions/{prediction_id}/replays")
async def list_prediction_replays(
    prediction_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id, "org_id": user["org_id"]})
    if not prediction:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    replays = await store.find_many("prediction_replays", {"prediction_id": prediction_id}, sort=[("created_at", -1)], limit=100)
    return {"items": replays}
